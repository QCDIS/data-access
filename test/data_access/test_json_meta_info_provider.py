from multiply_data_access import DataSetMetaInfo, JsonMetaInfoProvider
import os
import shutil

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"

path_to_json_file = './test/test_data/test_meta_info.json'


def test_get_name():
    provider = JsonMetaInfoProvider(path_to_json_file, None)

    assert 'JsonMetaInfoProvider' == provider.name()
    assert 'JsonMetaInfoProvider' == JsonMetaInfoProvider.name()


def test_json_meta_info_provider_query_for_region():
    provider = JsonMetaInfoProvider(path_to_json_file, None)
    query_string = "POLYGON((5 5, 20 5, 20 20, 5 20, 5 5));2017-03-01;2017-03-31;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 2
    ensure_first_data_set(meta_data_infos[0])
    ensure_second_data_set(meta_data_infos[1])

    query_string = "POLYGON((5 20, 35 20, 35 40, 5 40, 5 20));2017-03-01;2017-03-31;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 3
    ensure_second_data_set(meta_data_infos[0])
    ensure_third_data_set(meta_data_infos[1])
    ensure_fourth_data_set(meta_data_infos[2])

    query_string = "POLYGON((35 0, 45 0, 45 10, 35 10, 35 0));2017-03-01;2017-03-31;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 0


def test_json_meta_info_provider_query_for_times():
    provider = JsonMetaInfoProvider(path_to_json_file, None)
    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-24;2017-03-26;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 2
    ensure_first_data_set(meta_data_infos[0])
    ensure_fourth_data_set(meta_data_infos[1])

    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-19;2017-03-20;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 3
    ensure_second_data_set(meta_data_infos[0])
    ensure_third_data_set(meta_data_infos[1])
    ensure_fourth_data_set(meta_data_infos[2])

    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-10;2017-03-10;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 1
    ensure_fourth_data_set(meta_data_infos[0])

    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03;2017-03;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 4
    ensure_first_data_set(meta_data_infos[0])
    ensure_second_data_set(meta_data_infos[1])
    ensure_third_data_set(meta_data_infos[2])
    ensure_fourth_data_set(meta_data_infos[3])

    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2016-03;2016-03;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 0


def test_json_meta_info_provider_query_for_data_type():
    provider = JsonMetaInfoProvider(path_to_json_file, None)
    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03;2017-03;TYPE_A, TYPE_C"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 3
    ensure_first_data_set(meta_data_infos[0])
    ensure_second_data_set(meta_data_infos[1])
    ensure_fourth_data_set(meta_data_infos[2])

    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03;2017-03;TYPE_B"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 1
    ensure_third_data_set(meta_data_infos[0])

    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03;2017-03;"
    meta_data_infos = provider.query(query_string)
    assert len(meta_data_infos) == 0


def test_json_meta_info_provider_query_local():
    provider = JsonMetaInfoProvider(path_to_json_file, None)
    query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03;2017-03;TYPE_A, TYPE_C"
    meta_data_infos = provider.query_local(query_string)
    assert len(meta_data_infos) == 3
    ensure_first_data_set(meta_data_infos[0])
    ensure_second_data_set(meta_data_infos[1])
    ensure_fourth_data_set(meta_data_infos[2])


def test_json_meta_info_provider_query_non_local():
    provider = JsonMetaInfoProvider(path_to_json_file, None)
    query_string = "POLYGON((0 0, 90 0, 90 90, 0 90, 0 0));2017-01;2019-01;TYPE_A, TYPE_B, TYPE_C"
    meta_data_infos = provider.query_non_local(query_string)
    assert len(meta_data_infos) == 0


def test_get_parameters_as_dict():
    provider = JsonMetaInfoProvider(path_to_json_file, None)

    meta_info_providers_dict = provider._get_parameters_as_dict()

    assert 2 == len(meta_info_providers_dict.keys())
    assert 'path_to_json_file' in meta_info_providers_dict.keys()
    assert path_to_json_file == meta_info_providers_dict['path_to_json_file']
    assert 'supported_data_types' in meta_info_providers_dict.keys()
    assert 'TYPE_A,TYPE_B,TYPE_C' == meta_info_providers_dict['supported_data_types']


def test_update():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_2'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        provider = JsonMetaInfoProvider(path_to_json_file_2, 'TYPE_A,TYPE_B,TYPE_C,TYPE_D')
        data_set_meta_info = DataSetMetaInfo(coverage="POLYGON((10 10, 20 10, 20 20, 10 20, 10 10))",
                                         start_time="2017-03-21 14:33:00",
                                         end_time="2017-03-21 14:45:00",
                                         data_type="TYPE_D",
                                         identifier="ctfgb")
        provider.update(data_set_meta_info)

        # use a second provider to ensure the update is saved
        provider_2 = JsonMetaInfoProvider(path_to_json_file_2, None)

        query_result = provider_2.query(";2017-03-21;2017-03-21;TYPE_D")
        assert 1 == len(query_result)
        assert "POLYGON((10 10, 20 10, 20 20, 10 20, 10 10))" == query_result[0].coverage
        assert "2017-03-21 14:33:00" == query_result[0].start_time
        assert "2017-03-21 14:45:00" == query_result[0].end_time
        assert "TYPE_D" == query_result[0].data_type
        assert "ctfgb" == query_result[0].identifier
    finally:
        os.remove(path_to_json_file_2)


def test_remove():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_3'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        provider = JsonMetaInfoProvider(path_to_json_file_2, None)
        query_string = "POLYGON((5 5, 35 5, 35 35, 5 35, 5 5));2017-03-10;2017-03-10;TYPE_A, TYPE_B, TYPE_C"
        meta_data_infos = provider.query(query_string)
        assert 1 == len(meta_data_infos)
        ensure_fourth_data_set(meta_data_infos[0])
        provider.remove(meta_data_infos[0])

        # use a second provider to ensure the update is saved
        provider_2 = JsonMetaInfoProvider(path_to_json_file_2, None)
        meta_data_infos_2 = provider_2.query(query_string)

        assert 0 == len(meta_data_infos_2)
    finally:
        os.remove(path_to_json_file_2)


def test_provides_data_type():
    # copy this so we don't mess up the original file
    path_to_json_file_2 = path_to_json_file + '_4'
    shutil.copyfile(path_to_json_file, path_to_json_file_2)
    try:
        provider = JsonMetaInfoProvider(path_to_json_file_2, 'TYPE_A,TYPE_B,TYPE_C')
        assert True == provider.provides_data_type("TYPE_A")
        assert True == provider.provides_data_type("TYPE_B")
        assert True == provider.provides_data_type("TYPE_C")
        assert False == provider.provides_data_type("TYPE_D")
        assert False == provider.provides_data_type("ctfsvbzrt")
    finally:
        os.remove(path_to_json_file_2)


def ensure_first_data_set(data_set:DataSetMetaInfo):
    assert data_set.coverage == 'POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))'
    assert data_set.start_time == '2017-03-25 12:30:00'
    assert data_set.end_time == '2017-03-25 12:40:00'
    assert data_set.data_type == 'TYPE_A'
    assert data_set.identifier == 'dvgbvjn'


def ensure_second_data_set(data_set:DataSetMetaInfo):
    assert data_set.coverage == 'POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))'
    assert data_set.start_time == '2017-03-20 14:30:00'
    assert data_set.end_time == '2017-03-20 14:40:00'
    assert data_set.data_type == 'TYPE_A'
    assert data_set.identifier == 'nkhmjzh'


def ensure_third_data_set(data_set:DataSetMetaInfo):
    assert data_set.coverage == 'POLYGON((35 35, 45 35, 45 35, 35 45, 35 35))'
    assert data_set.start_time == '2017-03-20'
    assert data_set.end_time == '2017-03-20'
    assert data_set.data_type == 'TYPE_B'
    assert data_set.identifier == 'rtwgtnj'


def ensure_fourth_data_set(data_set:DataSetMetaInfo):
    assert data_set.coverage == 'POLYGON((0 35, 10 35, 10 35, 0 45, 0 35))'
    assert data_set.start_time == '2017-03'
    assert data_set.end_time == '2017-03'
    assert data_set.data_type == 'TYPE_C'
    assert data_set.identifier == 'vgfbhngf'
