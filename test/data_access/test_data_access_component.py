from multiply_data_access.data_access_component import DataAccessComponent, _build_query_string
from multiply_data_access.json_meta_info_provider import JsonMetaInfoProvider
from multiply_data_access.local_file_system import LocalFileSystem
from multiply_data_access.data_store import DataStore

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


PATH_TO_YAML_FILE = base_path + 'test_data_stores.yml'


def test_data_access_read_data_stores():
    data_access_component = DataAccessComponent()
    data_stores = data_access_component._read_data_stores(PATH_TO_YAML_FILE)
    assert 2 == len(data_stores)

    assert 'Default' == data_stores[0].id
    assert 'Fallback' == data_stores[1].id


def test_put_data_store():
    path_to_yaml_file_2 = base_path + 'test_data_stores_2.yml'
    shutil.copyfile(PATH_TO_YAML_FILE, path_to_yaml_file_2)
    try:
        data_access_component = DataAccessComponent()
        local_file_system = LocalFileSystem(base_path + '', '/yy/dt/dd/')
        json_meta_info_provider = JsonMetaInfoProvider(base_path + 'test_meta_info.json', 'TYPE_A,TYPE_B,TYPE_C')
        data_store = DataStore(local_file_system, json_meta_info_provider, 'a_test')
        data_access_component._put_data_store(data_store, path_to_yaml_file_2)

        data_stores = data_access_component._read_data_stores(path_to_yaml_file_2)
        assert 3 == len(data_stores)
        assert 'Default' == data_stores[0].id
        assert 'Fallback' == data_stores[1].id
        assert 'a_test' == data_stores[2].id
    finally:
        os.remove(path_to_yaml_file_2)


def test_write_data_store_as_dict():
    path_to_yaml_file_2 = base_path + 'test_data_stores_3.yml'
    shutil.copyfile(PATH_TO_YAML_FILE, path_to_yaml_file_2)
    try:
        data_access_component = DataAccessComponent()
        file_system_parameters = {'path': base_path + '', 'pattern': '/yy/dt/dd/'}
        file_system_as_dict = {'type': 'LocalFileSystem', 'parameters': file_system_parameters}
        meta_info_provider_parameters = {'path_to_json_file': base_path + 'test_meta_info.json'}
        meta_info_provider_as_dict = {'type': 'JsonMetaInfoProvider', 'parameters': meta_info_provider_parameters}
        data_store_as_dict = {'FileSystem': file_system_as_dict, 'MetaInfoProvider': meta_info_provider_as_dict,
                              'Id': 'for_testing'}
        data_store = {'DataStore': data_store_as_dict}
        data_access_component._write_data_store_as_dict(data_store, path_to_yaml_file_2)

        data_stores = data_access_component._read_data_stores(path_to_yaml_file_2)
        assert 3 == len(data_stores)

        assert 'Default' == data_stores[0].id
        assert 'Fallback' == data_stores[1].id
        assert 'for_testing' == data_stores[2].id
    finally:
        os.remove(path_to_yaml_file_2)


def test_write_data_store_as_dict_to_empty_file():
    path_to_empty_yaml_file = base_path + 'test_data_stores_4.yml'
    open(path_to_empty_yaml_file, 'w')
    try:
        data_access_component = DataAccessComponent()
        file_system_parameters = {'path': base_path + '', 'pattern': '/yy/dt/dd/'}
        file_system_as_dict = {'type': 'LocalFileSystem', 'parameters': file_system_parameters}
        meta_info_provider_parameters = {'path_to_json_file': base_path + 'test_meta_info.json'}
        meta_info_provider_as_dict = {'type': 'JsonMetaInfoProvider', 'parameters': meta_info_provider_parameters}
        data_store_as_dict = {'FileSystem': file_system_as_dict, 'MetaInfoProvider': meta_info_provider_as_dict,
                              'Id': 'for_testing'}
        data_store = {'DataStore': data_store_as_dict}
        data_access_component._write_data_store_as_dict(data_store, path_to_empty_yaml_file)

        data_stores = data_access_component._read_data_stores(path_to_empty_yaml_file)
        assert 1 == len(data_stores)

        assert 'for_testing' == data_stores[0].id
    finally:
        os.remove(path_to_empty_yaml_file)


def test_create_local_data_store():
    data_access_component = DataAccessComponent()
    data_access_component.create_local_data_store(base_dir=base_path + '',
                                                  meta_info_file=base_path + 'meta_store.json',
                                                  base_pattern='mm/dt/', id='cgfsvt',
                                                  supported_data_types='TYPE_A,TYPE_B')


def test_build_query_string():
    query_string = _build_query_string(roi="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                       start_time="2017-03-21 14:33:00", end_time="2017-03-21 14:45:00",
                                       data_types="TYPE_A,TYPE_B", roi_grid="EPSG:3301")
    expected = "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15));2017-03-21 14:33:00;2017-03-21 14:45:00;" \
               "TYPE_A,TYPE_B;EPSG:3301"

    assert expected == query_string


def test_get_query_strings_regular():
    data_access_component = DataAccessComponent()
    query_strings = data_access_component._get_query_strings(roi="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                                             start_time="2017-03-21 14:33:00",
                                                             end_time="2017-03-21 14:45:00",
                                                             data_types="TYPE_A",
                                                             roi_grid="EPSG:3301")
    assert 1 == len(query_strings)
    expected = "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15));2017-03-21 14:33:00;2017-03-21 14:45:00;" \
               "TYPE_A;EPSG:3301"
    assert expected == query_strings[0]


def test_get_query_strings_sentinel_1_and_emtpy():
    data_access_component = DataAccessComponent()
    query_strings = data_access_component._get_query_strings(roi="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                                             start_time="2017-03-21 14:33:00",
                                                             end_time="2017-03-21 14:45:00",
                                                             data_types="Sentinel-1",
                                                             roi_grid="EPSG:3301")
    assert 2 == len(query_strings)
    expected_1 = "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15));2017-03-21 14:33:00;2017-03-21 14:45:00;" \
                 "S1_SLC;EPSG:3301"
    expected_2 = "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15));2017-03-21 14:33:00;2017-03-21 14:45:00;" \
                 "S1_Speckled;EPSG:3301"
    assert expected_1 == query_strings[0]
    assert expected_2 == query_strings[1]


def test_get_query_strings_sentinel_2_and_other_types():
    data_access_component = DataAccessComponent()
    query_strings = data_access_component._get_query_strings(roi="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                                             start_time="2017-03-21 14:33:00",
                                                             end_time="2017-03-21 14:45:00",
                                                             data_types="TYPE_A,Sentinel-2,TYPE_B",
                                                             roi_grid="EPSG:3301")
    assert 3 == len(query_strings)
    assert "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15));2017-03-21 14:33:00;2017-03-21 14:45:00;" \
           "S2_L1C,AWS_S2_L1C;EPSG:3301" == query_strings[0]
    assert "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15));2017-03-21 14:33:00;2017-03-21 14:45:00;" \
           "S2_L2,AWS_S2_L2;EPSG:3301" == query_strings[1]
    assert "POLYGON((15 15, 25 15, 25 25, 15 25, 15 15));2017-03-21 14:33:00;2017-03-21 14:45:00;" \
           "TYPE_A,TYPE_B;EPSG:3301" == query_strings[2]
