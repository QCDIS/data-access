"""
Description
===========

This module contains the functionality to access data from the MUNDI DIAS.
"""
from bs4 import BeautifulSoup
from datetime import datetime
from lxml.etree import XML
import glob
import logging
import os
import requests
import shutil
import time
from http.cookiejar import CookieJar
from shapely.geometry import Polygon
from shapely.wkt import dumps
from sys import stdout
from typing import List, Sequence
import urllib.request as urllib2

from multiply_core.observations import DataTypeConstants
from multiply_core.util import FileRef, get_mime_type, get_time_from_string
from multiply_data_access.data_access import DataSetMetaInfo, FileSystemAccessor, MetaInfoProvider, \
    MetaInfoProviderAccessor
from multiply_data_access.locally_wrapped_data_access import LocallyWrappedFileSystem, LocallyWrappedMetaInfoProvider

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

_LOCALLY_WRAPPED_META_INFO_PROVIDER_NAME = 'MundiMetaInfoProvider'
_MUNDI_META_INFO_PROVIDER_NAME = 'MundiDiasMetaInfoProvider'
_OBS_FILE_SYSTEM_NAME = 'MundiFileSystem'
_REST_FILE_SYSTEM_NAME = 'MundiRestFileSystem'

_BASE_URL = 'https://mundiwebservices.com/acdc/catalog/proxy/search/'
_COLLECTIONS_DESCRIPTIONS_ADDITION = 'collections/opensearch/description.xml'
_COLLECTION_DESCRIPTION_ADDITION = '{}/opensearch/description.xml'
_BASE_CATALOGUE_URL = "https://mundiwebservices.com/acdc/catalog/proxy/search/{}/opensearch?q=({})"
_REST_BASE_URL = "https://obs.eu-de.otc.t-systems.com/{}/?prefix={}{}"
_REST_BASE_KEY_URL = "https://obs.eu-de.otc.t-systems.com/{}/{}"
_POLYGON_FORMAT = 'POLYGON(({1} {0}, {3} {2}, {5} {4}, {7} {6}, {9} {8}))'
_DATA_TYPE_PARAMETER_DICTS = {
    DataTypeConstants.S1_SLC:
        {'platform': 'Sentinel1', 'processingLevel': 'L1_', 'productType': 'SLC',
         'baseBuckets': ['s1-l1-slc', 's1-l1-slc-{YYYY}', 's1-l1-slc-{YYYY}-q{q}'],
         'storageStructure': 'YYYY/MM/DD/MM/pp/', 'excludes': [],
         'placeholders': {'MM': {'start': 4, 'end': 6}, 'pp': {'start': 14, 'end': 16}}},
    DataTypeConstants.S2_L1C:
        {'platform': 'Sentinel2', 'processingLevel': 'L1C', 'instrument': 'MSI', 'productType': 'IMAGE',
         'baseBuckets': ['s2-l1c-{YYYY}-q{q}', 's2-l1c-{YYYY}', 's2-l1c'], 'storageStructure': 'UU/L/SS/YYYY/MM/DD/',
         'excludes': ['.zip'],
         'placeholders': {'UU': {'start': 39, 'end': 41}, 'L': {'start': 41, 'end': 42},
                          'SS': {'start': 42, 'end': 44}}},
    DataTypeConstants.S3_L1_OLCI_RR:
        {'platform': 'Sentinel3', 'processingLevel': 'L1_', 'instrument': 'OLCI', 'productType': 'OL_1_ERR___',
         'baseBuckets': ['s3-olci'], 'storageStructure': 'LRR/YYYY/MM/DD/', 'excludes': [], 'placeholders': {}},
    DataTypeConstants.S3_L1_OLCI_FR:
        {'platform': 'Sentinel3', 'processingLevel': 'L1_', 'instrument': 'OLCI', 'productType': 'OL_1_EFR___',
         'baseBuckets': ['s3-olci'], 'storageStructure': 'LFR/YYYY/MM/DD/', 'excludes': [], 'placeholders': {}}
}
_MUNDI_SERVER = 'obs.otc.t-systems.com'


def _create_mundi_query(roi: str, data_type: str, start_time: str, end_time: str, run: int) -> str:
    data_type_dict = _DATA_TYPE_PARAMETER_DICTS[data_type]
    start_index = (10 * run) + 1
    instrument_part = ''
    if 'instrument' in data_type_dict:
        instrument_part = f"instrument={data_type_dict['instrument']}"
    query_part = f"(sensingStartDate:[{start_time} TO {end_time}] AND footprint:\"Intersects({roi})\")&" \
                 f"startIndex={start_index}&maxRecords=10&processingLevel={data_type_dict['processingLevel']}&" \
                 f"{instrument_part}&productType={data_type_dict['productType']}"
    return _BASE_CATALOGUE_URL.format(data_type_dict['platform'], query_part)


def _convert_mundi_coverage(mundi_coverage_string: str):
    coords = mundi_coverage_string.split(" ")
    coord_list = []
    for i in range(0, len(coords), 2):
        coord_list.append((float(coords[i + 1]), float(coords[i])))
    coverage = Polygon(coord_list)
    return dumps(coverage)


def _get_provided_data_types() -> List[str]:
    collections_description_url = '{}{}'.format(_BASE_URL, _COLLECTIONS_DESCRIPTIONS_ADDITION)
    descriptions = urllib2.urlopen(collections_description_url).read()
    descriptions_root = XML(descriptions)
    platforms = []
    # todo make this more sophisticated
    for child in descriptions_root:
        if child.tag == '{http://a9.com/-/spec/opensearch/1.1/}Url':
            if child.get('rel') == 'search':
                for child2 in child:
                    if child2.tag == '{http://a9.com/-/spec/opensearch/extensions/parameters/1.0/}Parameter':
                        for child3 in child2:
                            platforms.append(child3.get('value'))
    provided_data_types = []
    for data_type in _DATA_TYPE_PARAMETER_DICTS:
        data_type_dict = _DATA_TYPE_PARAMETER_DICTS[data_type]
        instruments = []
        processing_levels = []
        product_types = []
        if data_type_dict['platform'] in platforms:
            platform_url = '{}{}'.format(_BASE_URL, _COLLECTION_DESCRIPTION_ADDITION.format(data_type_dict['platform']))
            description = urllib2.urlopen(platform_url).read()
            platform_description_root = XML(description)
            for child in platform_description_root:
                if child.tag == '{http://a9.com/-/spec/opensearch/1.1/}Url':
                    for child2 in child:
                        if child2.tag == '{http://a9.com/-/spec/opensearch/extensions/parameters/1.0/}Parameter':
                            if child2.get('name') == 'instrument':
                                for child3 in child2:
                                    instruments.append(child3.get('value'))
                            elif child2.get('name') == 'processingLevel':
                                for child3 in child2:
                                    processing_levels.append(child3.get('value'))
                            elif child2.get('name') == 'productType':
                                for child3 in child2:
                                    product_types.append(child3.get('value'))
        if (('instrument' in data_type_dict and data_type_dict['instrument'] in instruments)
            or 'instrument' not in data_type_dict) and \
                data_type_dict['processingLevel'] in processing_levels and \
                data_type_dict['productType'] in product_types:
            provided_data_types.append(data_type)
    return provided_data_types


class LocallyWrappedMundiMetaInfoProvider(LocallyWrappedMetaInfoProvider):

    def _init_wrapped_meta_info_provider(self, parameters: dict) -> None:
        pass

    def _query_wrapped_meta_info_provider(self, query_string: str, local_data_set_meta_infos: List[DataSetMetaInfo]) -> \
            List[DataSetMetaInfo]:
        roi = dumps(self.get_roi_from_query_string(query_string))
        data_types = self.get_data_types_from_query_string(query_string)
        start_time = datetime.strftime(self.get_start_time_from_query_string(query_string), "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strftime(self.get_end_time_from_query_string(query_string), "%Y-%m-%dT%H:%M:%SZ")
        data_set_meta_infos = []
        for data_type in data_types:
            if self.provides_data_type(data_type):
                run = 0
                continue_checking_for_data_sets = True
                while continue_checking_for_data_sets:
                    mundi_query = _create_mundi_query(roi, data_type, start_time, end_time, run)
                    run += 1
                    response = requests.get(mundi_query)
                    response_xml = XML(response.content)
                    continue_checking_for_data_sets = False
                    for child in response_xml:
                        if child.tag == '{http://www.w3.org/2005/Atom}entry':
                            data_set_meta_info_id = ""
                            data_set_meta_info_time = ""
                            data_set_meta_info_coverage = ""
                            for child2 in child:
                                if child2.tag == '{http://www.w3.org/2005/Atom}id':
                                    data_set_meta_info_id = child2.text
                                elif child2.tag == '{http://www.georss.org/georss}polygon':
                                    data_set_meta_info_coverage = _convert_mundi_coverage(child2.text)
                                elif child2.tag == '{http://tas/DIAS}sensingStartDate':
                                    data_set_meta_info_time = child2.text
                            data_set_meta_info = DataSetMetaInfo(data_set_meta_info_coverage, data_set_meta_info_time,
                                                                 data_set_meta_info_time, data_type,
                                                                 data_set_meta_info_id)
                            if not self._is_provided_locally(data_set_meta_info, local_data_set_meta_infos):
                                data_set_meta_infos.append(data_set_meta_info)
                            continue_checking_for_data_sets = True
        return data_set_meta_infos

    def _get_wrapped_parameters_as_dict(self) -> dict:
        return {}

    @classmethod
    def name(cls) -> str:
        return _LOCALLY_WRAPPED_META_INFO_PROVIDER_NAME

    def provides_data_type(self, data_type: str) -> bool:
        if not hasattr(self, '_provided_data_types'):
            self._provided_data_types = _get_provided_data_types()
        return data_type in self._provided_data_types

    def get_provided_data_types(self) -> List[str]:
        if not hasattr(self, '_provided_data_types'):
            self._provided_data_types = _get_provided_data_types()
        return self._provided_data_types

    def encapsulates_data_type(self, data_type: str) -> bool:
        return False


class LocallyWrappedMundiMetaInfoProviderAccessor(MetaInfoProviderAccessor):

    @classmethod
    def name(cls) -> str:
        return _LOCALLY_WRAPPED_META_INFO_PROVIDER_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> LocallyWrappedMundiMetaInfoProvider:
        return LocallyWrappedMundiMetaInfoProvider(parameters)


class MundiMetaInfoProvider(MetaInfoProvider):

    def __init__(self, parameters: dict):
        self._provided_data_types = _get_provided_data_types()

    @classmethod
    def name(cls) -> str:
        return _MUNDI_META_INFO_PROVIDER_NAME

    def query(self, query_string: str) -> List[DataSetMetaInfo]:
        return self.query_non_local(query_string)

    def query_local(self, query_string: str) -> List[DataSetMetaInfo]:
        # this meta info provider holds no information on locally available data
        return []

    def query_non_local(self, query_string: str) -> List[DataSetMetaInfo]:
        roi = dumps(self.get_roi_from_query_string(query_string))
        data_types = self.get_data_types_from_query_string(query_string)
        start_time = datetime.strftime(self.get_start_time_from_query_string(query_string), "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strftime(self.get_end_time_from_query_string(query_string), "%Y-%m-%dT%H:%M:%SZ")
        data_set_meta_infos = []
        for data_type in data_types:
            if self.provides_data_type(data_type):
                run = 0
                continue_checking_for_data_sets = True
                while continue_checking_for_data_sets:
                    mundi_query = _create_mundi_query(roi, data_type, start_time, end_time, run)
                    run += 1
                    response = requests.get(mundi_query)
                    response_xml = XML(response.content)
                    continue_checking_for_data_sets = False
                    for child in response_xml:
                        if child.tag == '{http://www.w3.org/2005/Atom}entry':
                            data_set_meta_info_id = ""
                            data_set_meta_info_time = ""
                            data_set_meta_info_coverage = ""
                            for child2 in child:
                                if child2.tag == '{http://www.w3.org/2005/Atom}id':
                                    data_set_meta_info_id = child2.text
                                elif child2.tag == '{http://www.georss.org/georss}polygon':
                                    data_set_meta_info_coverage = _convert_mundi_coverage(child2.text)
                                elif child2.tag == '{http://tas/DIAS}sensingStartDate':
                                    data_set_meta_info_time = child2.text
                            data_set_meta_infos.append(DataSetMetaInfo(data_set_meta_info_coverage,
                                                                       data_set_meta_info_time, data_set_meta_info_time,
                                                                       data_type, data_set_meta_info_id))
                            continue_checking_for_data_sets = True
        return data_set_meta_infos

    def provides_data_type(self, data_type: str) -> bool:
        return data_type in self._provided_data_types

    def get_provided_data_types(self) -> List[str]:
        return self._provided_data_types

    def encapsulates_data_type(self, data_type: str) -> bool:
        return False

    def _get_parameters_as_dict(self) -> dict:
        return {}

    def can_update(self) -> bool:
        return False

    def update(self, data_set_meta_info: DataSetMetaInfo):
        pass

    def remove(self, data_set_meta_info: DataSetMetaInfo):
        pass

    def get_all_data(self) -> Sequence[DataSetMetaInfo]:
        return []


class MundiMetaInfoProviderAccessor(MetaInfoProviderAccessor):

    @classmethod
    def name(cls) -> str:
        return _MUNDI_META_INFO_PROVIDER_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> MundiMetaInfoProvider:
        return MundiMetaInfoProvider(parameters)


class MundiObsFileSystem(LocallyWrappedFileSystem):

    def _init_wrapped_file_system(self, parameters: dict) -> None:
        if 'access_key_id' not in parameters.keys():
            self._access_key_id = ''
            logging.warning('No access key id set. Will not be able to download data from MUNDI DIAS')
        else:
            self._access_key_id = parameters['access_key_id']
        if 'secret_access_key' not in parameters.keys():
            logging.warning('No secret access key set. Will not be able to download data from MUNDI DIAS')
            self._secret_access_key = ''
        else:
            self._secret_access_key = parameters['secret_access_key']
        if 'temp_dir' not in parameters.keys():
            raise ValueError('No valid temporal directory provided for AWS S2 File System')
        if not os.path.exists(parameters['temp_dir']):
            os.makedirs(parameters['temp_dir'])
        self._temp_dir = parameters['temp_dir']
        self._path = parameters['path']

    @classmethod
    def name(cls) -> str:
        return _OBS_FILE_SYSTEM_NAME

    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        from com.obs.client.obs_client import ObsClient
        if data_set_meta_info.data_type not in _DATA_TYPE_PARAMETER_DICTS:
            logging.warning(f'Data Type {data_set_meta_info.data_type} not supported by MUNDI DIAS File System '
                            f'implementation.')
            return []
        buckets = self._get_bucket_names(data_set_meta_info)
        prefix = self._get_prefix(data_set_meta_info)
        obs_client = ObsClient(access_key_id=self._access_key_id,
                               secret_access_key=self._secret_access_key,
                               server=_MUNDI_SERVER)
        keys = []
        excludes = _DATA_TYPE_PARAMETER_DICTS[data_set_meta_info.data_type]['excludes']
        right_bucket = None
        for bucket in buckets:
            right_bucket = bucket
            objects = obs_client.listObjects(bucketName=bucket, prefix=prefix)
            if objects.status < 300:
                for content in objects.body.contents:
                    if data_set_meta_info.identifier in content.key:
                        move_on = False
                        for exclude in excludes:
                            if content.key.endswith(exclude):
                                move_on = True
                        if not move_on:
                            keys.append(content.key)
                if len(keys) > 0:
                    break
        if len(keys) == 0:
            return []
        data_set_id = data_set_meta_info.identifier
        for key in keys:
            relative_path_to_file = key.split(data_set_meta_info.identifier)[1]
            target_file = f'{self._temp_dir}/{data_set_meta_info.identifier}{relative_path_to_file}'
            if len(keys) == 1:
                data_set_id = f'{data_set_meta_info.identifier}{relative_path_to_file}'
            resp = obs_client.getObject(right_bucket, key, downloadPath= target_file)
            if resp.status >= 300:
                return []
        obs_client.close()
        file_ref = FileRef(f'{self._temp_dir}/{data_set_id}',
                           data_set_meta_info.start_time, data_set_meta_info.end_time,
                           get_mime_type(data_set_meta_info.identifier))
        return [file_ref]

    @staticmethod
    def _get_bucket_names(data_set_meta_info: DataSetMetaInfo) -> List[str]:
        start_time = get_time_from_string(data_set_meta_info.start_time)
        base_bucket_names = _DATA_TYPE_PARAMETER_DICTS[data_set_meta_info.data_type]['baseBuckets']
        bucket_names = []
        for base_bucket_name in base_bucket_names:
            quarter = int(int(start_time.month - 1) / 3) + 1
            bucket_name = base_bucket_name.replace('{YYYY}', str(start_time.year))
            bucket_name = bucket_name.replace('{q}', str(quarter))
            bucket_names.append(bucket_name)
        return bucket_names

    @staticmethod
    def _get_prefix(data_set_meta_info: DataSetMetaInfo):
        data_type_dict = _DATA_TYPE_PARAMETER_DICTS[data_set_meta_info.data_type]
        storage_structure = data_type_dict['storageStructure']
        data_time = get_time_from_string(data_set_meta_info.start_time)
        prefix = storage_structure.replace('{}'.format('YYYY'), '{:04d}'.format(data_time.year))
        prefix = prefix.replace('{}'.format('MM'), '{:02d}'.format(data_time.month))
        prefix = prefix.replace('{}'.format('DD'), '{:02d}'.format(data_time.day))
        for placeholder in data_type_dict['placeholders'].keys():
            start = data_type_dict['placeholders'][placeholder]['start']
            end = data_type_dict['placeholders'][placeholder]['end']
            prefix = prefix.replace(placeholder, data_set_meta_info.identifier[start:end])
        return prefix

    def _get_wrapped_parameters_as_dict(self) -> dict:
        return {'access_key_id': self._access_key_id, 'secret_access_key': self._secret_access_key,
                'temp_dir': self._temp_dir}

    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo) -> None:
        files = glob.glob(f'{self._temp_dir}/{data_set_meta_info.identifier}*')
        for file in files:
            if os.path.exists(file):
                if os.path.isdir(file):
                    shutil.rmtree(file)
                else:
                    os.remove(file)

    def clear_cache(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)


class MundiObsFileSystemAccessor(FileSystemAccessor):

    @classmethod
    def name(cls) -> str:
        return _OBS_FILE_SYSTEM_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> MundiObsFileSystem:
        return MundiObsFileSystem(parameters)


class MundiRestFileSystem(LocallyWrappedFileSystem):

    def _init_wrapped_file_system(self, parameters: dict) -> None:
        if 'temp_dir' not in parameters.keys():
            raise ValueError('No valid temporal directory provided for AWS S2 File System')
        if not os.path.exists(parameters['temp_dir']):
            os.makedirs(parameters['temp_dir'])
        self._temp_dir = parameters['temp_dir']

    @classmethod
    def name(cls) -> str:
        return _REST_FILE_SYSTEM_NAME

    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        if data_set_meta_info.data_type not in _DATA_TYPE_PARAMETER_DICTS:
            logging.warning(f'Data Type {data_set_meta_info.data_type} not supported by MUNDI DIAS File System '
                            f'implementation.')
            return []
        buckets = self._get_bucket_names(data_set_meta_info)
        prefix = self._get_prefix(data_set_meta_info)
        file_refs = []
        for bucket in buckets:
            file_url = _REST_BASE_URL.format(bucket, prefix, data_set_meta_info.identifier)
            excludes = _DATA_TYPE_PARAMETER_DICTS[data_set_meta_info.data_type]['excludes']
            success = self._download_url(file_url, data_set_meta_info.identifier, bucket, excludes)
            if success:
                url = glob.glob(f"{self._temp_dir}/{data_set_meta_info.identifier}*")[0]
                file_refs.append(FileRef(url, data_set_meta_info.start_time, data_set_meta_info.end_time,
                                         get_mime_type(url)))
                logging.info('Downloaded {}'.format(data_set_meta_info.identifier))
                break
        return file_refs

    def _download_url(self, url: str, file_name: str, bucket: str, excludes: List[str]) -> bool:
        try:
            request = requests.get(url, stream=True)
        except ConnectionError:
            logging.warning('Could not retrieve data from Mundi due to a connection error.')
            return False
        if request.status_code > 300:
            request.close()
            return False
        content_type = urllib2.urlopen(url).info().get_content_type()
        if content_type == 'application/xml':
            soup = BeautifulSoup(request.content, 'xml')
            contents = soup.find_all('Contents')
            total_size_in_bytes = 0
            file_sizes = []
            keys = []
            for content in contents:
                key = content.find('Key').text
                move_on = False
                for exclude in excludes:
                    if key.endswith(exclude):
                        move_on = True
                if move_on:
                    continue
                file_size = int(content.find('Size').text)
                total_size_in_bytes += file_size
                file_sizes.append(file_size)
                keys.append(key)
            if len(keys) == 0:
                request.close()
                return False
            cj = CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            logging.info('Downloading {}'.format(file_name))
            one_percent = total_size_in_bytes / 100
            downloaded_bytes = 0
            next_threshold = one_percent
            for index, key in enumerate(keys):
                relative_path_to_file = key.split(file_name)[1]
                destination = f'{self._temp_dir}/{file_name}{relative_path_to_file}'
                destination_dir = os.path.abspath(os.path.join(destination, os.pardir))
                if not os.path.exists(destination_dir):
                    os.makedirs(destination_dir)
                key_url = _REST_BASE_KEY_URL.format(bucket, key)
                mode = 'wb'
                hundred_mb = 250 * 1024 * 1024
                file_downloaded_bytes = 0
                start = 0
                while start < file_sizes[index]:
                    try:
                        end = min(file_sizes[index], start + hundred_mb) - 1
                        key_request = urllib2.Request(key_url)
                        if start != 0 or end != file_sizes[index] - 1:
                            key_request.add_header('Range', f'bytes={start}-{end}')
                            time.sleep(3) # sleep to avoid double connections
                        remote_file = opener.open(key_request)
                        if remote_file.status >= 300:
                            logging.warning(f'Could not download {key}.')
                            return False
                        with open(destination, mode) as fp:
                            length = 1024 * 1024
                            buf = remote_file.read(length)
                            while buf:
                                fp.write(buf)
                                downloaded_bytes += min(len(buf), 1024 * 1024)
                                file_downloaded_bytes += min(len(buf), 1024 * 1024)
                                fp.flush()
                                remote_file.flush()
                                if downloaded_bytes > next_threshold:
                                    stdout.write('\r{} %'.format(int(next_threshold / one_percent)))
                                    stdout.flush()
                                    next_threshold += one_percent
                                buf = remote_file.read(length)
                        fp.close()
                        remote_file.close()
                        start += hundred_mb
                        mode = 'ab'
                    except ConnectionResetError:
                        start = downloaded_bytes
                if file_downloaded_bytes != file_sizes[index]:
                    logging.warning(f'File download incomplete. Should be {file_sizes[index]}, '
                                    f'is {file_downloaded_bytes}')
        request.close()
        return True

    @staticmethod
    def _get_bucket_names(data_set_meta_info: DataSetMetaInfo) -> List[str]:
        start_time = get_time_from_string(data_set_meta_info.start_time)
        base_bucket_names = _DATA_TYPE_PARAMETER_DICTS[data_set_meta_info.data_type]['baseBuckets']
        bucket_names = []
        for base_bucket_name in base_bucket_names:
            quarter = int(int(start_time.month - 1) / 3) + 1
            bucket_name = base_bucket_name.replace('{YYYY}', str(start_time.year))
            bucket_name = bucket_name.replace('{q}', str(quarter))
            bucket_names.append(bucket_name)
        return bucket_names

    @staticmethod
    def _get_prefix(data_set_meta_info: DataSetMetaInfo):
        data_type_dict = _DATA_TYPE_PARAMETER_DICTS[data_set_meta_info.data_type]
        storage_structure = data_type_dict['storageStructure']
        data_time = get_time_from_string(data_set_meta_info.start_time)
        prefix = storage_structure.replace('{}'.format('YYYY'), '{:04d}'.format(data_time.year))
        prefix = prefix.replace('{}'.format('MM'), '{:02d}'.format(data_time.month))
        prefix = prefix.replace('{}'.format('DD'), '{:02d}'.format(data_time.day))
        for placeholder in data_type_dict['placeholders'].keys():
            start = data_type_dict['placeholders'][placeholder]['start']
            end = data_type_dict['placeholders'][placeholder]['end']
            prefix = prefix.replace(placeholder, data_set_meta_info.identifier[start:end])
        return prefix

    def _get_wrapped_parameters_as_dict(self) -> dict:
        return {'temp_dir': self._temp_dir}

    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo) -> None:
        files = glob.glob(f'{self._temp_dir}/{data_set_meta_info.identifier}*')
        for file in files:
            if os.path.exists(file):
                if os.path.isdir(file):
                    shutil.rmtree(file)
                else:
                    os.remove(file)

    def clear_cache(self):
        shutil.rmtree(self._temp_dir)


class MundiRestFileSystemAccessor(FileSystemAccessor):

    @classmethod
    def name(cls) -> str:
        return _REST_FILE_SYSTEM_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> MundiRestFileSystem:
        return MundiRestFileSystem(parameters)
