import os
import pytest
from shapely.wkt import loads
import shutil

from multiply_data_access.data_store import DataStore
from multiply_data_access.local_file_system import LocalFileSystem
from multiply_data_access.json_meta_info_provider import JsonMetaInfoProvider

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'
import urllib.request
import zipfile

test_data_save_path = '/tmp/data-access-test_data.zip'
if not os.path.exists(test_data_save_path):
    urllib.request.urlretrieve('https://github.com/QCDIS/data-access/raw/master/test/test_data.zip', test_data_save_path)
    with zipfile.ZipFile(test_data_save_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp')
    zip_ref.close()
base_path = '/tmp/test_data/'

AWS_S2_DATA_PATH = base_path + 'aws_s2_data'
EMPTY_PATH = base_path + 'empty_dir'
INCORRECT_AWS_S2_META_INFO_FILE = base_path + 'non_existent_meta_info.json'
EMPTY_AWS_S2_META_INFO_FILE = base_path + 'empty_store.json'
PATH_TO_S2_FILE = base_path + 'aws_s2_data/29/S/QB/2017/9/4/0'


def test_put():
    # copy this so we don't mess up the original file
    path_to_incorrect_json_file = EMPTY_AWS_S2_META_INFO_FILE + '_2'
    shutil.copyfile(EMPTY_AWS_S2_META_INFO_FILE, path_to_incorrect_json_file)
    expected_data_dir = base_path + 'empty_dir/29/S/QB/2017/9/4/0'
    try:
        local_file_system = LocalFileSystem(EMPTY_PATH, '')
        meta_info_provider = JsonMetaInfoProvider(path_to_incorrect_json_file, 'AWS_S2_L1C')
        writable_data_store = DataStore(local_file_system, meta_info_provider, 'put_test')

        writable_data_store.put(PATH_TO_S2_FILE)

        data_set_meta_infos_from_file_system = local_file_system.scan()

        assert 1 == len(data_set_meta_infos_from_file_system)
        assert expected_data_dir == data_set_meta_infos_from_file_system[0].identifier

        data_set_meta_infos_from_provider = meta_info_provider.get_all_data()

        assert 1 == len(data_set_meta_infos_from_provider)
        assert expected_data_dir == data_set_meta_infos_from_provider[0].identifier
        assert '2017-09-04 11:18:25' == data_set_meta_infos_from_provider[0].start_time
        assert '2017-09-04 11:18:25' == data_set_meta_infos_from_provider[0].end_time
        covered_geometry_bounds = loads(data_set_meta_infos_from_provider[0].coverage).bounds
        assert covered_geometry_bounds[0] == pytest.approx(-6.754676710360797)
        assert covered_geometry_bounds[1] == pytest.approx(36.906971812661624)
        assert covered_geometry_bounds[2] == pytest.approx(-5.4774490849610435)
        assert covered_geometry_bounds[3] == pytest.approx(37.92559054724302)
        assert os.path.exists(expected_data_dir)

    finally:
        os.remove(path_to_incorrect_json_file)
        shutil.rmtree(EMPTY_PATH + '/29')


def test_update():
    # copy this so we don't mess up the original file
    path_to_incorrect_json_file = INCORRECT_AWS_S2_META_INFO_FILE + '_2'
    shutil.copyfile(INCORRECT_AWS_S2_META_INFO_FILE, path_to_incorrect_json_file)
    try:
        local_file_system = LocalFileSystem(AWS_S2_DATA_PATH, '')
        meta_info_provider = JsonMetaInfoProvider(path_to_incorrect_json_file, None)
        writable_data_store = DataStore(local_file_system, meta_info_provider, 'test')

        writable_data_store.update()

        all_available_files = local_file_system.scan()
        assert 2 == len(all_available_files)
        assert 'AWS_S2_L1C' == all_available_files[0].data_type
        assert 'AWS_S2_L1C' == all_available_files[1].data_type
        assert (base_path + 'aws_s2_data/29/S/QB/2017/9/4/0' == all_available_files[0].identifier and \
               base_path + 'aws_s2_data/34/V/CL/2016/11/22/0' == all_available_files[1].identifier) or \
               (base_path + 'aws_s2_data/29/S/QB/2017/9/4/0' == all_available_files[1].identifier and \
               base_path + 'aws_s2_data/34/V/CL/2016/11/22/0' == all_available_files[0].identifier)

        all_registered_files = meta_info_provider.get_all_data()
        assert 2 == len(all_registered_files)
        assert 'AWS_S2_L1C' == all_registered_files[0].data_type
        assert base_path + 'aws_s2_data/34/V/CL/2016/11/22/0/' == all_registered_files[0].identifier
        assert '2016-11-22 10:03:36' == all_registered_files[0].start_time
        assert '2016-11-22 10:03:36' == all_registered_files[0].end_time
        covered_geometry_bounds = loads(all_registered_files[0].coverage).bounds
        assert covered_geometry_bounds[0] == pytest.approx(17.467397959438937)
        assert covered_geometry_bounds[1] == pytest.approx(58.50637201225454)
        assert covered_geometry_bounds[2] == pytest.approx(19.45040137223655)
        assert covered_geometry_bounds[3] == pytest.approx(59.52863352307349)
        assert 'AWS_S2_L1C' == all_registered_files[1].data_type
        assert base_path + 'aws_s2_data/29/S/QB/2017/9/4/0' == all_registered_files[1].identifier
        assert '2017-09-04 11:18:25' == all_registered_files[1].start_time
        assert '2017-09-04 11:18:25' == all_registered_files[1].end_time
        covered_geometry_bounds = loads(all_registered_files[1].coverage).bounds
        assert covered_geometry_bounds[0] == pytest.approx(-6.754676710360797)
        assert covered_geometry_bounds[1] == pytest.approx(36.906971812661624)
        assert covered_geometry_bounds[2] == pytest.approx(-5.4774490849610435)
        assert covered_geometry_bounds[3] == pytest.approx(37.92559054724302)
    finally:
        os.remove(path_to_incorrect_json_file)
