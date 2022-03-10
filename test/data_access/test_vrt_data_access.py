__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

from multiply_data_access.data_access import DataSetMetaInfo
import os

from multiply_core.observations import DataTypeConstants
from multiply_data_access.vrt_data_access import VrtMetaInfoProvider, VrtMetaInfoProviderAccessor, VrtFileSystem, \
    VrtFileSystemAccessor
from shapely.wkt import loads

H17_V05_COVERAGE = 'POLYGON ((-13.05407289035348 39.99999999616804, -11.54700538146705 29.9999999970181, ' \
                   '1.127072786096139e-09 39.99999999616804, 9.96954409223065e-10 29.9999999970181, ' \
                   '-13.05407289035348 39.99999999616804))'
H17_V04_COVERAGE = 'POLYGON ((-15.55723826442343 49.99999999531797, -13.05407289035348 39.99999999616804, ' \
                   '1.343193041889809e-09 49.99999999531797, 1.127072786096139e-09 39.99999999616804, ' \
                   '-15.55723826442343 49.99999999531797))'
PATH_TO_VRT_FILE = './test/test_data/global_dem.vrt'
PATH_TO_OTHER_VRT_FILE = './test/test_data/global_dem_2.vrt'
PATH_TO_NON_EXISTENT_VRT_FILE = './test/test_data/global_dem_3.vrt'
PATH_TO_JSON_FILE = './test/test_data/aster_meta_info.json'
ASTER_POLYGON = "POLYGON ((-5. 37., -4. 37., -4. 36., -5. 36., -5. 37.))"
COVERED_GEOMETRY = 'MULTIPOLYGON (((-7 39, -6 39, -6 38, -7 38, -7 39)), ' \
                   '((-5 37, -4 37, -4 36, -5 36, -6 36, -6 37, -5 37)))'


def test_vrt_meta_info_provider_create():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert provider is not None


def test_vrt_meta_info_provider_name():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert 'VrtMetaInfoProvider' == provider.name()
    assert 'VrtMetaInfoProvider' == VrtMetaInfoProvider.name()
    assert 'VrtMetaInfoProvider' == VrtMetaInfoProviderAccessor.name()


def test_vrt_meta_info_provider_query_vrt_file_does_not_exist_yet():
    parameters = {'path_to_vrt_file': 'a_non_existing_file', 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON ((-4.6 36.8, -4. 36.8, -4. 36.2, -4.6 36.2, -4.6 36.8));2017-09-01;2017-09-12;Aster DEM'
    data_set_meta_infos = provider.query(query_string)

    assert 1 == len(data_set_meta_infos)
    polygon = loads(COVERED_GEOMETRY)
    covered_geometry = loads(data_set_meta_infos[0].coverage)
    assert covered_geometry.almost_equals(polygon)
    assert data_set_meta_infos[0].start_time is None
    assert data_set_meta_infos[0].end_time is None
    assert 'Aster DEM' == data_set_meta_infos[0].data_type
    assert 'a_non_existing_file' == data_set_meta_infos[0].identifier
    assert data_set_meta_infos[0].referenced_data is not None
    assert 'ASTGTM2_N36W005_dem.tif;ASTGTM2_N36W006_dem.tif;ASTGTM2_N38W007_dem.tif' == \
           data_set_meta_infos[0].referenced_data


def test_vrt_meta_info_provider_query_existing_vrt_file_can_use_existing_vrt():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON ((-4.6 36.8, -4. 36.8, -4. 36.2, -4.6 36.2, -4.6 36.8));2017-09-01;2017-09-12;Aster DEM'
    data_set_meta_infos = provider.query(query_string)

    assert 1 == len(data_set_meta_infos)
    polygon = loads(COVERED_GEOMETRY)
    covered_geometry = loads(data_set_meta_infos[0].coverage)
    assert covered_geometry.almost_equals(polygon)
    assert data_set_meta_infos[0].start_time is None
    assert data_set_meta_infos[0].end_time is None
    assert 'Aster DEM' == data_set_meta_infos[0].data_type
    assert PATH_TO_VRT_FILE == data_set_meta_infos[0].identifier
    assert data_set_meta_infos[0].referenced_data is not None
    assert 'ASTGTM2_N36W005_dem.tif;ASTGTM2_N36W006_dem.tif;ASTGTM2_N38W007_dem.tif' == \
           data_set_meta_infos[0].referenced_data


def test_vrt_meta_info_provider_query_local_can_use_existing_vrt():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON ((-4.6 36.8, -4. 36.8, -4. 36.2, -4.6 36.2, -4.6 36.8));2017-09-01;2017-09-12;Aster DEM'
    data_set_meta_infos = provider.query_local(query_string)

    assert 1 == len(data_set_meta_infos)
    polygon = loads(COVERED_GEOMETRY)
    covered_geometry = loads(data_set_meta_infos[0].coverage)
    assert covered_geometry.almost_equals(polygon)
    assert data_set_meta_infos[0].start_time is None
    assert data_set_meta_infos[0].end_time is None
    assert 'Aster DEM' == data_set_meta_infos[0].data_type
    assert PATH_TO_VRT_FILE == data_set_meta_infos[0].identifier
    assert data_set_meta_infos[0].referenced_data is not None
    assert 'ASTGTM2_N36W005_dem.tif;ASTGTM2_N36W006_dem.tif;ASTGTM2_N38W007_dem.tif' == \
           data_set_meta_infos[0].referenced_data


def test_vrt_meta_info_provider_query_non_local_can_use_existing_vrt():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON ((-4.6 36.8, -4. 36.8, -4. 36.2, -4.6 36.2, -4.6 36.8));2017-09-01;2017-09-12;Aster DEM'
    data_set_meta_infos = provider.query_non_local(query_string)


def test_vrt_meta_info_provider_query_local_can_not_use_existing_vrt():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON ((-4.6 36.8, 4. 36.8, 4. 36.2, -4.6 36.2, -4.6 36.8));2017-09-01;2017-09-12;Aster DEM'
    data_set_meta_infos = provider.query_local(query_string)

    assert 0 == len(data_set_meta_infos)


def test_vrt_meta_info_provider_query_existing_vrt_file_new_vrt():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON ((-5.2 36.8, -4.2 36.8, -4.2 36.2, -5.2 36.2, -5.2 36.8));2017-09-01;2017-09-12;Aster DEM'
    data_set_meta_infos = provider.query(query_string)

    assert 1 == len(data_set_meta_infos)
    polygon = loads(COVERED_GEOMETRY)
    covered_geometry = loads(data_set_meta_infos[0].coverage)
    assert covered_geometry.almost_equals(polygon)
    assert data_set_meta_infos[0].start_time is None
    assert data_set_meta_infos[0].end_time is None
    assert 'Aster DEM' == data_set_meta_infos[0].data_type
    assert PATH_TO_VRT_FILE == data_set_meta_infos[0].identifier
    assert data_set_meta_infos[0].referenced_data is not None
    assert 'ASTGTM2_N36W005_dem.tif;ASTGTM2_N36W006_dem.tif;ASTGTM2_N38W007_dem.tif' == \
           data_set_meta_infos[0].referenced_data


def test_vrt_meta_info_provider_query_existing_vrt_file_new_vrt_with_multipolygon():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = 'POLYGON ((-6.8 38.8, -6.2 38.8, -6.2 38.2, -6.8 38.2, -6.8 38.8));2017-09-01;2017-09-12;Aster DEM'
    data_set_meta_infos = provider.query(query_string)

    assert 1 == len(data_set_meta_infos)
    multi_polygon = loads(COVERED_GEOMETRY)
    covered_geometry = loads(data_set_meta_infos[0].coverage)
    assert covered_geometry.almost_equals(multi_polygon)
    assert data_set_meta_infos[0].start_time is None
    assert data_set_meta_infos[0].end_time is None
    assert 'Aster DEM' == data_set_meta_infos[0].data_type
    assert PATH_TO_VRT_FILE == data_set_meta_infos[0].identifier
    assert data_set_meta_infos[0].referenced_data is not None
    assert 'ASTGTM2_N36W005_dem.tif;ASTGTM2_N36W006_dem.tif;ASTGTM2_N38W007_dem.tif' == \
           data_set_meta_infos[0].referenced_data


def test_vrt_meta_info_provider_provides_data_type():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert provider.provides_data_type('Aster DEM')
    assert not provider.provides_data_type(DataTypeConstants.ASTER)
    assert not provider.provides_data_type('dcdvgf')


def test_vrt_meta_info_provider_get_parameters_as_dict():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    parameters_as_dict = provider._get_parameters_as_dict()

    assert 5 == len(parameters_as_dict)
    assert 'path_to_vrt_file' in parameters_as_dict.keys()
    assert PATH_TO_VRT_FILE == parameters_as_dict['path_to_vrt_file']
    assert 'encapsulated_data_type' in parameters_as_dict.keys()
    assert 'ASTER' == parameters_as_dict['encapsulated_data_type']
    assert 'provided_data_type' in parameters_as_dict.keys()
    assert 'Aster DEM' == parameters_as_dict['provided_data_type']
    assert 'accessed_meta_info_provider' in parameters_as_dict.keys()
    assert 'JsonMetaInfoProvider' == parameters_as_dict['accessed_meta_info_provider']
    assert 'path_to_json_file' in parameters_as_dict.keys()
    assert PATH_TO_JSON_FILE == parameters_as_dict['path_to_json_file']


def test_vrt_meta_info_provider_encapsulates_data_type():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert not provider.encapsulates_data_type('Aster DEM')
    assert provider.encapsulates_data_type(DataTypeConstants.ASTER)
    assert not provider.encapsulates_data_type('zgjdh')


def test_vrt_meta_info_provider_get_referenced_data_sets_from_vrt():
    parameters = {'path_to_vrt_file': PATH_TO_OTHER_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'provided_data_type': 'Aster DEM',
                  'accessed_meta_info_provider': 'JsonMetaInfoProvider', 'path_to_json_file': PATH_TO_JSON_FILE}
    provider = VrtMetaInfoProviderAccessor.create_from_parameters(parameters)

    data_sets_from_vrt = provider._get_referenced_data_sets_from_vrt()

    assert 2 == len(data_sets_from_vrt)
    assert 'ASTGTM2_N36W005_dem.tif' == data_sets_from_vrt[0]
    assert 'ASTGTM2_N36W006_dem.tif' == data_sets_from_vrt[1]


def test_vrt_file_system_create():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'accessed_file_system': 'LocalFileSystem', 'path': './test/test_data/', 'pattern': '/dt/'}
    file_system = VrtFileSystemAccessor.create_from_parameters(parameters)

    assert file_system is not None


def test_vrt_file_system_name():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'accessed_file_system': 'LocalFileSystem', 'path': './test/test_data/', 'pattern': '/dt/'}
    file_system = VrtFileSystemAccessor.create_from_parameters(parameters)

    assert 'VrtFileSystem' == file_system.name()
    assert 'VrtFileSystem' == VrtFileSystem.name()
    assert 'VrtFileSystem' == VrtFileSystemAccessor.name()


def test_vrt_file_system_get_parameters_as_dict():
    parameters = {'path_to_vrt_file': PATH_TO_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'accessed_file_system': 'LocalFileSystem', 'path': './test/test_data/', 'pattern': '/dt/'}
    file_system = VrtFileSystemAccessor.create_from_parameters(parameters)

    parameters_as_dict = file_system.get_parameters_as_dict()

    assert 5 == len(parameters_as_dict)
    assert 'path_to_vrt_file' in parameters_as_dict.keys()
    assert PATH_TO_VRT_FILE == parameters_as_dict['path_to_vrt_file']
    assert 'encapsulated_data_type' in parameters_as_dict.keys()
    assert 'ASTER' == parameters_as_dict['encapsulated_data_type']
    assert 'accessed_file_system' in parameters_as_dict.keys()
    assert 'LocalFileSystem' == parameters_as_dict['accessed_file_system']
    assert 'path' in parameters_as_dict.keys()
    assert './test/test_data/' == parameters_as_dict['path']
    assert 'pattern' in parameters_as_dict.keys()
    assert '/dt/' == parameters_as_dict['pattern']


def test_vrt_file_system_get():
    parameters = {'path_to_vrt_file': PATH_TO_NON_EXISTENT_VRT_FILE, 'encapsulated_data_type': DataTypeConstants.ASTER,
                  'accessed_file_system': 'LocalFileSystem', 'path': './test/test_data/', 'pattern': '/dt/'}
    file_system = VrtFileSystemAccessor.create_from_parameters(parameters)

    try:
        data_set_meta_info = DataSetMetaInfo('of no concern here', None, None, DataTypeConstants.ASTER,
                                             PATH_TO_NON_EXISTENT_VRT_FILE, 'ASTGTM2_N36W005_dem.tif')
        file_refs = file_system.get(data_set_meta_info)
        assert 1 == len(file_refs)
        assert PATH_TO_NON_EXISTENT_VRT_FILE == file_refs[0].url
        assert file_refs[0].start_time is None
        assert file_refs[0].end_time is None
        assert 'x-world/x-vrt' == file_refs[0].mime_type

        assert os.path.exists(PATH_TO_NON_EXISTENT_VRT_FILE)
    finally:
        if os.path.exists(PATH_TO_NON_EXISTENT_VRT_FILE):
            os.remove(PATH_TO_NON_EXISTENT_VRT_FILE)
