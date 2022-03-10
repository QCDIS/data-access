from multiply_core.observations import data_validation
from multiply_data_access import DataSetMetaInfo, LocalFileSystem, add_data_set_meta_info_extractor, \
    DataSetMetaInfoExtractor
from datetime import datetime
from shapely.geometry import Polygon
import os
import shutil

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"


def test_get_name():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    assert 'LocalFilesystem', local_file_system.name()
    assert 'LocalFilesystem', LocalFileSystem.name()


def test_get_one_file():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2017-08-21', '2017-08-21', 'my_data_type', '')
    file_refs = local_file_system.get(data_set_meta_info)
    assert 1, len(file_refs)
    assert 'small_product.nc', file_refs[0].url
    assert '2017-08-21', file_refs[0].start_time
    assert '2017-08-21', file_refs[0].end_time
    assert 'application/x-netcdf', file_refs[0].mime_type


def test_get_two_files():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2017-08-21', '2017-08-25', 'my_data_type', '')
    file_refs = local_file_system.get(data_set_meta_info)
    assert 2, len(file_refs)
    assert 'small_product.nc', file_refs[0].url
    assert '2017-08-21', file_refs[0].start_time
    assert '2017-08-21', file_refs[0].end_time
    assert 'application/x-netcdf', file_refs[0].mime_type
    assert 'other_small_product.nc', file_refs[1].url
    assert '2017-08-25', file_refs[0].start_time
    assert '2017-08-25', file_refs[0].end_time
    assert 'application/x-netcdf', file_refs[1].mime_type


def test_get_invalid_time():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2017-07-19', '2017-07-20', 'my_data_type', '')
    file_refs = local_file_system.get(data_set_meta_info)
    assert 0 == len(file_refs)


def test_get_invalid_data_type():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2017-08-21', '2017-08-21', 'my_other_data_type', '')
    file_refs = local_file_system.get(data_set_meta_info)
    assert 0 == len(file_refs)


def test_get_invalid_identifier():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2017-08-21', '2017-08-21', 'my_data_type', ' rtfghnmchfj')
    file_refs = local_file_system.get(data_set_meta_info)
    assert 0 == len(file_refs)


def test_get_weird_pattern():
    local_file_system = LocalFileSystem('./test/test_data/', '/mm/')
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2017-06-21', '2017-06-21', 'doesn\'t matter', '')
    file_refs = local_file_system.get(data_set_meta_info)
    assert 1, len(file_refs)
    assert 'vfbzf.json', file_refs[0].url
    assert '2017-06-21', file_refs[0].start_time
    assert '2017-06-21', file_refs[0].end_time
    assert 'application/json', file_refs[0].mime_type


def test_put():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    url = open('gfhnfd.nc', 'w+').name
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2016-12-15', '2016-12-16', 'my_data_type',
                                         'doesn\'t matter')
    try:
        assert not os.path.exists('./test/test_data/my_data_type/2016/12/15/gfhnfd.nc')
        local_file_system.put(url, data_set_meta_info)
        assert os.path.exists('./test/test_data/my_data_type/2016/12/15/gfhnfd.nc')
        local_file_system.put(url, data_set_meta_info)
        assert os.path.exists('./test/test_data/my_data_type/2016/12/15/gfhnfd.nc')
    finally:
        os.remove(url)
        if os.path.exists('./test/test_data/my_data_type/2016/'):
            shutil.rmtree('./test/test_data/my_data_type/2016/')


def test_remove_one_file_in_folder():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    if not os.path.exists('./test/test_data/my_data_type/2015/12/15/'):
        os.makedirs('./test/test_data/my_data_type/2015/12/15/')
    open('./test/test_data/my_data_type/2015/12/15/gfhnfd.nc', 'w+')
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2015-12-15', '2015-12-16', 'my_data_type', '')
    try:
        local_file_system.remove(data_set_meta_info)
        assert not os.path.exists('./test/test_data/my_data_type/2015/12/15/gfhnfd.nc')
    finally:
        if os.path.exists('./test/test_data/my_data_type/2015/'):
            shutil.rmtree('./test/test_data/my_data_type/2015/')


def test_remove_two_files_in_folder():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    if not os.path.exists('./test/test_data/my_data_type/2015/12/15/'):
        os.makedirs('./test/test_data/my_data_type/2015/12/15/')
    open('./test/test_data/my_data_type/2015/12/15/gfhnfd.nc', 'w+')
    open('./test/test_data/my_data_type/2015/12/15/bcdvhftzd.nc', 'w+')
    data_set_meta_info = DataSetMetaInfo('doesn\'t matter', '2015-12-15', '2015-12-16', 'my_data_type',
                                         'gfhnfd.nc')
    try:
        local_file_system.remove(data_set_meta_info)
        assert not os.path.exists('./test/test_data/my_data_type/2015/12/15/gfhnfd.nc')
        assert os.path.exists('./test/test_data/my_data_type/2015/12/15/bcdvhftzd.nc')
    finally:
        if os.path.exists('./test/test_data/my_data_type/2015/'):
            shutil.rmtree('./test/test_data/my_data_type/2015/')


def test_scan():

    class MyValidator(data_validation.DataValidator):

        @classmethod
        def name(cls) -> str:
            return 'my_data_type'

        def is_valid(self, path: str) -> bool:
            return path.endswith('.nc')

        def get_relative_path(self, path: str) -> str:
            return ''

        def get_file_pattern(self) -> str:
            return '*.nc'

        def is_valid_for(self, path: str, roi: Polygon, start_time: datetime, end_time: datetime) -> bool:
            return self.is_valid(path)

        def differs_by_name(cls):
            return False

    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')
    data_validation.add_validator(MyValidator())

    class MyDataSetMetaInfoExtractor(DataSetMetaInfoExtractor):

        @classmethod
        def name(cls) -> str:
            return 'my_data_type'

        def extract_meta_info(self, path: str) -> DataSetMetaInfo:
            return DataSetMetaInfo('', None, None, 'my_data_type', path)

    add_data_set_meta_info_extractor(MyDataSetMetaInfoExtractor())

    retrieved_data_set_meta_infos = local_file_system.scan()

    assert 2 == len(retrieved_data_set_meta_infos)
    assert 'my_data_type' == retrieved_data_set_meta_infos[0].data_type
    assert retrieved_data_set_meta_infos[0].identifier.endswith('small_product.nc')
    assert 'my_data_type' == retrieved_data_set_meta_infos[1].data_type
    assert retrieved_data_set_meta_infos[1].identifier.endswith('other_small_product.nc')


def test_get_parameters_as_dict():
    local_file_system = LocalFileSystem('./test/test_data/', '/dt/yy/mm/dd/')

    parameters_as_dict = local_file_system.get_parameters_as_dict()

    assert 2 == len(parameters_as_dict)
    assert 'path' in parameters_as_dict.keys()
    assert './test/test_data/' == parameters_as_dict['path']
    assert 'pattern' in parameters_as_dict.keys()
    assert '/dt/yy/mm/dd/' == parameters_as_dict['pattern']
