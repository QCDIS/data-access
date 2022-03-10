"""
Description
===========

This module contains an implementation of a file system that allows to get and put data stored on the local hard drive.
"""
from multiply_core.observations import data_validation, get_data_type_path
from multiply_core.util import FileRef, get_days_of_month, get_mime_type, get_time_from_string, is_leap_year
from .data_access import DataSetMetaInfo, FileSystem, FileSystemAccessor
from .data_set_meta_info_extraction import get_data_set_meta_info
from datetime import datetime, timedelta, MAXYEAR
from enum import Enum
from typing import Sequence
import glob
import os.path
import shutil

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"

_DATA_TYPE_PATTERN = 'dt'
_DAY_PATTERN = 'dd'
_MONTH_PATTERN = 'mm'
_YEAR_PATTERN = 'yy'
_ALLOWED_PATTERNS = [_DATA_TYPE_PATTERN, _YEAR_PATTERN, _MONTH_PATTERN, _DAY_PATTERN]
_NAME = 'LocalFileSystem'


class LocalFileSystem(FileSystem):
    """
    A representation of a file system on the local disk.
    """

    def __init__(self, path: str, pattern: str):
        self.path = self._get_validated_path(path)
        pattern = self._validate_pattern(pattern)
        self.pattern = pattern
        self._derive_timestep(self.pattern)

    @classmethod
    def name(cls) -> str:
        """The name of the file system implementation."""
        return _NAME

    def _derive_timestep(self, pattern: str):
        if '/{}/'.format(_DAY_PATTERN) in pattern:
            self.time_step = TimeStep.DAILY
        elif '/{}/'.format(_MONTH_PATTERN) in pattern:
            self.time_step = TimeStep.MONTHLY
        elif '/{}/'.format(_YEAR_PATTERN) in pattern:
            self.time_step = TimeStep.YEARLY
        else:
            self.time_step = TimeStep.NONE

    @staticmethod
    def _get_validated_path(path: str) -> str:
        if not os.path.exists(path):
            os.makedirs(path)
        if not path.endswith('/'):
            path += '/'
        return path

    @staticmethod
    def _validate_pattern(pattern: str) -> str:
        if pattern is '':
            return pattern
        if pattern is None:
            raise ValueError('No pattern provided')
        if pattern.startswith('/'):
            pattern = pattern[1:]
        if pattern.endswith('/'):
            pattern = pattern[:-1]
        split_pattern = pattern.split('/')
        for token in split_pattern:
            if token not in _ALLOWED_PATTERNS:
                raise ValueError('Invalid pattern: {0} not allowed in {1}'.format(token, pattern))
        return '/{}/'.format(pattern)

    def get(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        file_refs = []
        if os.path.exists(data_set_meta_info.identifier):
            mime_type = get_mime_type(data_set_meta_info.identifier)
            file_refs.append(FileRef(data_set_meta_info.identifier, data_set_meta_info.start_time,
                                     data_set_meta_info.end_time, mime_type))
            return file_refs
        relative_path = (self.path + self.pattern).replace('//', '/')
        relative_path = relative_path.replace('/{}/'.format(_DATA_TYPE_PATTERN),
                                              '/{}/'.format(data_set_meta_info.data_type))
        if _DAY_PATTERN not in self.pattern and _MONTH_PATTERN not in self.pattern and \
                _YEAR_PATTERN not in self.pattern:
            if os.path.exists(relative_path):
                file_names = glob.glob(relative_path + '/**', recursive=True)
                for file_name in file_names:
                    file_name = file_name.replace('\\', '/')
                    if data_set_meta_info.identifier in file_name and \
                            data_validation.is_valid(file_name, data_set_meta_info.data_type):
                        mime_type = get_mime_type(file_name)
                        file_refs.append(FileRef(file_name, data_set_meta_info.start_time,
                                                 data_set_meta_info.end_time, mime_type))
            return file_refs
        if data_set_meta_info.start_time is None and data_set_meta_info.end_time is None:
            mime_type = get_mime_type(relative_path)
            file_refs.append(FileRef(relative_path, data_set_meta_info.start_time,
                                     data_set_meta_info.end_time, mime_type))
            return file_refs

        # todo consider (weird) case when a start time but no end time is given
        start_time = get_time_from_string(data_set_meta_info.start_time)
        end_time = get_time_from_string(data_set_meta_info.end_time)
        time = start_time
        while time <= end_time:
            path = relative_path
            path = path.replace('/{}/'.format(_YEAR_PATTERN), '/{:04d}/'.format(time.year))
            path = path.replace('/{}/'.format(_MONTH_PATTERN), '/{:02d}/'.format(time.month))
            path = path.replace('/{}/'.format(_DAY_PATTERN), '/{:02d}/'.format(time.day))
            time = self._get_next_time_step(time)
            if not os.path.exists(path):
                continue
            file_names = glob.glob(path + '/**', recursive=True)
            for file_name in file_names:
                file_name = file_name.replace('\\', '/')
                if data_set_meta_info.identifier in file_name and \
                        data_validation.is_valid(file_name, data_set_meta_info.data_type):
                    mime_type = get_mime_type(file_name)
                    file_refs.append(FileRef(file_name, data_set_meta_info.start_time,
                                             data_set_meta_info.end_time, mime_type))
        return file_refs

    def _get_next_time_step(self, time: datetime) -> datetime:
        if self.time_step == TimeStep.DAILY:
            return time + timedelta(days=1)
        if self.time_step == TimeStep.MONTHLY:
            num_delta_days = get_days_of_month(time.year, time.month)
            return time + timedelta(days=num_delta_days)
        if self.time_step == TimeStep.YEARLY:
            if is_leap_year(time.year):
                return time + timedelta(days=366)
            else:
                return time + timedelta(days=365)
        return datetime(year=MAXYEAR, month=12, day=31)

    def can_put(self) -> bool:
        return True

    def put(self, from_url: str, data_set_meta_info: DataSetMetaInfo):
        # we assume here that it suffices to consider the start time for putting a data set correctly
        data_type_path = get_data_type_path(data_set_meta_info.data_type, from_url)
        relative_path = self.path + self.pattern + data_type_path
        relative_path = relative_path.replace('/{}/'.format(_DATA_TYPE_PATTERN),
                                              '/{}/'.format(data_set_meta_info.data_type))
        if _YEAR_PATTERN in relative_path or _MONTH_PATTERN in relative_path or _DAY_PATTERN in relative_path:
            if data_set_meta_info.start_time is None:
                raise ValueError('Data Set Meta Info is missing required time information')
            time = get_time_from_string(data_set_meta_info.start_time)
            relative_path = relative_path.replace('/{}/'.format(_YEAR_PATTERN), '/{:04d}/'.format(time.year))
            relative_path = relative_path.replace('/{}/'.format(_MONTH_PATTERN), '/{:02d}/'.format(time.month))
            relative_path = relative_path.replace('/{}/'.format(_DAY_PATTERN), '/{:02d}/'.format(time.day))
        if not from_url == relative_path:
            if os.path.isdir(from_url):
                if os.path.exists(relative_path):
                    shutil.rmtree(relative_path)
                shutil.copytree(from_url, relative_path)
            else:
                if not os.path.exists(relative_path):
                    os.makedirs(relative_path)
                shutil.copy(from_url, relative_path)

        return DataSetMetaInfo(data_set_meta_info.coverage, data_set_meta_info.start_time, data_set_meta_info.end_time,
                               data_set_meta_info.data_type, relative_path)

    def remove(self, data_set_meta_info: DataSetMetaInfo):
        # todo test whether this works with aws s2 data too
        time = get_time_from_string(data_set_meta_info.start_time)
        relative_path = self.path + self.pattern
        relative_path = relative_path.replace('/{}/'.format(_DATA_TYPE_PATTERN),
                                              '/{}/'.format(data_set_meta_info.data_type))
        relative_path = relative_path.replace('/{}/'.format(_YEAR_PATTERN), '/{:04d}/'.format(time.year))
        relative_path = relative_path.replace('/{}/'.format(_MONTH_PATTERN), '/{:02d}/'.format(time.month))
        relative_path = relative_path.replace('/{}/'.format(_DAY_PATTERN), '/{:02d}/'.format(time.day))
        if os.path.exists(relative_path):
            file_names = os.listdir(relative_path)
            for file_name in file_names:
                if data_set_meta_info.identifier in file_name:
                    os.remove(relative_path + file_name)
        while not self.path == relative_path and len(os.listdir(relative_path)) == 0:
            os.rmdir(relative_path)
            relative_path = relative_path[:relative_path[:relative_path.rfind('/')].rfind('/')]

    def scan(self) -> Sequence[DataSetMetaInfo]:
        data_set_meta_infos = []
        relative_path = self.path + self.pattern
        relative_path = relative_path.replace('/{}/'.format(_YEAR_PATTERN), '/{}/'.format('*'))
        relative_path = relative_path.replace('/{}/'.format(_MONTH_PATTERN), '/{}/'.format('*'))
        relative_path = relative_path.replace('/{}/'.format(_DAY_PATTERN), '/{}/'.format('*'))
        if _DATA_TYPE_PATTERN in relative_path:
            valid_types = data_validation.get_valid_types()
        else:
            valid_types = ['placeholder']
        for valid_type in valid_types:
            adjusted_relative_path = relative_path.replace('/{}/'.format(_DATA_TYPE_PATTERN), '/{}/'.format(valid_type))
            found_files = glob.glob(adjusted_relative_path + '/**', recursive=True)
            for found_file in found_files:
                found_file = found_file.replace('\\', '/')
                data_type = data_validation.get_valid_type(found_file)
                if data_type is not '':
                    data_set_meta_info = get_data_set_meta_info(data_type, found_file)
                    if data_set_meta_info is not None:
                        data_set_meta_infos.append(data_set_meta_info)
        return data_set_meta_infos

    def get_parameters_as_dict(self) -> dict:
        return {'path': self.path,
                'pattern': self.pattern}

    def clear_cache(self):
        pass


class TimeStep(Enum):
    DAILY = 0
    MONTHLY = 1
    YEARLY = 2
    NONE = 3


class LocalFileSystemAccessor(FileSystemAccessor):
    @classmethod
    def name(cls) -> str:
        """The name of the file system implementation."""
        return _NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> LocalFileSystem:
        if 'path' not in parameters.keys():
            raise ValueError('Required parameter path is missing')
        if 'pattern' not in parameters.keys():
            raise ValueError('Required parameter pattern is missing')
        return LocalFileSystem(path=parameters['path'], pattern=parameters['pattern'])
