import re

from multiply_core.observations import DataValidator, add_validator
from multiply_data_access import DataSetMetaInfo
from datetime import datetime
from shapely.geometry import Polygon

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"


def test_meta_info_provider_equals():
    data_set_meta_info = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                     start_time="2017-03-21 14:33:00",
                                     end_time="2017-03-21 14:45:00",
                                     data_type="TYPE_D",
                                     identifier="dterftge")
    other_coverage = DataSetMetaInfo(coverage="POLYGON((10 10, 20 10, 20 20, 10 20, 10 10))",
                                         start_time="2017-03-21 14:33:00",
                                         end_time="2017-03-21 14:45:00",
                                         data_type="TYPE_D",
                                         identifier="ctfgb")
    other_start_time = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                       start_time="2017-03-20 14:33:00",
                                       end_time="2017-03-21 14:45:00",
                                       data_type="TYPE_D",
                                       identifier="frgswh")
    other_end_time = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                     start_time="2017-03-21 14:33:00",
                                     end_time="2017-03-22 14:45:00",
                                     data_type="TYPE_D",
                                     identifier="dtfsgtr")
    other_data_type = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                      start_time="2017-03-21 14:33:00",
                                      end_time="2017-03-21 14:45:00",
                                      data_type="TYPE_A",
                                      identifier="drtwr")
    equal_except_for_id = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                          start_time="2017-03-21 14:33:00",
                                          end_time="2017-03-21 14:45:00",
                                          data_type="TYPE_D",
                                          identifier="tfgtzz")
    assert not data_set_meta_info.equals(other_coverage)
    assert not data_set_meta_info.equals(other_start_time)
    assert not data_set_meta_info.equals(other_end_time)
    assert not data_set_meta_info.equals(other_data_type)
    assert data_set_meta_info.equals(equal_except_for_id)


def test_meta_info_provider_equals_except_data_type():
    data_set_meta_info = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                     start_time="2017-03-21 14:33:00",
                                     end_time="2017-03-21 14:45:00",
                                     data_type="TYPE_D",
                                     identifier="dterftge")
    other_coverage = DataSetMetaInfo(coverage="POLYGON((10 10, 20 10, 20 20, 10 20, 10 10))",
                                         start_time="2017-03-21 14:33:00",
                                         end_time="2017-03-21 14:45:00",
                                         data_type="TYPE_D",
                                         identifier="ctfgb")
    other_start_time = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                       start_time="2017-03-20 14:33:00",
                                       end_time="2017-03-21 14:45:00",
                                       data_type="TYPE_D",
                                       identifier="frgswh")
    other_end_time = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                     start_time="2017-03-21 14:33:00",
                                     end_time="2017-03-22 14:45:00",
                                     data_type="TYPE_D",
                                     identifier="dtfsgtr")
    other_data_type = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                      start_time="2017-03-21 14:33:00",
                                      end_time="2017-03-21 14:45:00",
                                      data_type="TYPE_A",
                                      identifier="drtwr")
    equal_except_for_id = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                          start_time="2017-03-21 14:33:00",
                                          end_time="2017-03-21 14:45:00",
                                          data_type="TYPE_D",
                                          identifier="tfgtzz")
    assert not data_set_meta_info.equals_except_data_type(other_coverage)
    assert not data_set_meta_info.equals_except_data_type(other_start_time)
    assert not data_set_meta_info.equals_except_data_type(other_end_time)
    assert data_set_meta_info.equals_except_data_type(other_data_type)
    assert data_set_meta_info.equals_except_data_type(equal_except_for_id)


class TypeDValidator(DataValidator):

    @classmethod
    def name(cls) -> str:
        return 'TYPE_D'

    def get_relative_path(self, path: str) -> str:
        return ''

    def is_valid(self, path: str) -> bool:
        return path.endswith('some_wrapped_file')

    def get_file_pattern(self) -> str:
        return ''

    def is_valid_for(self, path: str, roi: Polygon, start_time: datetime, end_time: datetime) -> bool:
        return self.is_valid(path)

    @classmethod
    def differs_by_name(cls):
        return True


def test_meta_info_provider_equals_considers_different_name():
    add_validator(TypeDValidator())
    data_set_meta_info = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                     start_time="2017-03-21 14:33:00",
                                     end_time="2017-03-21 14:45:00",
                                     data_type="TYPE_D",
                                     identifier="/some/path/dterftge")
    equal_except_for_id = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                          start_time="2017-03-21 14:33:00",
                                          end_time="2017-03-21 14:45:00",
                                          data_type="TYPE_D",
                                          identifier="/some/other/path/dterftge")
    assert data_set_meta_info.equals(equal_except_for_id)


class TypeEValidator(DataValidator):

    def __init__(self):
        self.BASIC_AWS_S2_PATTERN = '/[0-9]{1,2}/[A-Z]/[A-Z]{2}/20[0-9][0-9]/[0-9]{1,2}/[0-9]{1,2}/[0-9]{1,2}'
        self.BASIC_AWS_S2_MATCHER = re.compile(self.BASIC_AWS_S2_PATTERN)

    @classmethod
    def name(cls) -> str:
        return 'TYPE_E'

    def get_relative_path(self, path: str) -> str:
        dirs_names = self.BASIC_AWS_S2_MATCHER.search(path)
        if dirs_names is None:
            return ''
        start_pos, end_pos = dirs_names.regs[0]
        return path[start_pos + 1:end_pos]

    def is_valid(self, path: str) -> bool:
        return path.endswith('some_wrapped_file')

    def get_file_pattern(self) -> str:
        return ''

    def is_valid_for(self, path: str, roi: Polygon, start_time: datetime, end_time: datetime) -> bool:
        return self.is_valid(path)

    @staticmethod
    def differs_by_name():
        return True


def test_meta_info_provider_equals_considers_different_name_with_realtive_path():
    add_validator(TypeEValidator())
    data_set_meta_info = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                     start_time="2017-03-21 14:33:00",
                                     end_time="2017-03-21 14:45:00",
                                     data_type="TYPE_E",
                                     identifier="/some/path/29/S/QB/2017/9/4/0")
    same_relative_path = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                          start_time="2017-03-21 14:33:00",
                                          end_time="2017-03-21 14:45:00",
                                          data_type="TYPE_E",
                                          identifier="/some/other/path/29/S/QB/2017/9/4/0")
    other_relative_path = DataSetMetaInfo(coverage="POLYGON((15 15, 25 15, 25 25, 15 25, 15 15))",
                                          start_time="2017-03-21 14:33:00",
                                          end_time="2017-03-21 14:45:00",
                                          data_type="TYPE_E",
                                          identifier="/some/other/path/29/S/QB/2016/9/4/0")
    assert data_set_meta_info.equals(same_relative_path)
    assert not data_set_meta_info.equals(other_relative_path)
