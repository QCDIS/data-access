__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

import os
import pytest
from multiply_core.observations import DataTypeConstants
from multiply_data_access.data_access import DataSetMetaInfo
from multiply_data_access.general_remote_access import HttpFileSystem, HttpFileSystemAccessor, \
    HttpMetaInfoProvider, HttpMetaInfoProviderAccessor

from shapely import wkt

import urllib.request
import zipfile

test_data_save_path = '/tmp/data-access-test_data.zip'
if not os.path.exists(test_data_save_path):
    urllib.request.urlretrieve('https://github.com/QCDIS/data-access/raw/master/test/test_data.zip', test_data_save_path)
    with zipfile.ZipFile(test_data_save_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp')
    zip_ref.close()
base_path = '/tmp/test_data/'


PATH_TO_JSON_FILE = base_path + 'modis_store.json'
PATH_TO_EMUS_STORE = base_path + 'empty_store.json'
TEMP_DIR = base_path + ''
ELES_TEST_URL = 'http://www2.geog.ucl.ac.uk/~ucfafyi/eles/'
EMUS_TEST_URL = 'http://www2.geog.ucl.ac.uk/~ucfafyi/emus/'
WV_EMU_TEST_URL = 'http://www2.geog.ucl.ac.uk/~ucfafyi/emus/old_emus/'
CAMS_TEST_URL = 'http://www2.geog.ucl.ac.uk/~ucfafyi/cams/'


def test_meta_info_provider_create():
    parameters = {'path_to_json_file': PATH_TO_JSON_FILE, 'url': EMUS_TEST_URL,
                  'supported_data_types': '{}, TYPE_X'.format(DataTypeConstants.MODIS_MCD_43)}
    provider = HttpMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert provider is not None


def test_meta_info_provider_name():
    parameters = {'path_to_json_file': PATH_TO_JSON_FILE, 'url': EMUS_TEST_URL,
                  'supported_data_types': '{}, TYPE_X'.format(DataTypeConstants.MODIS_MCD_43)}
    provider = HttpMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert 'HttpMetaInfoProvider' == provider.name()
    assert 'HttpMetaInfoProvider' == HttpMetaInfoProvider.name()
    assert 'HttpMetaInfoProvider' == HttpMetaInfoProviderAccessor.name()


def test_meta_info_provider_get_parameters_as_dict():
    parameters = {'path_to_json_file': PATH_TO_JSON_FILE, 'url': EMUS_TEST_URL,
                  'supported_data_types': '{}, TYPE_X'.format(DataTypeConstants.MODIS_MCD_43)}
    provider = HttpMetaInfoProviderAccessor.create_from_parameters(parameters)

    parameters_as_dict = provider._get_parameters_as_dict()

    assert 3 == len(parameters_as_dict)
    assert 'path_to_json_file' in parameters_as_dict.keys()
    assert PATH_TO_JSON_FILE == parameters_as_dict['path_to_json_file']
    assert 'url' in parameters_as_dict.keys()
    assert EMUS_TEST_URL == parameters_as_dict['url']
    assert 'supported_data_types' in parameters_as_dict.keys()
    assert 'MCD43A1.006,TYPE_X' == parameters_as_dict['supported_data_types']


@pytest.mark.skip(reason='This test is expensive. Execute to test access to elevation data')
def test_query_wrapped_meta_info_provider_eles():
    parameters = {'path_to_json_file': PATH_TO_JSON_FILE, 'url': ELES_TEST_URL,
                  'data_types': '{}, TYPE_X'.format(DataTypeConstants.ASTER)}
    provider = HttpMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON((-6.5 42.7, -6.7 42.6, -6.7 42.1, -6.5 42.1, -6.5 42.7));2017-09-04;2017-09-04;ASTER'
    data_set_meta_infos = provider._query_wrapped_meta_info_provider(query_string)

    assert 1 == len(data_set_meta_infos)
    expected_aster_coverage = wkt.loads('POLYGON((-7. 42., -7. 43., -6. 43., -6. 42., -7. 42.))')
    aster_coverage = wkt.loads(data_set_meta_infos[0].coverage)
    assert expected_aster_coverage.almost_equals(aster_coverage)
    assert '' == data_set_meta_infos[0].start_time
    assert '' == data_set_meta_infos[0].end_time
    assert 'ASTER' == data_set_meta_infos[0].data_type
    assert 'ASTGTM2_N42W007_dem.tif' == data_set_meta_infos[0].identifier


@pytest.mark.skip(reason='Test will not work when server is down')
def test_query_wrapped_meta_info_provider_emus():
    parameters = {'path_to_json_file': PATH_TO_EMUS_STORE, 'url': EMUS_TEST_URL,
                  'supported_data_types': '{}, {}'.format(DataTypeConstants.S2A_EMULATOR, DataTypeConstants.S2B_EMULATOR)}
    provider = HttpMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON((-6. 42.7, -6.7 42.6, -6.7 42.1, -6. 42.1, -6. 42.7));2017-09-04;2017-09-04;' \
                   'ISO_MSI_A_EMU, ISO_MSI_B_EMU'
    data_set_meta_infos = provider._query_wrapped_meta_info_provider(query_string, [])

    assert 12 == len(data_set_meta_infos)
    for i, data_set_meta_info in enumerate(data_set_meta_infos):
        assert 'POLYGON((-180.0 90.0, 180.0 90.0, 180.0 -90.0, -180.0 -90.0, -180.0 90.0))' == \
               data_set_meta_info.coverage
        assert None == data_set_meta_info.start_time
        assert None == data_set_meta_info.end_time
        if i < 6:
            assert 'ISO_MSI_A_EMU' == data_set_meta_info.data_type
        else:
            assert 'ISO_MSI_B_EMU' == data_set_meta_info.data_type
    assert 'isotropic_MSI_emulators_correction_xap_S2A.pkl' == data_set_meta_infos[0].identifier
    assert 'isotropic_MSI_emulators_correction_xbp_S2A.pkl' == data_set_meta_infos[1].identifier
    assert 'isotropic_MSI_emulators_correction_xcp_S2A.pkl' == data_set_meta_infos[2].identifier
    assert 'isotropic_MSI_emulators_optimization_xap_S2A.pkl' == data_set_meta_infos[3].identifier
    assert 'isotropic_MSI_emulators_optimization_xbp_S2A.pkl' == data_set_meta_infos[4].identifier
    assert 'isotropic_MSI_emulators_optimization_xcp_S2A.pkl' == data_set_meta_infos[5].identifier
    assert 'isotropic_MSI_emulators_correction_xap_S2B.pkl' == data_set_meta_infos[6].identifier
    assert 'isotropic_MSI_emulators_correction_xbp_S2B.pkl' == data_set_meta_infos[7].identifier
    assert 'isotropic_MSI_emulators_correction_xcp_S2B.pkl' == data_set_meta_infos[8].identifier
    assert 'isotropic_MSI_emulators_optimization_xap_S2B.pkl' == data_set_meta_infos[9].identifier
    assert 'isotropic_MSI_emulators_optimization_xbp_S2B.pkl' == data_set_meta_infos[10].identifier
    assert 'isotropic_MSI_emulators_optimization_xcp_S2B.pkl' == data_set_meta_infos[11].identifier


@pytest.mark.skip(reason='Test will not work when server is down')
def test_query_wrapped_meta_info_provider_wv_emu():
    parameters = {'path_to_json_file': PATH_TO_EMUS_STORE, 'url': WV_EMU_TEST_URL,
                  'supported_data_types': '{}'.format(DataTypeConstants.WV_EMULATOR)}
    provider = HttpMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON((-6. 42.7, -6.7 42.6, -6.7 42.1, -6. 42.1, -6. 42.7));2017-09-04;2017-09-04;WV_EMU'
    data_set_meta_infos = provider._query_wrapped_meta_info_provider(query_string, [])

    assert 1 == len(data_set_meta_infos)
    assert 'POLYGON((-180.0 90.0, 180.0 90.0, 180.0 -90.0, -180.0 -90.0, -180.0 90.0))' == \
           data_set_meta_infos[0].coverage
    assert None == data_set_meta_infos[0].start_time
    assert None == data_set_meta_infos[0].end_time
    assert 'WV_EMU' == data_set_meta_infos[0].data_type
    assert 'wv_MSI_retrieval_S2A.pkl' == data_set_meta_infos[0].identifier


def test_file_system_create():
    parameters = {'path': TEMP_DIR, 'pattern': '', 'url': EMUS_TEST_URL, 'temp_dir': TEMP_DIR}
    file_system = HttpFileSystemAccessor.create_from_parameters(parameters)

    assert file_system is not None


def test_file_system_name():
    parameters = {'path': TEMP_DIR, 'pattern': '', 'url': EMUS_TEST_URL, 'temp_dir': TEMP_DIR}
    file_system = HttpFileSystemAccessor.create_from_parameters(parameters)

    assert 'HttpFileSystem' == file_system.name()
    assert 'HttpFileSystem' == HttpFileSystem.name()
    assert 'HttpFileSystem' == HttpFileSystemAccessor.name()


def test_file_system_get_parameters_as_dict():
    parameters = {'path': TEMP_DIR, 'pattern': '', 'url': EMUS_TEST_URL, 'temp_dir': TEMP_DIR}
    file_system = HttpFileSystemAccessor.create_from_parameters(parameters)

    parameters_as_dict = file_system.get_parameters_as_dict()

    assert 4 == len(parameters_as_dict)
    assert 'path' in parameters_as_dict.keys()
    assert TEMP_DIR == parameters_as_dict['path']
    assert 'url' in parameters_as_dict.keys()
    assert EMUS_TEST_URL == parameters_as_dict['url']
    assert 'pattern' in parameters_as_dict.keys()
    assert '' == parameters_as_dict['pattern']
    assert 'temp_dir' in parameters_as_dict.keys()
    assert TEMP_DIR == parameters_as_dict['temp_dir']


def test_notify_copied_to_local():
    parameters = {'path': TEMP_DIR, 'pattern': '', 'url': EMUS_TEST_URL, 'temp_dir': TEMP_DIR}
    file_system = HttpFileSystemAccessor.create_from_parameters(parameters)

    path_to_file = base_path + 'some_file'
    try:
        open(path_to_file, 'w+')
        data_set_meta_info = DataSetMetaInfo('ctfvgb', '2017-09-04', '2017-09-04', 'some_format',
                                             'some_file')
        file_system._notify_copied_to_local(data_set_meta_info)

        assert not os.path.exists(path_to_file)
    finally:
        if os.path.exists(path_to_file):
            os.remove(path_to_file)