__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

from multiply_data_access.lpdaac_data_access import DataSetMetaInfo, LpDaacFileSystem, LpDaacFileSystemAccessor
import os

H17_V05_COVERAGE = 'POLYGON ((-13.05407289035348 39.99999999616804, -11.54700538146705 29.9999999970181, ' \
                '1.127072786096139e-09 39.99999999616804, 9.96954409223065e-10 29.9999999970181, ' \
                '-13.05407289035348 39.99999999616804))'
H17_V04_COVERAGE = 'POLYGON ((-15.55723826442343 49.99999999531797, -13.05407289035348 39.99999999616804, ' \
                   '1.343193041889809e-09 49.99999999531797, 1.127072786096139e-09 39.99999999616804, ' \
                   '-15.55723826442343 49.99999999531797))'
import urllib.request
import zipfile

test_data_save_path = '/tmp/data-access-test_data.zip'
if not os.path.exists(test_data_save_path):
    urllib.request.urlretrieve('https://github.com/QCDIS/data-access/raw/master/test/test_data.zip', test_data_save_path)
    with zipfile.ZipFile(test_data_save_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp')
    zip_ref.close()
base_path = '/tmp/test_data/'


def test_lpdaac_file_system_creation():
    parameters = {'path': base_path + '', 'pattern': '', 'temp_dir': base_path + '', 'username': 'dummy',
                  'password': 'dummy'}
    file_system = LpDaacFileSystemAccessor.create_from_parameters(parameters)

    assert file_system is not None


def test_lpdaac_file_system_name():
    parameters = {'path': base_path + '', 'pattern': '', 'temp_dir': base_path + '', 'username': 'dummy',
                  'password': 'dummy'}
    file_system = LpDaacFileSystemAccessor.create_from_parameters(parameters)

    assert 'LpDaacFileSystem' == file_system.name()
    assert 'LpDaacFileSystem' == LpDaacFileSystem.name()
    assert 'LpDaacFileSystem' == LpDaacFileSystemAccessor.name()


def test_get_parameters_as_dict():
    parameters = {'path': base_path + '', 'pattern': '', 'temp_dir': base_path + '', 'username': 'dummyuser',
                  'password': 'dummypass'}
    file_system = LpDaacFileSystemAccessor.create_from_parameters(parameters)

    parameters = file_system.get_parameters_as_dict()

    assert 5 == len(parameters)
    assert 'path' in parameters.keys()
    assert base_path + '' == parameters['path']
    assert 'pattern' in parameters.keys()
    assert '' == parameters['pattern']
    assert 'temp_dir' in parameters.keys()
    assert base_path + '' == parameters['temp_dir']
    assert 'username' in parameters.keys()
    assert 'dummyuser' == parameters['username']
    assert 'password' in parameters.keys()
    assert 'dummypass' == parameters['password']


def test_notify_copied_to_local():
    parameters = {'path': base_path + '', 'pattern': '', 'temp_dir': base_path + '', 'username': 'dummyuser',
                  'password': 'dummypass'}
    file_system = LpDaacFileSystemAccessor.create_from_parameters(parameters)

    path_to_file = base_path + 'MCD43A1.A2017247.h17v05.006.2017256031007.hdf'
    try:
        open(path_to_file, 'w+')
        data_set_meta_info = DataSetMetaInfo('ctfvgb', '2017-09-04', '2017-09-04', 'MCD43A1.006',
                                             'MCD43A1.A2017247.h17v05.006.2017256031007.hdf')
        file_system._notify_copied_to_local(data_set_meta_info)

        assert not os.path.exists(path_to_file)
    finally:
        if os.path.exists(path_to_file):
            os.remove(path_to_file)

