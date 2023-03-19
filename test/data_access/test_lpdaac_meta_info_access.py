__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

import os

from multiply_data_access.lpdaac_data_access import LpDaacMetaInfoProvider, LpDaacMetaInfoProviderAccessor
from shapely.wkt import loads

import urllib.request
import zipfile

test_data_save_path = '/tmp/data-access-test_data.zip'
if not os.path.exists(test_data_save_path):
    urllib.request.urlretrieve('https://github.com/QCDIS/data-access/raw/master/test/test_data.zip', test_data_save_path)
    with zipfile.ZipFile(test_data_save_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp')
    zip_ref.close()
base_path = '/tmp/test_data/'

path_to_json_file = base_path + 'modis_store.json'
H17_V05_COVERAGE = 'POLYGON ((-13.05407289035348 39.99999999616804, -11.54700538146705 29.9999999970181, ' \
                '1.127072786096139e-09 39.99999999616804, 9.96954409223065e-10 29.9999999970181, ' \
                '-13.05407289035348 39.99999999616804))'
H17_V04_COVERAGE = 'POLYGON ((-15.55723826442343 49.99999999531797, -13.05407289035348 39.99999999616804, ' \
                   '1.343193041889809e-09 49.99999999531797, 1.127072786096139e-09 39.99999999616804, ' \
                   '-15.55723826442343 49.99999999531797))'


def test_lpdaac_meta_info_provider_create():
    parameters = {'path_to_json_file': path_to_json_file}
    provider = LpDaacMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert provider is not None


def test_lpdaac_meta_info_provider_name():
    parameters = {'path_to_json_file': path_to_json_file}
    provider = LpDaacMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert 'LpDaacMetaInfoProvider' == provider.name()
    assert 'LpDaacMetaInfoProvider' == LpDaacMetaInfoProvider.name()

def test_lpdaac_meta_info_provider_provides_data_type():
    parameters = {'path_to_json_file': path_to_json_file}
    provider = LpDaacMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert provider.provides_data_type('MCD43A1.006')
    assert not provider.provides_data_type('AWS_S2_L1C')
    assert not provider.provides_data_type('Mrtftgeftt')


def test_lpdaac_meta_info_provider_get_h_v_tile_ids():
    parameters = {'path_to_json_file': path_to_json_file}
    provider = LpDaacMetaInfoProviderAccessor.create_from_parameters(parameters)

    h_id_0, v_id_0 = provider._get_h_v_tile_ids(-6., 35.)
    assert 17 == h_id_0
    assert 5 == v_id_0
    h_id_1, v_id_1 = provider._get_h_v_tile_ids(-39., -25.)
    assert 14 == h_id_1
    assert 11 == v_id_1


def test_lpdaac_meta_info_provider_get_id_ranges():
    parameters = {'path_to_json_file': path_to_json_file}
    provider = LpDaacMetaInfoProviderAccessor.create_from_parameters(parameters)

    h_range_0, v_range_0 = provider._get_id_ranges(-6., 35., -6., 35)
    assert [17] == h_range_0
    assert [5] == v_range_0
    h_range_1, v_range_1 = provider._get_id_ranges(-39., -25., -6., 35)
    assert [14, 15, 16, 17] == h_range_1
    assert [5, 6, 7, 8, 9, 10, 11] == v_range_1
    h_range_2, v_range_2 = provider._get_id_ranges(-20., 25., -6., 35)
    assert [16, 17] == h_range_2
    assert [5, 6] == v_range_2


# commented this test, as lpdaac did not like to be queried frequently
# def test_query():
#     parameters = {'path_to_json_file': path_to_json_file}
#     provider = LpDaacMetaInfoProviderAccessor.create_from_parameters(parameters)
#     query_string =
# "POLYGON((-6.5 42.7, -5.7 42.6, -5.7 37.1, -6.5 37.1, -6.5 42.7));2017-09-04;2017-09-04;MCD43A1.006"
#
#     data_set_meta_infos = provider.query(query_string)
#
#     assert 2 == len(data_set_meta_infos)
#     assert 'MCD43A1.A2017247.h17v04.006.2017256031009.hdf' == data_set_meta_infos[0].identifier
#     assert 'MCD43A1.A2017247.h17v05.006.2017256031007.hdf' == data_set_meta_infos[1].identifier
#     for data_set_meta_info in data_set_meta_infos:
#         assert data_set_meta_info.start_time == '2017-09-04'
#         assert data_set_meta_info.end_time == '2017-09-04'
#         assert data_set_meta_info.data_type == 'MCD43A1.006'
#     data_set_coverage_0 = loads(data_set_meta_infos[0].coverage)
#     h17_v04_polygon = loads(H17_V04_COVERAGE)
#     assert data_set_coverage_0.almost_equals(h17_v04_polygon)
#     data_set_coverage_1 = loads(data_set_meta_infos[1].coverage)
#     h17_v05_polygon = loads(H17_V05_COVERAGE)
#     assert data_set_coverage_1.almost_equals(h17_v05_polygon)
