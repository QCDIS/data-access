import os
import pytest
import shutil
from multiply_data_access import DataSetMetaInfo
from multiply_data_access.scihub_data_access import SciHubFileSystem, SciHubFileSystemAccessor, \
    SciHubMetaInfoProvider, SciHubMetaInfoProviderAccessor

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

META_INFO_FILE = base_path + 'local_scihub_store.json'
_scihub_DIR = base_path + 'scihub_dir'
_scihub_TEMP_DIR = base_path + 'scihub_temp_dir'


def test_scihub_meta_info_provider_name():
    parameters = {'path_to_json_file': META_INFO_FILE, 'username':'', 'password': ''}
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert 'SciHubMetaInfoProvider' == scihub_meta_info_provider.name()


def test_scihub_meta_info_provider_provides_data_type():
    parameters = {'path_to_json_file': META_INFO_FILE, 'username':'', 'password': ''}
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert scihub_meta_info_provider.provides_data_type('S1_SLC')
    assert not scihub_meta_info_provider.provides_data_type('S2_L1C')
    assert not scihub_meta_info_provider.provides_data_type('AWS_S2_L1C')
    assert not scihub_meta_info_provider.provides_data_type('')
    # noinspection SpellCheckingInspection
    assert not scihub_meta_info_provider.provides_data_type('vfsgt')


def test_scihub_meta_info_provider_get_provided_data_types():
    parameters = {'path_to_json_file': META_INFO_FILE, 'username':'', 'password': ''}
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    provided_data_types = scihub_meta_info_provider.get_provided_data_types()

    assert 1 == len(provided_data_types)
    assert 'S1_SLC' == provided_data_types[0]


def test_scihub_meta_info_provider_encapsulates_data_type():
    parameters = {'path_to_json_file': META_INFO_FILE, 'username':'', 'password': ''}
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert not scihub_meta_info_provider.encapsulates_data_type('S1_SLC')
    assert not scihub_meta_info_provider.encapsulates_data_type('S2_L1C')
    assert not scihub_meta_info_provider.encapsulates_data_type('')
    # noinspection SpellCheckingInspection
    assert not scihub_meta_info_provider.encapsulates_data_type('vfsgt')


@pytest.mark.skip(reason='Test needs authorization')
def test_scihub_meta_info_provider_query():
    parameters = {'path_to_json_file': META_INFO_FILE}
    parameters['username'] = ''  # enter access key id here
    parameters['password'] = ''  # enter secret access key here
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-03;2018-06-05;S1_SLC"
    data_set_meta_infos = scihub_meta_info_provider.query(query_string)

    assert 1 == len(data_set_meta_infos)
    assert 'S1_SLC'  == data_set_meta_infos[0].data_type
    assert 'S1A_IW_SLC__1SDV_20180603T053307_20180603T053334_022188_026669_A432' == data_set_meta_infos[0].identifier
    assert '2018-06-03T05:33:07.493Z' == data_set_meta_infos[0].start_time
    assert '2018-06-03T05:33:34.589Z' == data_set_meta_infos[0].end_time
    assert '8a44331c-c286-4c28-a15b-d26da4359ae2' == data_set_meta_infos[0].referenced_data
    assert 'POLYGON ((12.121230 52.448013,8.330203 52.855953,8.744157 54.475960,' \
           '12.684868 54.064266,12.121230 52.448013))' == data_set_meta_infos[0].coverage


def test_scihub_meta_info_provider_query_local():
    parameters = {'path_to_json_file': META_INFO_FILE}
    parameters['username'] = ''  # enter access key id here
    parameters['password'] = ''  # enter secret access key here
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-03;2018-06-05;S1_SLC"
    data_set_meta_infos = scihub_meta_info_provider.query_local(query_string)

    assert 0 == len(data_set_meta_infos)


@pytest.mark.skip(reason='Test needs authorization')
def test_scihub_meta_info_provider_query_non_local():
    parameters = {'path_to_json_file': META_INFO_FILE}
    parameters['username'] = ''  # enter access key id here
    parameters['password'] = ''  # enter secret access key here
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-03;2018-06-05;S1_SLC"
    data_set_meta_infos = scihub_meta_info_provider.query_non_local(query_string)

    assert 1 == len(data_set_meta_infos)
    assert 'S1_SLC'  == data_set_meta_infos[0].data_type
    assert 'S1A_IW_SLC__1SDV_20180603T053307_20180603T053334_022188_026669_A432' == data_set_meta_infos[0].identifier
    assert '2018-06-03T05:33:07.493Z' == data_set_meta_infos[0].start_time
    assert '2018-06-03T05:33:34.589Z' == data_set_meta_infos[0].end_time
    assert '8a44331c-c286-4c28-a15b-d26da4359ae2' == data_set_meta_infos[0].referenced_data
    assert 'POLYGON ((12.121230 52.448013,8.330203 52.855953,8.744157 54.475960,' \
           '12.684868 54.064266,12.121230 52.448013))' == data_set_meta_infos[0].coverage


@pytest.mark.skip(reason='Test needs authorization')
def test_scihub_meta_info_provider_query_more_than_fifty_data_sets():
    parameters = {'path_to_json_file': META_INFO_FILE}
    parameters['username'] = ''  # enter access key id here
    parameters['password'] = ''  # enter secret access key here
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-03-01;2018-06-05;S1_SLC"
    data_set_meta_infos = scihub_meta_info_provider.query(query_string)

    assert 70 == len(data_set_meta_infos)


def test_scihub_meta_info_provider_accessor_name():
    assert 'SciHubMetaInfoProvider' == SciHubMetaInfoProviderAccessor.name()


def test_scihub_meta_info_provider_accessor_create_from_parameters():
    parameters = {'path_to_json_file': META_INFO_FILE, 'username':'', 'password': ''}
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert scihub_meta_info_provider is not None
    assert isinstance(scihub_meta_info_provider, SciHubMetaInfoProvider)


def test_scihub_meta_info_provider_get_wrapped_parameters_as_dict():
    parameters = {'path_to_json_file': META_INFO_FILE, 'username':'edftgt', 'password': 'jrehgt'}
    scihub_meta_info_provider = SciHubMetaInfoProviderAccessor.create_from_parameters(parameters)

    wrapped_parameters = scihub_meta_info_provider._get_wrapped_parameters_as_dict()

    assert 2 == len(wrapped_parameters)
    assert 'username' in wrapped_parameters
    assert 'edftgt' == wrapped_parameters['username']
    assert 'password' in wrapped_parameters
    assert 'jrehgt' == wrapped_parameters['password']


def test_scihub_file_system_accessor_name():
    assert 'SciHubFileSystem' == SciHubFileSystemAccessor.name()


def test_scihub_file_system_accessor_create_from_parameters():
    scihub_parameters = {'path': _scihub_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _scihub_TEMP_DIR,
                         'username':'', 'password': ''}
    scihub_file_system = SciHubFileSystemAccessor.create_from_parameters(scihub_parameters)

    assert scihub_file_system is not None
    assert isinstance(scihub_file_system, SciHubFileSystem)


def test_scihub_file_system_name():
    assert 'SciHubFileSystem' == SciHubFileSystem.name()
    scihub_parameters = {'path': _scihub_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _scihub_TEMP_DIR,
                         'username':'', 'password': ''}
    scihub_file_system = SciHubFileSystemAccessor.create_from_parameters(scihub_parameters)
    assert 'SciHubFileSystem' == scihub_file_system.name()


@pytest.mark.skip(reason='Test actually performs downloading and needs authorization')
def test_scihub_file_system_get():
    try:
        scihub_parameters = {'path': _scihub_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _scihub_TEMP_DIR}
        scihub_parameters['username'] = '' # enter access key id here
        scihub_parameters['password'] = '' # enter secret access key here
        scihub_file_system = SciHubFileSystemAccessor.create_from_parameters(scihub_parameters)
        data_set_meta_info = \
            DataSetMetaInfo(coverage='POLYGON ((12.121230 52.448013,8.330203 52.855953,8.744157 54.475960,'
                                     '12.684868 54.064266,12.121230 52.448013))',
                            start_time='2018-06-03T05:33:07.493Z', end_time='2018-06-03T05:33:34.589Z',
                            data_type='S1_SLC',
                            identifier='S1A_IW_SLC__1SDV_20180603T053307_20180603T053334_022188_026669_A432',
                            referenced_data='8a44331c-c286-4c28-a15b-d26da4359ae2')
        file_refs = scihub_file_system.get(data_set_meta_info)
        assert 1 == len(file_refs)
        assert '{}/S2_L1C/2018/06/03/S1A_IW_SLC__1SDV_20180603T053307_20180603T053334_022188_026669_A432'.format(_scihub_DIR) == file_refs[0].url
        assert 'application/x-directory' == file_refs[0].mime_type
    finally:
        if os.path.exists(_scihub_TEMP_DIR):
            shutil.rmtree(_scihub_TEMP_DIR)


def test_scihub_file_system_get_wrapped_parameters_as_dict():
    scihub_parameters = {'path': _scihub_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _scihub_TEMP_DIR, 'username': '',
                         'password': ''}
    scihub_file_system = SciHubFileSystemAccessor.create_from_parameters(scihub_parameters)

    scihub_file_system_as_dict = scihub_file_system._get_wrapped_parameters_as_dict()
    assert scihub_file_system_as_dict is not None
    assert dict == type(scihub_file_system_as_dict)
    assert 3 == len(scihub_file_system_as_dict.keys())
    assert 'username' in scihub_file_system_as_dict
    assert '' == scihub_file_system_as_dict['username']
    assert 'password' in scihub_file_system_as_dict
    assert '' == scihub_file_system_as_dict['password']
    assert 'temp_dir' in scihub_file_system_as_dict
    assert _scihub_TEMP_DIR == scihub_file_system_as_dict['temp_dir']
