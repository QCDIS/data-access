"""
Description
===========

This module contains an implementation of a file system that allows to access and download S2 L1C data from Amazon Web
Services (AWS).
"""
from distutils.dir_util import copy_tree
from multiply_core.util import FileRef, get_mime_type, get_time_from_string
from .data_access import DataSetMetaInfo, FileSystemAccessor
from multiply_data_access.locally_wrapped_data_access import LocallyWrappedFileSystem
from typing import Optional, Sequence
import itertools
import logging
import os
import re
import shutil

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"

BASIC_AWS_S2_PATTERN = '[0-9]{1,2}/[A-Z]/[A-Z]{2}/20[0-9][0-9]/[0-9]{1,2}/[0-9]{1,2}/[0-9]{1,2}'
BASIC_AWS_S2_MATCHER = re.compile(BASIC_AWS_S2_PATTERN)
_QI_LIST = ['DEFECT', 'DETFOO', 'NODATA', 'SATURA', 'TECQUA']
_S2_L1C_BANDS = ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B10', 'B11', 'B12']

_NAME = 'AwsS2FileSystem'


class AwsS2FileSystem(LocallyWrappedFileSystem):

    def __init__(self, parameters: dict):
        super().__init__(parameters)

    def _init_wrapped_file_system(self, parameters: dict):
        if 'temp_dir' not in parameters.keys():
            raise ValueError('No valid temporal directory provided for AWS S2 File System')
        if not os.path.exists(parameters['temp_dir']):
            os.makedirs(parameters['temp_dir'])
        self._temp_dir = parameters['temp_dir']

    @classmethod
    def name(cls) -> str:
        return _NAME

    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        file_refs = []
        metafiles = ['qi/MSK_{}_{}'.format(qi, band) for qi, band in itertools.product(_QI_LIST, _S2_L1C_BANDS)]
        metafiles.append('metadata')
        metafiles.append('tileInfo')
        retrieved_file_ref = self._get_file_ref(data_set_meta_info, metafiles=metafiles)
        if retrieved_file_ref is not None:
            file_refs.append(retrieved_file_ref)
        return file_refs

    def _get_file_ref(self, data_set_meta_info: DataSetMetaInfo, bands=None, metafiles=None) -> Optional[FileRef]:
        """auxiliary method to delimit the number of downloaded files for testing"""
        if not self._is_valid_identifier(data_set_meta_info.identifier):
            # consider throwing an exception
            return None
        from sentinelhub import AwsTileRequest
        tile_name = self._get_tile_name(data_set_meta_info.identifier)
        start_time_as_datetime = get_time_from_string(data_set_meta_info.start_time)
        time = start_time_as_datetime.strftime('%Y-%m-%d')
        aws_index = self._get_aws_index(data_set_meta_info.identifier)
        request = AwsTileRequest(tile=tile_name, time=time, aws_index=aws_index,
                                 bands=bands, metafiles=metafiles, data_folder=self._temp_dir)
        year = start_time_as_datetime.year
        month = start_time_as_datetime.month
        day = start_time_as_datetime.day
        logging.info('Downloading S2 Data from {}-{}-{}'.format(month, day, year))
        request.save_data()
        saved_dir = '{}/{},{}-{:02d}-{:02d},{}/'.format(self._temp_dir, tile_name, year, month, day, aws_index)
        new_dir = '{0}/{1}/{2}/{3}/{4}/{5}/{6}/{7}/'.format(self._temp_dir, tile_name[0:2], tile_name[2:3],
                                                            tile_name[3:5], year, month, day, aws_index)
        copy_tree(saved_dir, new_dir)
        logging.info('Downloaded S2 Data from {}-{}-{}'.format(month, day, year))
        return FileRef(new_dir, data_set_meta_info.start_time, data_set_meta_info.end_time, get_mime_type(new_dir))

    def _is_valid_identifier(self, path: str) -> bool:
        return BASIC_AWS_S2_MATCHER.match(path) is not None

    def _get_tile_name(self, id: str) -> str:
        split_id = id.split('/')
        return '{0}{1}{2}'.format(split_id[0], split_id[1], split_id[2])

    def _get_aws_index(self, id: str) -> int:
        return int(id.split('/')[-1])

    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo):
        tile_name = self._get_tile_name(data_set_meta_info.identifier)
        start_time = data_set_meta_info.start_time
        start_time_as_datetime = get_time_from_string(data_set_meta_info.start_time)
        year = start_time_as_datetime.year
        month = start_time_as_datetime.month
        day = start_time_as_datetime.day
        aws_index = self._get_aws_index(data_set_meta_info.identifier)
        time = get_time_from_string(start_time).strftime('%Y-%m-%d')
        file_dir = '{0}/{1},{2},{3}/'.format(self._temp_dir, tile_name, time, aws_index)
        other_file_dir = '{0}/{1}/{2}/{3}/{4}/{5}/{6}/{7}/'.format(self._temp_dir, tile_name[0:2], tile_name[2:3],
                                                            tile_name[3:5], year, month, day, aws_index)
        if os.path.exists(file_dir):
            shutil.rmtree(file_dir)
        if os.path.exists(other_file_dir):
            shutil.rmtree(other_file_dir)

    def _get_wrapped_parameters_as_dict(self) -> dict:
        parameters = {'temp_dir': self._temp_dir}
        return parameters

    def clear_cache(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)


class AwsS2FileSystemAccessor(FileSystemAccessor):

    @classmethod
    def name(cls) -> str:
        return _NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> AwsS2FileSystem:
        if 'temp_dir' not in parameters.keys():
            raise ValueError('No valid temporal directory provided for AWS S2 File System')
        return AwsS2FileSystem(parameters)
