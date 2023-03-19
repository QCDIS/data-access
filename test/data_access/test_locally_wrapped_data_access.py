from multiply_core.observations import add_validator, DataValidator
from multiply_core.util import get_mime_type, FileRef, get_time_from_string
from multiply_data_access import DataSetMetaInfo
from multiply_data_access.locally_wrapped_data_access import LocallyWrappedFileSystem, LocallyWrappedMetaInfoProvider
from datetime import datetime
from shapely.geometry import Polygon
from shapely.wkt import loads
from typing import List, Sequence

import os
import shutil

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"


import urllib.request
import zipfile

test_data_save_path = '/tmp/data-access-test_data.zip'
if not os.path.exists(test_data_save_path):
    urllib.request.urlretrieve('https://github.com/QCDIS/data-access/raw/master/test/test_data.zip', test_data_save_path)
    with zipfile.ZipFile(test_data_save_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp')
    zip_ref.close()
base_path = '/tmp/test_data/'


path_to_json_file = base_path + 'test_meta_info.json'
path_to_wrapped_file = base_path + 'a_wrapped_directory/some_wrapped_file'


class TestWrappedMetaInfoProvider(LocallyWrappedMetaInfoProvider):

    @classmethod
    def name(cls) -> str:
        return 'TestProvider'

    def _init_wrapped_meta_info_provider(self, parameters: dict) -> None:
        if 'some_parameter' not in parameters.keys():
            raise ValueError('I required some parameter')
        self._some_parameter = parameters['some_parameter']

    def _query_wrapped_meta_info_provider(self, query_string: str, local_data_set_meta_infos: List[DataSetMetaInfo]) \
            -> List[DataSetMetaInfo]:
        only_dataset = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                       start_time="2017-03-11 14:33:00",
                                       end_time="2017-03-11 14:45:00",
                                       data_type="TYPE_C",
                                       identifier="dterftge")
        if not self.get_roi_from_query_string(query_string).intersects(loads(only_dataset.coverage)):
            return []
        if self.get_start_time_from_query_string(query_string) > get_time_from_string(only_dataset.end_time):
            return []
        if self.get_end_time_from_query_string(query_string) < get_time_from_string(only_dataset.start_time):
            return []
        if 'TYPE_C' not in self.get_data_types_from_query_string(query_string):
            return []
        return [only_dataset]

    def provides_data_type(self, data_type: str) -> bool:
        return data_type == 'TYPE_C'

    def get_provided_data_types(self):
        return ['TYPE_C']

    def encapsulates_data_type(self, data_type: str) -> bool:
        return False

    def _get_wrapped_parameters_as_dict(self) -> dict:
        wrapped_parameters_as_dict = {'some_parameter': self._some_parameter}
        return wrapped_parameters_as_dict


def test_create_wrapped_meta_info_provider():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_2'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        parameters = {'some_parameter': 'something', 'path_to_json_file': path_to_json_file_2}

        wrapped_meta_info_provider = TestWrappedMetaInfoProvider(parameters)

        assert wrapped_meta_info_provider is not None
    finally:
        os.remove(path_to_json_file_2)


def test_wrapped_meta_info_provider_get_as_dict():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_2'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        parameters = {'some_parameter': 'something', 'path_to_json_file': path_to_json_file_2}
        wrapped_meta_info_provider = TestWrappedMetaInfoProvider(parameters)

        provider_as_dict = wrapped_meta_info_provider.get_as_dict()

        assert 2 == len(provider_as_dict)
        assert 'type' in provider_as_dict.keys()
        assert provider_as_dict['type'] == 'TestProvider'
        assert 'parameters' in provider_as_dict.keys()
        assert 2 == len(provider_as_dict['parameters'])
        assert 'some_parameter' in provider_as_dict['parameters']
        assert 'something' == provider_as_dict['parameters']['some_parameter']
        assert 'path_to_json_file' in provider_as_dict['parameters']
        assert path_to_json_file_2 == provider_as_dict['parameters']['path_to_json_file']
    finally:
        os.remove(path_to_json_file_2)


def test_supported_type():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_2'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        parameters = {'some_parameter': 'something', 'path_to_json_file': path_to_json_file_2}
        wrapped_meta_info_provider = TestWrappedMetaInfoProvider(parameters)

        assert not wrapped_meta_info_provider.provides_data_type('TYPE_A')
        assert not wrapped_meta_info_provider.provides_data_type('TYPE_B')
        assert wrapped_meta_info_provider.provides_data_type('TYPE_C')
    finally:
        os.remove(path_to_json_file_2)


def test_query():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_2'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        parameters = {'some_parameter': 'something', 'path_to_json_file': path_to_json_file_2}
        wrapped_meta_info_provider = TestWrappedMetaInfoProvider(parameters)

        query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-10;2017-03-10;TYPE_C"
        data_set_meta_infos = wrapped_meta_info_provider.query(query_string)
        assert len(data_set_meta_infos) == 1
        assert data_set_meta_infos[0].coverage == 'POLYGON((0 35, 10 35, 10 35, 0 45, 0 35))'
        assert data_set_meta_infos[0].start_time == '2017-03'
        assert data_set_meta_infos[0].end_time == '2017-03'
        assert data_set_meta_infos[0].data_type == 'TYPE_C'
        assert data_set_meta_infos[0].identifier == 'vgfbhngf'

        other_query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-10;2017-03-11;TYPE_C"
        other_data_set_meta_infos = wrapped_meta_info_provider.query(other_query_string)
        assert len(other_data_set_meta_infos) == 2
        assert other_data_set_meta_infos[0].coverage == 'POLYGON((0 35, 10 35, 10 35, 0 45, 0 35))'
        assert other_data_set_meta_infos[0].start_time == '2017-03'
        assert other_data_set_meta_infos[0].end_time == '2017-03'
        assert other_data_set_meta_infos[0].data_type == 'TYPE_C'
        assert other_data_set_meta_infos[0].identifier == 'vgfbhngf'
        assert other_data_set_meta_infos[1].coverage == "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))"
        assert other_data_set_meta_infos[1].start_time == '2017-03-11 14:33:00'
        assert other_data_set_meta_infos[1].end_time == '2017-03-11 14:45:00'
        assert other_data_set_meta_infos[1].data_type == 'TYPE_C'
        assert other_data_set_meta_infos[1].identifier == 'dterftge'
    finally:
        os.remove(path_to_json_file_2)


def test_query_local():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_2'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        parameters = {'some_parameter': 'something', 'path_to_json_file': path_to_json_file_2}
        wrapped_meta_info_provider = TestWrappedMetaInfoProvider(parameters)

        query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-10;2017-03-10;TYPE_C"
        data_set_meta_infos = wrapped_meta_info_provider.query_local(query_string)
        assert len(data_set_meta_infos) == 1
        assert data_set_meta_infos[0].coverage == 'POLYGON((0 35, 10 35, 10 35, 0 45, 0 35))'
        assert data_set_meta_infos[0].start_time == '2017-03'
        assert data_set_meta_infos[0].end_time == '2017-03'
        assert data_set_meta_infos[0].data_type == 'TYPE_C'
        assert data_set_meta_infos[0].identifier == 'vgfbhngf'

        other_query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-10;2017-03-11;TYPE_C"
        other_data_set_meta_infos = wrapped_meta_info_provider.query_local(other_query_string)
        assert len(other_data_set_meta_infos) == 1
        assert other_data_set_meta_infos[0].coverage == 'POLYGON((0 35, 10 35, 10 35, 0 45, 0 35))'
        assert other_data_set_meta_infos[0].start_time == '2017-03'
        assert other_data_set_meta_infos[0].end_time == '2017-03'
        assert other_data_set_meta_infos[0].data_type == 'TYPE_C'
        assert other_data_set_meta_infos[0].identifier == 'vgfbhngf'
    finally:
        os.remove(path_to_json_file_2)


def test_query_non_local():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_2'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        parameters = {'some_parameter': 'something', 'path_to_json_file': path_to_json_file_2}
        wrapped_meta_info_provider = TestWrappedMetaInfoProvider(parameters)

        query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-10;2017-03-10;TYPE_C"
        data_set_meta_infos = wrapped_meta_info_provider.query_non_local(query_string)
        assert len(data_set_meta_infos) == 0

        other_query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-10;2017-03-11;TYPE_C"
        other_data_set_meta_infos = wrapped_meta_info_provider.query_non_local(other_query_string)
        assert len(other_data_set_meta_infos) == 1
        assert other_data_set_meta_infos[0].coverage == "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))"
        assert other_data_set_meta_infos[0].start_time == '2017-03-11 14:33:00'
        assert other_data_set_meta_infos[0].end_time == '2017-03-11 14:45:00'
        assert other_data_set_meta_infos[0].data_type == 'TYPE_C'
        assert other_data_set_meta_infos[0].identifier == 'dterftge'
    finally:
        os.remove(path_to_json_file_2)


class TestWrappedFileSystem(LocallyWrappedFileSystem):

    @classmethod
    def name(cls) -> str:
        return 'TestWrappedFileSystem'

    def _init_wrapped_file_system(self, parameters: dict) -> None:
        if 'some_parameter' not in parameters.keys():
            raise ValueError('I required some parameter')
        self._some_parameter = parameters['some_parameter']

    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo) -> None:
        pass

    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        file_refs = []
        if data_set_meta_info.identifier == 'some_wrapped_file':
            file_refs.append(FileRef(path_to_wrapped_file,
                                     data_set_meta_info.start_time,
                                     data_set_meta_info.end_time,
                                     get_mime_type(path_to_wrapped_file)))
        return file_refs

    def _get_wrapped_parameters_as_dict(self) -> dict:
        wrapped_parameters_as_dict = {'some_parameter': self._some_parameter}
        return wrapped_parameters_as_dict

    def clear_cache(self):
        pass


def test_locally_wrappd_file_system_create():
    parameters = {'some_parameter': 'something', 'path': base_path + '', 'pattern': '/dt/yy/MM/dd/'}
    wrapped_file_system = TestWrappedFileSystem(parameters)

    assert wrapped_file_system is not None


def test_locally_wrapped_file_system_get_name():
    parameters = {'some_parameter': 'something', 'path': base_path + '', 'pattern': '/dt/yy/MM/dd/'}
    wrapped_file_system = TestWrappedFileSystem(parameters)

    assert 'TestWrappedFileSystem' == wrapped_file_system.name()
    assert 'TestWrappedFileSystem' == TestWrappedFileSystem.name()


def test_wrapped_file_system_get_as_dict():
    parameters = {'some_parameter': 'something', 'path': base_path + '', 'pattern': '/dt/yy/MM/dd/'}
    wrapped_file_system = TestWrappedFileSystem(parameters)

    provider_as_dict = wrapped_file_system.get_as_dict()

    assert 2 == len(provider_as_dict)
    assert 'type' in provider_as_dict.keys()
    assert provider_as_dict['type'] == 'TestWrappedFileSystem'
    assert 'parameters' in provider_as_dict.keys()
    assert 3 == len(provider_as_dict['parameters'])
    assert 'some_parameter' in provider_as_dict['parameters']
    assert 'something' == provider_as_dict['parameters']['some_parameter']
    assert 'path' in provider_as_dict['parameters']
    assert base_path + '' == provider_as_dict['parameters']['path']
    assert 'pattern' in provider_as_dict['parameters']
    assert '/dt/yy/MM/dd/' == provider_as_dict['parameters']['pattern']


class TypeXValidator(DataValidator):

    @classmethod
    def name(cls) -> str:
        return 'TYPE_X'

    def get_relative_path(self, path: str) -> str:
        return ''

    def is_valid(self, path: str) -> bool:
        return path.endswith('some_wrapped_file')

    def get_file_pattern(self) -> str:
        return ''

    def is_valid_for(self, path: str, roi: Polygon, start_time: datetime, end_time: datetime) -> bool:
        return self.is_valid(path)

    @staticmethod
    def differs_by_name(cls):
        return False


def test_wrapped_file_system_get():
    try:
        parameters = {'some_parameter': 'something', 'path': base_path + '', 'pattern': '/dt/yy/'}
        wrapped_file_system = TestWrappedFileSystem(parameters)
        add_validator(TypeXValidator())

        data_set_meta_info = DataSetMetaInfo('some_polygon', '2017-01-31', '2017-02-01', 'TYPE_X', 'some_wrapped_file')
        file_refs = wrapped_file_system.get(data_set_meta_info)
        assert 1 == len(file_refs)
        assert '2017-01-31' == file_refs[0].start_time
        assert '2017-02-01' == file_refs[0].end_time
        assert 'unknown mime type' == file_refs[0].mime_type
        assert base_path + 'TYPE_X/2017/some_wrapped_file'
    finally:
        if os.path.exists(base_path + 'TYPE_X'):
            shutil.rmtree(base_path + 'TYPE_X')
