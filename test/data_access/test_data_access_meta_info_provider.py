from multiply_data_access import MetaInfoProvider
from shapely.wkt import loads

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"


def test_meta_info_provider_get_roi_from_query_string():
    query_string = 'POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10));;;;EPSG:4326'
    roi = MetaInfoProvider.get_roi_from_query_string(query_string)
    assert roi.geom_type == 'Polygon'

    try:
        MetaInfoProvider.get_roi_from_query_string('POINT (0 0);;;;EPSG:4326')
    except ValueError:
        assert True


def test_meta_info_provider_get_roi_from_query_string_other_srs():
    query_string = 'POLYGON((685700. 6462200., 685700. 6470700., 697660. 6470700., 697660. 6462200., 685700. 6462200.))' \
                   ';;;;EPSG:3301'
    roi = MetaInfoProvider.get_roi_from_query_string(query_string)
    assert roi.geom_type == 'Polygon'
    expected_roi = loads('POLYGON ((27.1647563115467534 58.2611263320005577, 27.1716005869326196 58.3373581174386473, '
                         '27.3755330955532621 58.3321196269764286, 27.3682501734918766 58.2558991181697223, '
                         '27.1647563115467534 58.2611263320005577))')
    assert roi.almost_equals(expected_roi)


def test_meta_info_provider_get_start_time_from_string():
    query_string = ';2017;;'
    start_time = MetaInfoProvider.get_start_time_from_query_string(query_string)
    assert start_time.year == 2017
    assert start_time.month == 1
    assert start_time.day == 1
    assert start_time.hour == 0
    assert start_time.minute == 0
    assert start_time.second == 0

    query_string = ';2017-02;;'
    start_time = MetaInfoProvider.get_start_time_from_query_string(query_string)
    assert start_time.year == 2017
    assert start_time.month == 2
    assert start_time.day == 1
    assert start_time.hour == 0
    assert start_time.minute == 0
    assert start_time.second == 0

    query_string = ';2017-11;;'
    start_time = MetaInfoProvider.get_start_time_from_query_string(query_string)
    assert start_time.year == 2017
    assert start_time.month == 11
    assert start_time.day == 1
    assert start_time.hour == 0
    assert start_time.minute == 0
    assert start_time.second == 0

    query_string = ';2017-06-02;;'
    start_time = MetaInfoProvider.get_start_time_from_query_string(query_string)
    assert start_time.year == 2017
    assert start_time.month == 6
    assert start_time.day == 2
    assert start_time.hour == 0
    assert start_time.minute == 0
    assert start_time.second == 0

    query_string = ';2017-06-27;;'
    start_time = MetaInfoProvider.get_start_time_from_query_string(query_string)
    assert start_time.year == 2017
    assert start_time.month == 6
    assert start_time.day == 27
    assert start_time.hour == 0
    assert start_time.minute == 0
    assert start_time.second == 0

    query_string = ';2017-06-27 13:27:12;;'
    start_time = MetaInfoProvider.get_start_time_from_query_string(query_string)
    assert start_time.year == 2017
    assert start_time.month == 6
    assert start_time.day == 27
    assert start_time.hour == 13
    assert start_time.minute == 27
    assert start_time.second == 12

    query_string = ';2017-06-27T13:27:12;;'
    start_time = MetaInfoProvider.get_start_time_from_query_string(query_string)
    assert start_time.year == 2017
    assert start_time.month == 6
    assert start_time.day == 27
    assert start_time.hour == 13
    assert start_time.minute == 27
    assert start_time.second == 12


def test_meta_info_provider_get_end_time_from_string():
    query_string = ';;2017;'
    end_time = MetaInfoProvider.get_end_time_from_query_string(query_string)
    assert end_time.year == 2017
    assert end_time.month == 12
    assert end_time.day == 31
    assert end_time.hour == 23
    assert end_time.minute == 59
    assert end_time.second == 59
    
    query_string = ';;2017-02;'
    end_time = MetaInfoProvider.get_end_time_from_query_string(query_string)
    assert end_time.year == 2017
    assert end_time.month == 2
    assert end_time.day == 28
    assert end_time.hour == 23
    assert end_time.minute == 59
    assert end_time.second == 59
    
    query_string = ';;2017-11;'
    end_time = MetaInfoProvider.get_end_time_from_query_string(query_string)
    assert end_time.year == 2017
    assert end_time.month == 11
    assert end_time.day == 30
    assert end_time.hour == 23
    assert end_time.minute == 59
    assert end_time.second == 59
    
    query_string = ';;2017-06-02;'
    end_time = MetaInfoProvider.get_end_time_from_query_string(query_string)
    assert end_time.year == 2017
    assert end_time.month == 6
    assert end_time.day == 2
    assert end_time.hour == 23
    assert end_time.minute == 59
    assert end_time.second == 59
    
    query_string = ';;2017-06-27;'
    end_time = MetaInfoProvider.get_end_time_from_query_string(query_string)
    assert end_time.year == 2017
    assert end_time.month == 6
    assert end_time.day == 27
    assert end_time.hour == 23
    assert end_time.minute == 59
    assert end_time.second == 59
    
    query_string = ';;2017-06-27 13:27:12;'
    end_time = MetaInfoProvider.get_end_time_from_query_string(query_string)
    assert end_time.year == 2017
    assert end_time.month == 6
    assert end_time.day == 27
    assert end_time.hour == 13
    assert end_time.minute == 27
    assert end_time.second == 12
    
    query_string = ';;2017-06-27T13:27:12;'
    end_time = MetaInfoProvider.get_end_time_from_query_string(query_string)
    assert end_time.year == 2017
    assert end_time.month == 6
    assert end_time.day == 27
    assert end_time.hour == 13
    assert end_time.minute == 27
    assert end_time.second == 12


def test_meta_info_provider_get_data_types():
    query_string = ';;;SLSTR L1B, Era-Interim, S2A MSI'
    data_types = MetaInfoProvider.get_data_types_from_query_string(query_string)
    assert len(data_types) == 3
    # assert data_types, ['SLSTR L1B', 'Era-Interim', 'S2A MSI']
    assert all([a == b for a, b in zip(data_types, ['SLSTR L1B', 'Era-Interim', 'S2A MSI'])])

    query_string = ';;;'
    data_types = MetaInfoProvider.get_data_types_from_query_string(query_string)
    assert len(data_types) == 0
