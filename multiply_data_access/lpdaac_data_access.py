import base64
import datetime
import logging
import os
import osr
import re
import shutil
from sys import stdout
import urllib.request as urllib2
from urllib.error import URLError

from http.cookiejar import CookieJar
from multiply_core.util import FileRef, get_mime_type, get_time_from_string
from multiply_core.observations import DataTypeConstants
from multiply_data_access.data_access import DataSetMetaInfo, FileSystemAccessor, MetaInfoProviderAccessor
from multiply_data_access.locally_wrapped_data_access import LocallyWrappedFileSystem, LocallyWrappedMetaInfoProvider
from multiply_data_access.modis_tile_coverage_provider import get_tile_coverage
from typing import List, Sequence

__author__ = 'Tonio Fincke (Brockmann Consult GmbH),' \
             'José Luis Gómez-Dans (University College London)'

_SUPPORTED_DATA_TYPES = [DataTypeConstants.MODIS_MCD_43, DataTypeConstants.MODIS_MCD_15_A2]
_DATA_OFFSETS = {DataTypeConstants.MODIS_MCD_43: 0, DataTypeConstants.MODIS_MCD_15_A2: 1}
_DATA_INTERVALS = {DataTypeConstants.MODIS_MCD_43: 1, DataTypeConstants.MODIS_MCD_15_A2: 8}
_BASE_URL = 'http://e4ftl01.cr.usgs.gov/'
_PLATFORM = 'MOTA'
_FILE_SYSTEM_NAME = 'LpDaacFileSystem'
_META_INFO_PROVIDER_NAME = 'LpDaacMetaInfoProvider'
_X_STEP = -463.31271653 * 2400
_Y_STEP = 463.31271653 * 2400
_M_Y0 = -20015109.354
_M_X0 = 10007554.677
FIRST_DAY = '2000-02-24'


class LpDaacMetaInfoProvider(LocallyWrappedMetaInfoProvider):
    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    def _init_wrapped_meta_info_provider(self, parameters: dict) -> None:
        wgs84_srs = osr.SpatialReference()  # Define a SpatialReference object
        wgs84_srs.ImportFromEPSG(4326)  # And set it to WGS84 using the EPSG code
        modis_sinu_srs = osr.SpatialReference()  # define the SpatialReference object
        modis_sinu_srs.ImportFromProj4(
            "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")
        self._wgs84_to_modis = osr.CoordinateTransformation(wgs84_srs, modis_sinu_srs)
        self._modis_to_wgs84 = osr.CoordinateTransformation(modis_sinu_srs, wgs84_srs)
        if 'supported_data_types' not in parameters:
            # use this as default for backwards compatibility
            self._supported_data_types = [DataTypeConstants.MODIS_MCD_43]
        else:
            parameter_data_types  = parameters['supported_data_types'].replace(' ', '').split(',')
            self._supported_data_types = []
            for parameter_data_type in parameter_data_types:
                if parameter_data_type not in _SUPPORTED_DATA_TYPES:
                    logging.info('NASA Land Processes Distributed Active Archive Center does not support data type {}.'
                                 .format(parameter_data_type))
                    continue
                self._supported_data_types.append(parameter_data_type)

    def _query_wrapped_meta_info_provider(self, query_string: str, local_data_set_meta_infos: List[DataSetMetaInfo]) \
            -> List[DataSetMetaInfo]:
        requested_data_types = []
        query_data_types = self.get_data_types_from_query_string(query_string)
        for supported_data_type in self._supported_data_types:
            if supported_data_type in query_data_types:
                requested_data_types.append(supported_data_type)
        if len(requested_data_types) == 0:
            return []
        roi = self.get_roi_from_query_string(query_string)
        tile_coverages = []
        for v in range(18):
            for h in range(36):
                tile_coverage = get_tile_coverage(h, v)
                if tile_coverage is not None and tile_coverage.intersects(roi):
                    tile_coverages.append((h, v, tile_coverage.wkt))
        start_time = self.get_start_time_from_query_string(query_string)
        if start_time is None:
            start_time = get_time_from_string(FIRST_DAY)
        end_time = self.get_end_time_from_query_string(query_string)
        if end_time is None:
            end_time = datetime.datetime.now()
        data_set_meta_infos = []
        try:
            for requested_data_type in requested_data_types:
                start_doy = start_time.timetuple().tm_yday
                current_time = start_time - datetime.timedelta(days=(start_doy - _DATA_OFFSETS[requested_data_type])
                                                                    % _DATA_INTERVALS[requested_data_type])
                while current_time < end_time:
                    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
                    current_tile_coverages = []
                    for h, v, tile_coverage in tile_coverages:
                        add_to_current = True
                        for local_data_set_meta_info in local_data_set_meta_infos:
                            if local_data_set_meta_info.coverage == tile_coverage and \
                                    local_data_set_meta_info.start_time == current_time_str:
                                add_to_current = False
                                break
                        if add_to_current:
                            current_tile_coverages.append((h, v, tile_coverage))
                    next_time = current_time + datetime.timedelta(days=_DATA_INTERVALS[requested_data_type])
                    next_time -= datetime.timedelta(seconds=1)
                    if len(current_tile_coverages) > 0:
                        date_dir_url = '{}/{}/{}/{}.{:02d}.{:02d}/'.format(_BASE_URL, _PLATFORM, requested_data_type,
                                                                           current_time.year, current_time.month,
                                                                           current_time.day)
                        date_page = urllib2.urlopen(date_dir_url).read().decode('utf-8')
                        for h, v, tile_coverage in current_tile_coverages:
                            file_regex = '.hdf">{}.A{}{:03d}.h{:02d}v{:02d}.006.*.hdf'. \
                                format(requested_data_type.split('.')[0], current_time.year,
                                       current_time.timetuple().tm_yday, h, v)
                            available_files = re.findall(file_regex, date_page)
                            for file in available_files:
                                current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
                                logging.info('Found {} data set for {}'.format(requested_data_type, current_time_str))
                                data_set_meta_infos.append(DataSetMetaInfo(tile_coverage, current_time_str,
                                                                           next_time.strftime('%Y-%m-%d %H:%M:%S'),
                                                                           requested_data_type, file[6:]))
                    current_time = next_time + datetime.timedelta(seconds=1)
        except URLError as e:
            logging.warning('Could not access NASA Land Processes Distributed Active Archive Center: {}'.format(e.reason))
        return data_set_meta_infos

    def _get_id_ranges(self, min_x: float, min_y: float, max_x: float, max_y: float) -> ([], []):
        h0, v0 = self._get_h_v_tile_ids(min_x, min_y)
        h1, v1 = self._get_h_v_tile_ids(min_x, max_y)
        h2, v2 = self._get_h_v_tile_ids(max_x, min_y)
        h3, v3 = self._get_h_v_tile_ids(max_x, max_y)
        min_h_id = min([h0, h1, h2, h3])
        max_h_id = max([h0, h1, h2, h3]) + 1
        h_id_range = list(range(min_h_id, max_h_id))
        min_v_id = min([v0, v1, v2, v3])
        max_v_id = max([v0, v1, v2, v3]) + 1
        v_id_range = list(range(min_v_id, max_v_id))
        return h_id_range, v_id_range

    def _get_h_v_tile_ids(self, min_x: float, min_y: float) -> (int, int):
        h, v, z = self._wgs84_to_modis.TransformPoint(min_x, min_y)
        h_id = int((h - _M_Y0) / _Y_STEP)
        v_id = int((v - _M_X0) / _X_STEP)
        return h_id, v_id

    def _get_wrapped_parameters_as_dict(self) -> dict:
        return {}

    def provides_data_type(self, data_type: str) -> bool:
        return data_type in self._supported_data_types

    def get_provided_data_types(self) -> List[str]:
        if hasattr(self, '_supported_data_types'):
            return self._supported_data_types
        else:
            return [DataTypeConstants.MODIS_MCD_43]

    def encapsulates_data_type(self, data_type: str) -> bool:
        return False


class LpDaacMetaInfoProviderAccessor(MetaInfoProviderAccessor):
    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> LpDaacMetaInfoProvider:
        return LpDaacMetaInfoProvider(parameters)


class LpDaacFileSystem(LocallyWrappedFileSystem):

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    def _init_wrapped_file_system(self, parameters: dict) -> None:
        if 'temp_dir' not in parameters.keys():
            raise ValueError('No valid temporal directory provided for Lp Daac File System')
        if not os.path.exists(parameters['temp_dir']):
            os.makedirs(parameters['temp_dir'])
        self._temp_dir = parameters['temp_dir']
        if 'username' not in parameters.keys():
            raise ValueError('No username provided for Lp Daac File System')
        self._username = parameters['username']
        if 'password' not in parameters.keys():
            raise ValueError('No password provided for Lp Daac File System')
        self._password = parameters['password']
        cj = CookieJar()
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        file_refs = []
        time = get_time_from_string(data_set_meta_info.start_time)
        file_url = '{}/{}/{}/{}.{:02d}.{:02d}/{}'.format(_BASE_URL, _PLATFORM, data_set_meta_info.data_type,
                                                         time.year, time.month, time.day, data_set_meta_info.identifier)
        request = urllib2.Request(file_url)
        authorization = base64.encodebytes(str.encode('{}:{}'.format(self._username, self._password))). \
            replace(b'\n', b'').decode()
        request.add_header('Authorization', 'Basic {}'.format(authorization))
        remote_file = self._opener.open(request)
        temp_url = '{}/{}'.format(self._temp_dir, data_set_meta_info.identifier)
        logging.info('Downloading {}'.format(data_set_meta_info.identifier))
        with open(temp_url, 'wb') as temp_file:
            total_size_in_bytes = int(remote_file.info()['Content-Length'])
            one_percent = total_size_in_bytes / 100
            downloaded_bytes = 0
            next_threshold = one_percent
            length = 1024
            buf = remote_file.read(length)
            while buf:
                temp_file.write(buf)
                buf = remote_file.read(length)
                downloaded_bytes += 1024
                if downloaded_bytes > next_threshold:
                    stdout.write('\r{} %'.format(int(next_threshold / one_percent)))
                    stdout.flush()
                    next_threshold += one_percent
        logging.info('Downloaded {}'.format(data_set_meta_info.identifier))
        file_refs.append(FileRef(temp_url, data_set_meta_info.start_time, data_set_meta_info.end_time,
                                 get_mime_type(temp_url)))
        return file_refs

    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo):
        full_path = '{}/{}'.format(self._temp_dir, data_set_meta_info.identifier)
        if os.path.exists(full_path):
            os.remove(full_path)

    def _get_wrapped_parameters_as_dict(self) -> dict:
        parameters = {'temp_dir': self._temp_dir, 'username': self._username, 'password': self._password}
        return parameters

    def clear_cache(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)


class LpDaacFileSystemAccessor(FileSystemAccessor):
    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> LpDaacFileSystem:
        return LpDaacFileSystem(parameters)