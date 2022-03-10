"""
Description
===========

This module contains the functionality to access data from the MUNDI DIAS.
"""
from datetime import datetime
from http.cookiejar import CookieJar
from lxml.etree import XML
from zipfile import ZipFile
import base64
import glob
import logging
import os
import requests
import shutil
import time
from shapely.geometry import Polygon
from shapely.wkt import dumps
from sys import stdout
from typing import List, Sequence
import urllib.request as urllib2
from urllib.error import HTTPError

from multiply_core.observations import DataTypeConstants
from multiply_core.util import FileRef, get_mime_type, get_time_from_string
from multiply_data_access.data_access import DataSetMetaInfo, FileSystemAccessor, MetaInfoProviderAccessor
from multiply_data_access.locally_wrapped_data_access import LocallyWrappedFileSystem, LocallyWrappedMetaInfoProvider

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

_META_INFO_PROVIDER_NAME = 'SciHubMetaInfoProvider'
_FILE_SYSTEM_NAME = 'SciHubFileSystem'

_BASE_CATALOGUE_URL = "https://scihub.copernicus.eu/dhus/search?start={}&rows=50&q=({})"
_DATA_TYPE_PARAMETER_DICTS = {
    DataTypeConstants.S1_SLC: {'platformname': 'Sentinel-1', 'productType': 'SLC', 'unzip': False},
    DataTypeConstants.S2_L1C: {'platformname': 'Sentinel-2', 'productType': 'S2MSI1C', 'unzip': True}
}
_DOWNLOAD_URL = "https://scihub.copernicus.eu/dhus/odata/v1/Products(\'{}\')/$value"


class SciHubMetaInfoProvider(LocallyWrappedMetaInfoProvider):

    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    def _init_wrapped_meta_info_provider(self, parameters: dict) -> None:
        if 'username' not in parameters.keys():
            raise ValueError('No username provided for Copernicus Sci Hub')
        self._username = parameters['username']
        if 'password' not in parameters.keys():
            raise ValueError('No password provided for Copernicus Sci Hub')
        self._password = parameters['password']

    def _query_wrapped_meta_info_provider(self, query_string: str,
                                          local_data_set_meta_infos: List[DataSetMetaInfo]) -> List[DataSetMetaInfo]:
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
                    scihub_query = self._create_scihub_query(roi, data_type, start_time, end_time, run)
                    run += 1
                    response = requests.get(scihub_query, auth=(self._username, self._password))
                    response_xml = XML(response.content)
                    continue_checking_for_data_sets = False
                    for child in response_xml:
                        if child.tag == '{http://www.w3.org/2005/Atom}entry':
                            data_set_meta_info_id = ""
                            data_set_meta_info_start_time = ""
                            data_set_meta_info_end_time = ""
                            data_set_meta_info_coverage = ""
                            data_set_meta_info_reference = ""
                            for child2 in child:
                                if child2.tag == '{http://www.w3.org/2005/Atom}id':
                                    data_set_meta_info_reference = child2.text
                                elif child2.tag == '{http://www.w3.org/2005/Atom}title':
                                    data_set_meta_info_id = child2.text
                                elif child2.tag == '{http://www.w3.org/2005/Atom}date' and 'name' in child2.attrib \
                                        and child2.attrib['name'] == 'beginposition':
                                    data_set_meta_info_start_time = child2.text
                                elif child2.tag == '{http://www.w3.org/2005/Atom}date' and 'name' in child2.attrib \
                                        and child2.attrib['name'] == 'endposition':
                                    data_set_meta_info_end_time = child2.text
                                elif child2.tag == '{http://www.w3.org/2005/Atom}str' and 'name' in child2.attrib \
                                        and child2.attrib['name'] == 'footprint':
                                    data_set_meta_info_coverage = child2.text
                            data_set_meta_info = \
                                DataSetMetaInfo(data_set_meta_info_coverage, data_set_meta_info_start_time,
                                                data_set_meta_info_end_time, data_type, data_set_meta_info_id,
                                                data_set_meta_info_reference)
                            if not self._is_provided_locally(data_set_meta_info, local_data_set_meta_infos):
                                data_set_meta_infos.append(data_set_meta_info)
                            continue_checking_for_data_sets = True
                    response.close()
        return data_set_meta_infos

    @staticmethod
    def _convert_mundi_coverage(mundi_coverage_string: str):
        coords = mundi_coverage_string.split(" ")
        coord_list = []
        for i in range(0, len(coords), 2):
            coord_list.append((float(coords[i + 1]), float(coords[i])))
        coverage = Polygon(coord_list)
        return dumps(coverage)

    @staticmethod
    def _create_scihub_query(roi: str, data_type: str, start_time: str, end_time: str, run: int) -> str:
        data_type_dict = _DATA_TYPE_PARAMETER_DICTS[data_type]
        query_part = "(beginPosition:[{} TO {}] AND endPosition:[{} TO {}]) " \
                     "AND (footprint:\"Intersects({})\") " \
                     "AND (platformname:{} AND producttype:{})"
        query_part = query_part.format(start_time, end_time, start_time, end_time, roi,
                                       data_type_dict['platformname'], data_type_dict['productType'])
        return _BASE_CATALOGUE_URL.format((50 * run), query_part)

    def _get_wrapped_parameters_as_dict(self) -> dict:
        return {'username': self._username, 'password': self._password}

    def provides_data_type(self, data_type: str) -> bool:
        return data_type == DataTypeConstants.S1_SLC or data_type == DataTypeConstants.S2_L1C

    def get_provided_data_types(self) -> List[str]:
        return [DataTypeConstants.S1_SLC]

    def encapsulates_data_type(self, data_type: str) -> bool:
        return False


class SciHubMetaInfoProviderAccessor(MetaInfoProviderAccessor):

    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> SciHubMetaInfoProvider:
        return SciHubMetaInfoProvider(parameters)


class SciHubFileSystem(LocallyWrappedFileSystem):

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    def _init_wrapped_file_system(self, parameters: dict) -> None:
        if 'username' not in parameters.keys():
            raise ValueError('No username provided for Copernicus Sci Hub')
        self._username = parameters['username']
        if 'password' not in parameters.keys():
            raise ValueError('No password provided for Copernicus Sci Hub')
        self._password = parameters['password']
        if 'temp_dir' not in parameters.keys():
            raise ValueError('No valid temporal directory provided for Copernicus Sci Hub File System')
        self._temp_dir = parameters['temp_dir']
        if not os.path.exists(parameters['temp_dir']):
            os.makedirs(parameters['temp_dir'])

    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        file_refs = []
        file_url = _DOWNLOAD_URL.format(data_set_meta_info.referenced_data)
        request = urllib2.Request(file_url)
        authorization = base64.encodebytes(str.encode('{}:{}'.format(self._username, self._password))). \
            replace(b'\n', b'').decode()
        request.add_header('Authorization', 'Basic {}'.format(authorization))
        try:
            cj = CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            remote_file = opener.open(request)
            status = remote_file.status
            while status != 200:
                logging.info(f"Request '{file_url}' awaiting status")
                time.sleep(10)
                remote_file = opener.open(request)
                status = remote_file.status
            total_size_in_bytes = int(remote_file.info()['Content-Length'])
            # todo check in advance whether there is enough disk space left
            file_name = data_set_meta_info.identifier
            cdheader = remote_file.getheader('content-disposition')
            if cdheader:
                split_header = cdheader.split('"')
                if file_name in cdheader and len(split_header) > 1:
                    file_name = split_header[-2]
            temp_url = f'{self._temp_dir}/{file_name}'
            logging.info('Downloading {}'.format(data_set_meta_info.identifier))
            with open(temp_url, 'wb') as temp_file:
                one_percent = total_size_in_bytes / 100
                downloaded_bytes = 0
                next_threshold = one_percent
                length = 1024 * 1024
                buf = remote_file.read(length)
                while buf:
                    temp_file.write(buf)
                    downloaded_bytes += 1024 * 1024
                    if downloaded_bytes > next_threshold:
                        stdout.write('\r{} %'.format(int(next_threshold / one_percent)))
                        stdout.flush()
                        next_threshold += one_percent
                    buf = remote_file.read(length)
            temp_file.close()
            remote_file.close()
            logging.info('Downloaded {}'.format(data_set_meta_info.identifier))
            if _DATA_TYPE_PARAMETER_DICTS[data_set_meta_info.data_type]['unzip'] and file_name.endswith('.zip'):
                with ZipFile(temp_url) as zipfile:
                    zipfile.extractall(self._temp_dir)
                os.remove(temp_url)
            temp_content = glob.glob(f'{self._temp_dir}/*')
            if len(temp_content) > 0:
                id = temp_content[0]
                file_refs.append(FileRef(id, data_set_meta_info.start_time, data_set_meta_info.end_time,
                                         get_mime_type(temp_url)))
            opener.close()
        except HTTPError as e:
            logging.info(f"Could not download from url '{file_url}'. {e.reason}")
        return file_refs

    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo) -> None:
        full_paths = glob.glob(f'{self._temp_dir}/{data_set_meta_info.identifier}*')
        for full_path in full_paths:
            if os.path.exists(full_path):
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)

    def _get_wrapped_parameters_as_dict(self) -> dict:
        return {'username': self._username, 'password': self._password, 'temp_dir': self._temp_dir}

    def clear_cache(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)


class SciHubFileSystemAccessor(FileSystemAccessor):

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> SciHubFileSystem:
        return SciHubFileSystem(parameters)
