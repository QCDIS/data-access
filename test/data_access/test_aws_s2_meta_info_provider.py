__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

import os

from multiply_core.util import get_time_from_string
from multiply_data_access.aws_s2_meta_info_provider import AwsS2MetaInfoProvider, AwsS2MetaInfoProviderAccessor, \
    _get_tile_stripes, _get_center_tile_identifiers, TileDescription
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


BARRAX_POLYGON = "POLYGON((-2.20397502663252 39.09868106889479,-1.9142106223355313 39.09868106889479," \
                 "-1.9142106223355313 38.94504502508093,-2.20397502663252 38.94504502508093," \
                 "-2.20397502663252 39.09868106889479))"
BARRAX_TILE = 'POLYGON((-3.00023345437724 39.7502679265611,-3.00023019602957 38.7608644567253,-1.73659678081167 ' \
              '38.7540360477761,-1.71871965133358 39.7431961916792,-3.00023345437724 39.7502679265611))'

path_to_json_file = base_path + 'single_store.json'
SQB_29_COVERAGE = "POLYGON ((-6.72492653925008 37.9255905472328, -6.75467671036015 36.9366503972109, " \
                  "-5.52344565574506 36.9069718125641, -5.47744908496312 37.8948386584933, " \
                  "-6.72492653925008 37.9255905472328))"
STG_30_COVERAGE = "POLYGON ((-6.41197247866992 37.8980997872802, -6.36741300312877 36.9101191610502, " \
                  "-5.13602504583555 36.9386673110729, -5.16432984132288 37.9276804328811, " \
                  "-6.41197247866992 37.8980997872802))"

def test_aws_s2_meta_info_provider_accessor_get_name():
    assert 'AwsS2MetaInfoProvider' == AwsS2MetaInfoProviderAccessor.name()


def test_aws_s2_meta_info_provider_accessor_create_from_parameters():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    assert type(aws_s2_meta_info_provider) == AwsS2MetaInfoProvider


def test_aws_s2_meta_info_provider_get_name():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    assert 'AwsS2MetaInfoProvider' == aws_s2_meta_info_provider.name()


def test_aws_s2_meta_info_provider_provides_data_type():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)

    assert not aws_s2_meta_info_provider.provides_data_type('AWS_S2_L2')
    assert not aws_s2_meta_info_provider.provides_data_type('hdtgbhhj')
    assert aws_s2_meta_info_provider.provides_data_type('AWS_S2_L1C')


def test_aws_s2_meta_info_provider_get_parameters_as_dict():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    parameters_as_dict = aws_s2_meta_info_provider._get_parameters_as_dict()

    assert 1 == len(parameters_as_dict.keys())
    assert 'path_to_json_file' in parameters_as_dict.keys()
    assert path_to_json_file == parameters_as_dict['path_to_json_file']


def test_get_center_tile_identifiers():
    assert ['S'] == _get_center_tile_identifiers(38.94504502508093, 39.09868106889479)
    assert ['R', 'S', 'T', 'U'] == _get_center_tile_identifiers(28.94, 52.43)
    assert ['C'] == _get_center_tile_identifiers(-84., -81.)
    assert ['C'] == _get_center_tile_identifiers(-78., -75.)
    assert ['X'] == _get_center_tile_identifiers(81., 84.)
    assert ['X'] == _get_center_tile_identifiers(75., 78.)


def test_get_tile_stripes():
    assert [30] == _get_tile_stripes(-5., -1.)
    assert [28, 29, 30, 31, 32] == _get_tile_stripes(-15., 10.)
    assert [1, 2] == _get_tile_stripes(-176., -170.)
    assert [59, 60] == _get_tile_stripes(170., 176.)
    assert [59, 60, 1, 2] == _get_tile_stripes(170., -170.)
    assert [60, 1] == _get_tile_stripes(176., -176.)


def test_read_sub_lut():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    sub_lut = aws_s2_meta_info_provider._read_sub_lut('30', 'S')

    for key in sub_lut.keys():
        assert key.startswith('30S')


def test_get_affected_tile_descriptions():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    barrax_geometry = loads(BARRAX_POLYGON)
    affected_tile_ids = aws_s2_meta_info_provider.get_affected_tile_descriptions(barrax_geometry)

    assert 1 == len(affected_tile_ids)
    assert '30SWJ' == affected_tile_ids[0].tile_id
    assert BARRAX_TILE == affected_tile_ids[0].coverage

    large_polygon = loads("POLYGON((-15. 52.43,10. 52.43, 10. 28.94,-15. 28.94,-15. 52.43))")
    affected_tile_ids = aws_s2_meta_info_provider.get_affected_tile_descriptions(large_polygon)

    for tile_description in affected_tile_ids:
        assert tile_description.tile_id.startswith('28R') or tile_description.tile_id.startswith('29R') or \
               tile_description.tile_id.startswith('30R') or tile_description.tile_id.startswith('31R') or \
               tile_description.tile_id.startswith('32R') or tile_description.tile_id.startswith('28S') or \
               tile_description.tile_id.startswith('29S') or tile_description.tile_id.startswith('30S') or \
               tile_description.tile_id.startswith('31S') or tile_description.tile_id.startswith('32S') or \
               tile_description.tile_id.startswith('28T') or tile_description.tile_id.startswith('29T') or \
               tile_description.tile_id.startswith('30T') or tile_description.tile_id.startswith('31T') or \
               tile_description.tile_id.startswith('32T') or tile_description.tile_id.startswith('28U') or \
               tile_description.tile_id.startswith('29U') or tile_description.tile_id.startswith('30U') or \
               tile_description.tile_id.startswith('31U') or tile_description.tile_id.startswith('32U')


def test_get_data_set_meta_infos_for_tile_description():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    tile_description = TileDescription('30SWJ', BARRAX_TILE)
    start_time = get_time_from_string('2016-04-01')
    end_time = get_time_from_string('2016-04-30')
    data_set_meta_infos = aws_s2_meta_info_provider._get_data_set_meta_infos_for_tile_description(tile_description,
                                                                                                  start_time, end_time)
    assert 6 == len(data_set_meta_infos)
    assert '2016-04-01T10:57:59' == data_set_meta_infos[0].start_time
    assert '30/S/WJ/2016/4/1/0' == data_set_meta_infos[0].identifier
    assert '2016-04-04T11:03:11' == data_set_meta_infos[1].start_time
    assert '30/S/WJ/2016/4/4/0' == data_set_meta_infos[1].identifier
    assert '2016-04-11T10:57:56' == data_set_meta_infos[2].start_time
    assert '30/S/WJ/2016/4/11/0' == data_set_meta_infos[2].identifier
    assert '2016-04-14T11:09:07' == data_set_meta_infos[3].start_time
    assert '30/S/WJ/2016/4/14/0' == data_set_meta_infos[3].identifier
    assert '2016-04-21T10:59:16' == data_set_meta_infos[4].start_time
    assert '30/S/WJ/2016/4/21/0' == data_set_meta_infos[4].identifier
    assert '2016-04-24T11:09:39' == data_set_meta_infos[5].start_time
    assert '30/S/WJ/2016/4/24/0' == data_set_meta_infos[5].identifier


def test_query():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    query_string = "POLYGON((-6.5 37.7, -5.7 37.6, -5.7 37.1, -6.5 37.1, -6.5 37.7));2017-09-04;2017-09-04;AWS_S2_L1C"

    data_set_meta_infos = aws_s2_meta_info_provider.query(query_string)

    assert 2 == len(data_set_meta_infos)
    assert base_path + 'aws_s2_data/29/S/QB/2017/9/4/0/' == data_set_meta_infos[0].identifier
    assert '30/S/TG/2017/9/4/0' == data_set_meta_infos[1].identifier
    for data_set_meta_info in data_set_meta_infos:
        assert data_set_meta_info.start_time == '2017-09-04T11:18:25'
        assert data_set_meta_info.end_time == '2017-09-04T11:18:25'
        assert data_set_meta_info.data_type == 'AWS_S2_L1C'
    data_set_coverage_0 = loads(data_set_meta_infos[0].coverage)
    sqb_29_polygon = loads(SQB_29_COVERAGE)
    assert data_set_coverage_0.almost_equals(sqb_29_polygon)
    data_set_coverage_1 = loads(data_set_meta_infos[1].coverage)
    stg_30_polygon = loads(STG_30_COVERAGE)
    assert data_set_coverage_1.almost_equals(stg_30_polygon)


def test_query_local():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    query_string = "POLYGON((-6.5 37.7, -5.7 37.6, -5.7 37.1, -6.5 37.1, -6.5 37.7));2017-09-04;2017-09-04;AWS_S2_L1C"

    data_set_meta_infos = aws_s2_meta_info_provider.query_local(query_string)

    assert 1 == len(data_set_meta_infos)
    assert base_path + 'aws_s2_data/29/S/QB/2017/9/4/0/' == data_set_meta_infos[0].identifier
    assert data_set_meta_infos[0].start_time == '2017-09-04T11:18:25'
    assert data_set_meta_infos[0].end_time == '2017-09-04T11:18:25'
    assert data_set_meta_infos[0].data_type == 'AWS_S2_L1C'
    data_set_coverage_0 = loads(data_set_meta_infos[0].coverage)
    sqb_29_polygon = loads(SQB_29_COVERAGE)
    assert data_set_coverage_0.almost_equals(sqb_29_polygon)


def test_query_non_local():
    parameters = {'path_to_json_file': path_to_json_file}
    aws_s2_meta_info_provider = AwsS2MetaInfoProviderAccessor.create_from_parameters(parameters)
    query_string = "POLYGON((-6.5 37.7, -5.7 37.6, -5.7 37.1, -6.5 37.1, -6.5 37.7));2017-09-04;2017-09-04;AWS_S2_L1C"

    data_set_meta_infos = aws_s2_meta_info_provider.query_non_local(query_string)

    assert 1 == len(data_set_meta_infos)
    assert '30/S/TG/2017/9/4/0' == data_set_meta_infos[0].identifier
    assert data_set_meta_infos[0].start_time == '2017-09-04T11:18:25'
    assert data_set_meta_infos[0].end_time == '2017-09-04T11:18:25'
    assert data_set_meta_infos[0].data_type == 'AWS_S2_L1C'
    data_set_coverage_0 = loads(data_set_meta_infos[0].coverage)
    stg_30_polygon = loads(STG_30_COVERAGE)
    assert data_set_coverage_0.almost_equals(stg_30_polygon)
