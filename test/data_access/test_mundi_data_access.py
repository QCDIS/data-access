import os
import pytest
import shutil
from multiply_data_access import DataSetMetaInfo
from multiply_data_access.mundi_data_access import LocallyWrappedMundiMetaInfoProvider, \
    LocallyWrappedMundiMetaInfoProviderAccessor, MundiObsFileSystem, MundiObsFileSystemAccessor, MundiRestFileSystem, \
    MundiRestFileSystemAccessor, MundiMetaInfoProvider, MundiMetaInfoProviderAccessor
from shapely.wkt import loads

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

META_INFO_FILE = './test/test_data/local_mundi_store.json'
_MUNDI_DIR = './test/test_data/mundi_dir'
_MUNDI_REST_DIR = './test/test_data/mundi_rest_dir'
_MUNDI_TEMP_DIR = './test/test_data/mundi_temp_dir'
_MUNDI_REST_TEMP_DIR = './test/test_data/mundi_rest_temp_dir'


def test_locally_wrapped_mundi_meta_info_provider_name():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert 'MundiMetaInfoProvider' == mundi_meta_info_provider.name()


def test_locally_wrapped_mundi_meta_info_provider_provides_data_type():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert mundi_meta_info_provider.provides_data_type('S2_L1C')
    assert not mundi_meta_info_provider.provides_data_type('AWS_S2_L1C')
    assert not mundi_meta_info_provider.provides_data_type('')
    # noinspection SpellCheckingInspection
    assert not mundi_meta_info_provider.provides_data_type('vfsgt')


def test_locally_wrapped_mundi_meta_info_provider_get_provided_data_types():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    provided_data_types = mundi_meta_info_provider.get_provided_data_types()

    assert 4 == len(provided_data_types)
    expected_data_types = ['S1_SLC', 'S2_L1C', 'S3_L1_OLCI_RR', 'S3_L1_OLCI_FR']
    assert all([a == b for a, b in zip(provided_data_types, expected_data_types)])


def test_locally_wrapped_mundi_meta_info_provider_encapsulates_data_type():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert not mundi_meta_info_provider.encapsulates_data_type('S2_L1C')
    assert not mundi_meta_info_provider.encapsulates_data_type('AWS_S2_L1C')
    assert not mundi_meta_info_provider.encapsulates_data_type('')
    # noinspection SpellCheckingInspection
    assert not mundi_meta_info_provider.encapsulates_data_type('vfsgt')


def test_locally_wrapped_mundi_meta_info_provider_query_s2():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-01;2018-06-05;S2_L1C"
    data_set_meta_infos = mundi_meta_info_provider.query(query_string)

    assert 2 == len(data_set_meta_infos)

    assert 'S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118' == data_set_meta_infos[0].identifier
    expected_coverage = loads('POLYGON ((10.3882277619999996 54.1384156120000029, '
                              '10.3173421249999997 54.0163176499999977, 10.2348201129999996 53.8730417960000025, '
                              '10.1528176469999991 53.7297406859999995, 10.0714324099999999 53.5864079979999985, '
                              '9.9905949619999994 53.4430542019999990, 9.9101521629999993 53.2996597570000006, '
                              '9.8301509550000006 53.1562272170000014, 9.8297230889999998 53.1554540790000019, '
                              '8.9997008679999997 53.1611735449999969, 8.9996937989999992 54.1481041039999980, '
                              '10.3882277619999996 54.1384156120000029))')
    coverage = loads(data_set_meta_infos[0].coverage)
    assert coverage.almost_equals(expected_coverage)

    assert 'S2_L1C' == data_set_meta_infos[0].data_type
    assert '2018-06-02T10:40:19Z' == data_set_meta_infos[0].start_time
    assert '2018-06-02T10:40:19Z' == data_set_meta_infos[0].end_time

    assert 'S2A_MSIL1C_20180604T103021_N0206_R108_T32UNE_20180604T141551' == data_set_meta_infos[1].identifier
    expected_coverage = loads('POLYGON ((9.5329991839999995 54.1443829669999985, '
                              '9.6393092639999995 54.1279838920000032, 9.7303900619999997 54.1138008249999984, '
                              '9.7304462029999996 54.1139137250000033, 9.7459873600000009 54.1115134209999979, '
                              '9.7459783400000006 54.1114953069999984, 9.7461166410000004 54.1114721849999967, '
                              '9.7458160340000006 54.1108685330000014, 10.0791996249999993 54.0551552350000009, '
                              '10.0792399160000006 54.0552348470000013, 10.0829703790000007 54.0546105379999986, '
                              '10.0830927999999993 54.0548524700000002, 10.1046638760000000 54.0511033299999966, '
                              '10.1046137130000009 54.0510042180000028, 10.4340695340000007 53.9936632220000021, '
                              '10.4341582939999995 53.9938358810000025, 10.4518227370000005 53.9907657299999997, '
                              '10.4517716210000007 53.9906664869999986, 10.4518087590000004 53.9906596909999976, '
                              '10.4515281689999995 53.9901149660000002, 10.6729949840000007 53.9495901889999985, '
                              '10.6415649559999999 53.1498598900000019, 8.9997008679999997 53.1611735449999969, '
                              '8.9996937989999992 54.1481041039999980, 9.5329991839999995 54.1443829669999985))')
    coverage = loads(data_set_meta_infos[1].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S2_L1C' == data_set_meta_infos[1].data_type
    assert '2018-06-04T10:30:21Z' == data_set_meta_infos[1].start_time
    assert '2018-06-04T10:30:21Z' == data_set_meta_infos[1].end_time


def test_locally_wrapped_mundi_meta_info_provider_query_s1():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-01;2018-06-05;S1_SLC"
    data_set_meta_infos = mundi_meta_info_provider.query(query_string)

    assert 3 == len(data_set_meta_infos)

    assert 'S1A_IW_SLC__1SDV_20180601T170037_20180601T170104_022166_0265B3_466C' == data_set_meta_infos[0].identifier
    expected_coverage = loads('POLYGON ((9.1527709999999995 54.2447889999999973, '
                              '13.1172269999999997 54.6578639999999965, 13.5328199999999992 53.0389899999999983, '
                              '9.7198080000000004 52.6297950000000014, 9.1527709999999995 54.2447889999999973))')
    coverage = loads(data_set_meta_infos[0].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S1_SLC' == data_set_meta_infos[0].data_type
    assert '2018-06-01T17:00:37Z' == data_set_meta_infos[0].start_time
    assert '2018-06-01T17:00:37Z' == data_set_meta_infos[0].end_time

    assert 'S1B_IW_SLC__1SDV_20180602T054039_20180602T054107_011190_014887_B851' == data_set_meta_infos[1].identifier
    expected_coverage = loads('POLYGON ((10.0823180000000008 52.4006839999999983, '
                              '6.2640330000000004 52.8124690000000001, 6.6777379999999997 54.4328689999999966, '
                              '10.6465929999999993 54.0172839999999965, 10.0823180000000008 52.4006839999999983))')
    coverage = loads(data_set_meta_infos[1].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S1_SLC' == data_set_meta_infos[1].data_type
    assert '2018-06-02T05:40:39Z' == data_set_meta_infos[1].start_time
    assert '2018-06-02T05:40:39Z' == data_set_meta_infos[1].end_time

    assert 'S1A_IW_SLC__1SDV_20180603T053307_20180603T053334_022188_026669_A432' == data_set_meta_infos[2].identifier
    expected_coverage = loads('POLYGON ((12.1212300000000006 52.4480130000000031, '
                              '8.3302029999999991 52.8559529999999995, 8.7441569999999995 54.4759600000000006, '
                              '12.6848679999999998 54.0642660000000035, 12.1212300000000006 52.4480130000000031))')
    coverage = loads(data_set_meta_infos[2].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S1_SLC' == data_set_meta_infos[2].data_type
    assert '2018-06-03T05:33:07Z' == data_set_meta_infos[2].start_time
    assert '2018-06-03T05:33:07Z' == data_set_meta_infos[2].end_time


def test_locally_wrapped_mundi_meta_info_provider_query_local():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)
    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-01;2018-06-05;S1_SLC, S2_L1C"
    data_set_meta_infos = mundi_meta_info_provider.query_local(query_string)
    assert 0 == len(data_set_meta_infos)


def test_locally_wrapped_mundi_meta_info_provider_query_non_local_s1():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-01;2018-06-05;S1_SLC"
    data_set_meta_infos = mundi_meta_info_provider.query_non_local(query_string)

    assert 3 == len(data_set_meta_infos)

    assert 'S1A_IW_SLC__1SDV_20180601T170037_20180601T170104_022166_0265B3_466C' == data_set_meta_infos[0].identifier
    expected_coverage = loads('POLYGON ((9.1527709999999995 54.2447889999999973, '
                              '13.1172269999999997 54.6578639999999965, 13.5328199999999992 53.0389899999999983, '
                              '9.7198080000000004 52.6297950000000014, 9.1527709999999995 54.2447889999999973))')
    coverage = loads(data_set_meta_infos[0].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S1_SLC' == data_set_meta_infos[0].data_type
    assert '2018-06-01T17:00:37Z' == data_set_meta_infos[0].start_time
    assert '2018-06-01T17:00:37Z' == data_set_meta_infos[0].end_time


def test_locally_wrapped_mundi_meta_info_provider_query_more_than_fifty_data_sets():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-03-01;2018-09-05;S2_L1C"
    data_set_meta_infos = mundi_meta_info_provider.query(query_string)

    assert 77 == len(data_set_meta_infos)


def test_locally_wrapped_mundi_meta_info_provider_accessor_name():
    assert 'MundiMetaInfoProvider' == LocallyWrappedMundiMetaInfoProviderAccessor.name()


def test_locally_wrapped_mundi_meta_info_provider_accessor_create_from_parameters():
    parameters = {'path_to_json_file': META_INFO_FILE}
    mundi_meta_info_provider = LocallyWrappedMundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert mundi_meta_info_provider is not None
    assert isinstance(mundi_meta_info_provider, LocallyWrappedMundiMetaInfoProvider)


def test_mundi_meta_info_provider_name():
    assert 'MundiDiasMetaInfoProvider' == MundiMetaInfoProvider({}).name()


def test_mundi_meta_info_provider_query_s2():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-01;2018-06-05;S2_L1C"
    data_set_meta_infos = mundi_meta_info_provider.query(query_string)

    assert 2 == len(data_set_meta_infos)

    assert 'S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118' == data_set_meta_infos[0].identifier
    expected_coverage = loads('POLYGON ((10.3882277619999996 54.1384156120000029, '
                              '10.3173421249999997 54.0163176499999977, 10.2348201129999996 53.8730417960000025, '
                              '10.1528176469999991 53.7297406859999995, 10.0714324099999999 53.5864079979999985, '
                              '9.9905949619999994 53.4430542019999990, 9.9101521629999993 53.2996597570000006, '
                              '9.8301509550000006 53.1562272170000014, 9.8297230889999998 53.1554540790000019, '
                              '8.9997008679999997 53.1611735449999969, 8.9996937989999992 54.1481041039999980, '
                              '10.3882277619999996 54.1384156120000029))')
    coverage = loads(data_set_meta_infos[0].coverage)
    assert coverage.almost_equals(expected_coverage)

    assert 'S2_L1C' == data_set_meta_infos[0].data_type
    assert '2018-06-02T10:40:19Z' == data_set_meta_infos[0].start_time
    assert '2018-06-02T10:40:19Z' == data_set_meta_infos[0].end_time

    assert 'S2A_MSIL1C_20180604T103021_N0206_R108_T32UNE_20180604T141551' == data_set_meta_infos[1].identifier
    expected_coverage = loads('POLYGON ((9.5329991839999995 54.1443829669999985, '
                              '9.6393092639999995 54.1279838920000032, 9.7303900619999997 54.1138008249999984, '
                              '9.7304462029999996 54.1139137250000033, 9.7459873600000009 54.1115134209999979, '
                              '9.7459783400000006 54.1114953069999984, 9.7461166410000004 54.1114721849999967, '
                              '9.7458160340000006 54.1108685330000014, 10.0791996249999993 54.0551552350000009, '
                              '10.0792399160000006 54.0552348470000013, 10.0829703790000007 54.0546105379999986, '
                              '10.0830927999999993 54.0548524700000002, 10.1046638760000000 54.0511033299999966, '
                              '10.1046137130000009 54.0510042180000028, 10.4340695340000007 53.9936632220000021, '
                              '10.4341582939999995 53.9938358810000025, 10.4518227370000005 53.9907657299999997, '
                              '10.4517716210000007 53.9906664869999986, 10.4518087590000004 53.9906596909999976, '
                              '10.4515281689999995 53.9901149660000002, 10.6729949840000007 53.9495901889999985, '
                              '10.6415649559999999 53.1498598900000019, 8.9997008679999997 53.1611735449999969, '
                              '8.9996937989999992 54.1481041039999980, 9.5329991839999995 54.1443829669999985))')
    coverage = loads(data_set_meta_infos[1].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S2_L1C' == data_set_meta_infos[1].data_type
    assert '2018-06-04T10:30:21Z' == data_set_meta_infos[1].start_time
    assert '2018-06-04T10:30:21Z' == data_set_meta_infos[1].end_time


def test_mundi_meta_info_provider_query_s1():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-01;2018-06-05;S1_SLC"
    data_set_meta_infos = mundi_meta_info_provider.query(query_string)

    assert 3 == len(data_set_meta_infos)

    assert 'S1A_IW_SLC__1SDV_20180601T170037_20180601T170104_022166_0265B3_466C' == data_set_meta_infos[0].identifier
    expected_coverage = loads('POLYGON ((9.1527709999999995 54.2447889999999973, '
                              '13.1172269999999997 54.6578639999999965, 13.5328199999999992 53.0389899999999983, '
                              '9.7198080000000004 52.6297950000000014, 9.1527709999999995 54.2447889999999973))')
    coverage = loads(data_set_meta_infos[0].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S1_SLC' == data_set_meta_infos[0].data_type
    assert '2018-06-01T17:00:37Z' == data_set_meta_infos[0].start_time
    assert '2018-06-01T17:00:37Z' == data_set_meta_infos[0].end_time

    assert 'S1B_IW_SLC__1SDV_20180602T054039_20180602T054107_011190_014887_B851' == data_set_meta_infos[1].identifier
    expected_coverage = loads('POLYGON ((10.0823180000000008 52.4006839999999983, '
                              '6.2640330000000004 52.8124690000000001, 6.6777379999999997 54.4328689999999966, '
                              '10.6465929999999993 54.0172839999999965, 10.0823180000000008 52.4006839999999983))')
    coverage = loads(data_set_meta_infos[1].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S1_SLC' == data_set_meta_infos[1].data_type
    assert '2018-06-02T05:40:39Z' == data_set_meta_infos[1].start_time
    assert '2018-06-02T05:40:39Z' == data_set_meta_infos[1].end_time

    assert 'S1A_IW_SLC__1SDV_20180603T053307_20180603T053334_022188_026669_A432' == data_set_meta_infos[2].identifier
    expected_coverage = loads('POLYGON ((12.1212300000000006 52.4480130000000031, '
                              '8.3302029999999991 52.8559529999999995, 8.7441569999999995 54.4759600000000006, '
                              '12.6848679999999998 54.0642660000000035, 12.1212300000000006 52.4480130000000031))')
    coverage = loads(data_set_meta_infos[2].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S1_SLC' == data_set_meta_infos[2].data_type
    assert '2018-06-03T05:33:07Z' == data_set_meta_infos[2].start_time
    assert '2018-06-03T05:33:07Z' == data_set_meta_infos[2].end_time


def test_mundi_meta_info_provider_query_local():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)
    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-01;2018-06-05;S1_SLC, S2_L1C"
    data_set_meta_infos = mundi_meta_info_provider.query_local(query_string)
    assert 0 == len(data_set_meta_infos)


def test_mundi_meta_info_provider_query_non_local_s1():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-06-01;2018-06-05;S1_SLC"
    data_set_meta_infos = mundi_meta_info_provider.query_non_local(query_string)

    assert 3 == len(data_set_meta_infos)

    assert 'S1A_IW_SLC__1SDV_20180601T170037_20180601T170104_022166_0265B3_466C' == data_set_meta_infos[0].identifier
    expected_coverage = loads('POLYGON ((9.1527709999999995 54.2447889999999973, '
                              '13.1172269999999997 54.6578639999999965, 13.5328199999999992 53.0389899999999983, '
                              '9.7198080000000004 52.6297950000000014, 9.1527709999999995 54.2447889999999973))')
    coverage = loads(data_set_meta_infos[0].coverage)
    assert coverage.almost_equals(expected_coverage)
    assert 'S1_SLC' == data_set_meta_infos[0].data_type
    assert '2018-06-01T17:00:37Z' == data_set_meta_infos[0].start_time
    assert '2018-06-01T17:00:37Z' == data_set_meta_infos[0].end_time


def test_mundi_meta_info_provider_query_more_than_fifty_data_sets():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    query_string = "POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6));2018-03-01;2018-09-05;S2_L1C"
    data_set_meta_infos = mundi_meta_info_provider.query(query_string)

    assert 77 == len(data_set_meta_infos)


def test_mundi_meta_info_provider_provides_data_type():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)
    assert mundi_meta_info_provider.provides_data_type('S2_L1C')
    assert not mundi_meta_info_provider.provides_data_type('AWS_S2_L1C')
    assert not mundi_meta_info_provider.provides_data_type('')
    # noinspection SpellCheckingInspection
    assert not mundi_meta_info_provider.provides_data_type('vfsgt')


def test_mundi_meta_info_provider_get_provided_data_types():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)
    provided_data_types = mundi_meta_info_provider.get_provided_data_types()
    assert 4 == len(provided_data_types)
    expected_data_types = ['S1_SLC', 'S2_L1C', 'S3_L1_OLCI_RR', 'S3_L1_OLCI_FR']
    assert all([a == b for a, b in zip(provided_data_types, expected_data_types)])


def test_mundi_meta_info_provider_encapsulates_data_type():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)
    assert not mundi_meta_info_provider.encapsulates_data_type('S2_L1C')
    assert not mundi_meta_info_provider.encapsulates_data_type('AWS_S2_L1C')
    assert not mundi_meta_info_provider.encapsulates_data_type('')
    # noinspection SpellCheckingInspection
    assert not mundi_meta_info_provider.encapsulates_data_type('vfsgt')


def test_mundi_meta_info_provider_can_update():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert not mundi_meta_info_provider.can_update()


def test_mundi_meta_info_provider_get_all_data():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)
    all_data = mundi_meta_info_provider.get_all_data()
    assert 0 == len(all_data)


def test_mundi_meta_info_provider_get_as_dict():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    mundi_meta_info_provider_dict = mundi_meta_info_provider.get_as_dict()
    assert 'type' in mundi_meta_info_provider_dict.keys()
    assert 'MundiDiasMetaInfoProvider' == mundi_meta_info_provider_dict['type']
    assert 'parameters' in mundi_meta_info_provider_dict.keys()
    assert 0 == len(mundi_meta_info_provider_dict['parameters'])


def test_mundi_meta_info_provider_accessor_name():
    assert 'MundiDiasMetaInfoProvider' == MundiMetaInfoProviderAccessor.name()


def test_mundi_meta_info_provider_accessor_create_from_parameters():
    parameters = {}
    mundi_meta_info_provider = MundiMetaInfoProviderAccessor.create_from_parameters(parameters)

    assert mundi_meta_info_provider is not None
    assert isinstance(mundi_meta_info_provider, MundiMetaInfoProvider)


def test_mundi_obs_file_system_accessor_name():
    assert 'MundiFileSystem' == MundiObsFileSystemAccessor.name()


def test_mundi_obs_file_system_accessor_create_from_parameters():
    mundi_parameters = {'path': _MUNDI_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_TEMP_DIR}
    mundi_file_system = MundiObsFileSystemAccessor.create_from_parameters(mundi_parameters)

    assert mundi_file_system is not None
    assert isinstance(mundi_file_system, MundiObsFileSystem)


def test_mundi_obs_file_system_name():
    assert 'MundiFileSystem' == MundiObsFileSystem.name()

    mundi_parameters = {'path': _MUNDI_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_TEMP_DIR}
    mundi_file_system = MundiObsFileSystemAccessor.create_from_parameters(mundi_parameters)
    assert 'MundiFileSystem' == mundi_file_system.name()


@pytest.mark.skip(reason='Test actually performs downloading and needs authorization')
def test_mundi_obs_file_system_get():
    try:
        mundi_parameters = {'path': _MUNDI_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_TEMP_DIR}
        mundi_parameters['access_key_id'] = ''  # enter access key id here
        mundi_parameters['secret_access_key'] = ''  # enter secret access key here
        mundi_file_system = MundiObsFileSystemAccessor.create_from_parameters(mundi_parameters)
        data_set_meta_info = DataSetMetaInfo(
            coverage='POLYGON ((10.3882277619999996 54.1384156120000029, 10.3173421249999997 54.0163176499999977,'
                     '10.2348201129999996 53.8730417960000025, 10.1528176469999991 53.7297406859999995, '
                     '10.0714324099999999 53.5864079979999985, 9.9905949619999994 53.4430542019999990, '
                     '9.9101521629999993 53.2996597570000006, 9.8301509550000006 53.1562272170000014, '
                     '9.8297230889999998 53.1554540790000019, 8.9997008679999997 53.1611735449999969, '
                     '8.9996937989999992 54.1481041039999980, 10.3882277619999996 54.1384156120000029))',
            start_time='2018-06-02T10:40:19Z', end_time='2018-06-02T10:40:19Z', data_type='S2_L1C',
            identifier='S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118')
        file_refs = mundi_file_system.get(data_set_meta_info)
        assert 1 == len(file_refs)
        assert '{}/S2_L1C/2018/06/02/S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118'.format(_MUNDI_DIR) == \
               file_refs[0].url
        assert '2018-06-02T10:40:19Z' == file_refs[0].start_time
        assert '2018-06-02T10:40:19Z' == file_refs[0].end_time
        assert 'application/x-directory' == file_refs[0].mime_type
    finally:
        if os.path.exists(_MUNDI_TEMP_DIR):
            shutil.rmtree(_MUNDI_TEMP_DIR)
        if os.path.exists(_MUNDI_DIR):
            shutil.rmtree(_MUNDI_DIR)


def test_mundi_obs_file_system_get_wrapped_parameters_as_dict():
    mundi_parameters = {'path': _MUNDI_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_TEMP_DIR}
    mundi_file_system = MundiObsFileSystemAccessor.create_from_parameters(mundi_parameters)

    mundi_file_system_as_dict = mundi_file_system._get_wrapped_parameters_as_dict()
    assert mundi_file_system_as_dict is not None
    assert dict == type(mundi_file_system_as_dict)
    assert 3 == len(mundi_file_system_as_dict.keys())
    assert 'access_key_id' in mundi_file_system_as_dict
    assert '' == mundi_file_system_as_dict['access_key_id']
    assert 'secret_access_key' in mundi_file_system_as_dict
    assert '' == mundi_file_system_as_dict['secret_access_key']
    assert 'temp_dir' in mundi_file_system_as_dict
    assert _MUNDI_TEMP_DIR == mundi_file_system_as_dict['temp_dir']


def test_mundi_obs_file_system_get_bucket():
    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-06-01', end_time='2018-06-01', data_type='S2_L1C',
                                         identifier='S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118')
    bucket_names = MundiObsFileSystem._get_bucket_names(data_set_meta_info)
    assert 's2-l1c' in bucket_names
    assert 's2-l1c-2018' in bucket_names
    assert 's2-l1c-2018-q2' in bucket_names

    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-10-02', end_time='2018-10-02', data_type='S1_SLC',
                                         identifier='S1A_IW_SLC__1SDV_20181002T012023_20181002T012053_023950_029D89_4DB1')
    bucket_names = MundiObsFileSystem._get_bucket_names(data_set_meta_info)
    assert 's1-l1-slc' == bucket_names[0]
    assert 's1-l1-slc-2018' == bucket_names[1]
    assert 's1-l1-slc-2018-q4' == bucket_names[2]

    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-01-05', end_time='2018-01-05', data_type='S3_L1_OLCI_FR',
                                         identifier='S3A_OL_2_LFR____20180105T104935_20180105T105235_20180106T153005_0180_026_222_3239_LN1_O_NT_002')
    bucket_names = MundiObsFileSystem._get_bucket_names(data_set_meta_info)
    assert 's3-olci' == bucket_names[0]


def test_mundi_obs_file_system_get_prefix():
    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-06-02', end_time='2018-06-02', data_type='S2_L1C',
                                         identifier='S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118')
    prefix = MundiObsFileSystem._get_prefix(data_set_meta_info)
    assert '32/U/NE/2018/06/02/' == prefix

    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-10-02', end_time='2018-10-02', data_type='S1_SLC',
                                         identifier='S1A_IW_SLC__1SDV_20181002T012023_20181002T012053_023950_029D89_4DB1')
    prefix = MundiObsFileSystem._get_prefix(data_set_meta_info)
    assert '2018/10/02/IW/DV/' == prefix

    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-01-05', end_time='2018-01-05', data_type='S3_L1_OLCI_FR',
                                         identifier='S3A_OL_2_LFR____20180105T104935_20180105T105235_20180106T153005_0180_026_222_3239_LN1_O_NT_002')
    prefix = MundiObsFileSystem._get_prefix(data_set_meta_info)
    assert 'LFR/2018/01/05/' == prefix


def test_mundi_rest_file_system_accessor_name():
    assert 'MundiRestFileSystem' == MundiRestFileSystemAccessor.name()


def test_mundi_rest_file_system_accessor_create_from_parameters():
    mundi_parameters = {'path': _MUNDI_REST_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_REST_TEMP_DIR}
    mundi_file_system = MundiRestFileSystemAccessor.create_from_parameters(mundi_parameters)

    assert mundi_file_system is not None
    assert isinstance(mundi_file_system, MundiRestFileSystem)


def test_mundi_rest_file_system_name():
    assert 'MundiRestFileSystem' == MundiRestFileSystem.name()

    mundi_parameters = {'path': _MUNDI_REST_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_REST_TEMP_DIR}
    mundi_file_system = MundiRestFileSystemAccessor.create_from_parameters(mundi_parameters)
    assert 'MundiRestFileSystem' == mundi_file_system.name()


@pytest.mark.skip(reason='Test actually performs downloading')
def test_mundi_rest_file_system_get_s1():
    try:
        mundi_parameters = {'path': _MUNDI_REST_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_REST_TEMP_DIR}
        mundi_file_system = MundiRestFileSystemAccessor.create_from_parameters(mundi_parameters)
        data_set_meta_info = DataSetMetaInfo(coverage='POLYGON ((9.1527709999999995 54.2447889999999973, '
                                                      '13.1172269999999997 54.6578639999999965, '
                                                      '13.5328199999999992 53.0389899999999983, '
                                                      '9.7198080000000004 52.6297950000000014, '
                                                      '9.1527709999999995 54.2447889999999973))',
                                             start_time='2018-06-01T17:00:37Z', end_time='2018-06-01T17:00:37Z',
                                             data_type='S1_SLC',
                                             identifier='S1A_IW_SLC__1SDV_20180601T170037_20180601T170104_022166_0265B3_466C')
        file_refs = mundi_file_system.get(data_set_meta_info)
        assert 1 == len(file_refs)
        assert '{}/S1_SLC/2018/06/01/S1A_IW_SLC__1SDV_20180601T170037_20180601T170104_022166_0265B3_466C'.format(
            _MUNDI_REST_DIR) == file_refs[0].url
        assert '2018-06-01T17:00:37Z' == file_refs[0].start_time
        assert '2018-06-01T17:00:37Z' == file_refs[0].end_time
        assert 'application/zip' == file_refs[0].mime_type
    finally:
        if os.path.exists(_MUNDI_REST_TEMP_DIR):
            shutil.rmtree(_MUNDI_REST_TEMP_DIR)
        if os.path.exists(_MUNDI_REST_DIR):
            shutil.rmtree(_MUNDI_REST_DIR)


@pytest.mark.skip(reason='Test actually performs downloading')
def test_mundi_rest_file_system_get_s2():
    try:
        mundi_parameters = {'path': _MUNDI_REST_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_REST_TEMP_DIR}
        mundi_file_system = MundiRestFileSystemAccessor.create_from_parameters(mundi_parameters)
        # data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
        #                                      start_time='2018-09-26', end_time='2018-09-26', data_type='S2_L1C',
        #                                      identifier='S2B_MSIL1C_20180926T200619_N0206_R099_T01CDQ_20180926T231404')
        data_set_meta_info = DataSetMetaInfo(
            coverage='POLYGON ((10.3882277619999996 54.1384156120000029, 10.3173421249999997 54.0163176499999977,'
                     '10.2348201129999996 53.8730417960000025, 10.1528176469999991 53.7297406859999995, '
                     '10.0714324099999999 53.5864079979999985, 9.9905949619999994 53.4430542019999990, '
                     '9.9101521629999993 53.2996597570000006, 9.8301509550000006 53.1562272170000014, '
                     '9.8297230889999998 53.1554540790000019, 8.9997008679999997 53.1611735449999969, '
                     '8.9996937989999992 54.1481041039999980, 10.3882277619999996 54.1384156120000029))',
            start_time='2018-06-02T10:40:19Z', end_time='2018-06-02T10:40:19Z', data_type='S2_L1C',
            identifier='S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118')
        file_refs = mundi_file_system.get(data_set_meta_info)
        assert 1 == len(file_refs)
        assert '{}/S2_L1C/2018/09/26/S2B_MSIL1C_20180926T200619_N0206_R099_T01CDQ_20180926T231404'.format(
            _MUNDI_REST_DIR) == file_refs[0].url
        assert '2018-09-26' == file_refs[0].start_time
        assert '2018-09-26' == file_refs[0].end_time
        assert 'application/x-directory' == file_refs[0].mime_type
    finally:
        if os.path.exists(_MUNDI_REST_TEMP_DIR):
            shutil.rmtree(_MUNDI_REST_TEMP_DIR)
        if os.path.exists(_MUNDI_REST_DIR):
            shutil.rmtree(_MUNDI_REST_DIR)


def test_mundi_rest_file_system_get_wrapped_parameters_as_dict():
    mundi_parameters = {'path': _MUNDI_REST_DIR, 'pattern': '/dt/yy/mm/dd/', 'temp_dir': _MUNDI_REST_TEMP_DIR}
    mundi_file_system = MundiRestFileSystemAccessor.create_from_parameters(mundi_parameters)

    mundi_file_system_as_dict = mundi_file_system._get_wrapped_parameters_as_dict()
    assert mundi_file_system_as_dict is not None
    assert dict == type(mundi_file_system_as_dict)
    assert 1 == len(mundi_file_system_as_dict.keys())
    assert 'temp_dir' in mundi_file_system_as_dict
    assert _MUNDI_REST_TEMP_DIR == mundi_file_system_as_dict['temp_dir']


def test_mundi_rest_file_system_get_bucket():
    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-06-01', end_time='2018-06-01', data_type='S2_L1C',
                                         identifier='S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118')
    bucket_names = MundiRestFileSystem._get_bucket_names(data_set_meta_info)
    assert 's2-l1c' in bucket_names
    assert 's2-l1c-2018' in bucket_names
    assert 's2-l1c-2018-q2' in bucket_names

    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-10-02', end_time='2018-10-02', data_type='S1_SLC',
                                         identifier='S1A_IW_SLC__1SDV_20181002T012023_20181002T012053_023950_029D89_4DB1')
    bucket_names = MundiRestFileSystem._get_bucket_names(data_set_meta_info)
    assert 's1-l1-slc' == bucket_names[0]
    assert 's1-l1-slc-2018' == bucket_names[1]
    assert 's1-l1-slc-2018-q4' == bucket_names[2]

    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-01-05', end_time='2018-01-05', data_type='S3_L1_OLCI_FR',
                                         identifier='S3A_OL_2_LFR____20180105T104935_20180105T105235_20180106T153005_0180_026_222_3239_LN1_O_NT_002')
    bucket_names = MundiRestFileSystem._get_bucket_names(data_set_meta_info)
    assert 's3-olci' == bucket_names[0]


def test_mundi_rest_file_system_get_prefix():
    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-06-02', end_time='2018-06-02', data_type='S2_L1C',
                                         identifier='S2B_MSIL1C_20180602T104019_N0206_R008_T32UNE_20180602T132118')
    prefix = MundiRestFileSystem._get_prefix(data_set_meta_info)
    assert '32/U/NE/2018/06/02/' == prefix

    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-10-02', end_time='2018-10-02', data_type='S1_SLC',
                                         identifier='S1A_IW_SLC__1SDV_20181002T012023_20181002T012053_023950_029D89_4DB1')
    prefix = MundiRestFileSystem._get_prefix(data_set_meta_info)
    assert '2018/10/02/IW/DV/' == prefix

    data_set_meta_info = DataSetMetaInfo(coverage='POLYGON((9.8 53.6,10.2 53.6,10.2 53.4,9.8 53.4,9.8 53.6))',
                                         start_time='2018-01-05', end_time='2018-01-05', data_type='S3_L1_OLCI_FR',
                                         identifier='S3A_OL_2_LFR____20180105T104935_20180105T105235_20180106T153005_0180_026_222_3239_LN1_O_NT_002')
    prefix = MundiRestFileSystem._get_prefix(data_set_meta_info)
    assert 'LFR/2018/01/05/' == prefix
