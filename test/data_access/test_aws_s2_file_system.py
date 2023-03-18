__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

import os
import pytest
import shutil
from multiply_core.observations import DataTypeConstants
from multiply_data_access.aws_s2_file_system import AwsS2FileSystem, AwsS2FileSystemAccessor
from multiply_data_access.data_access import DataSetMetaInfo

import urllib.request
import zipfile

test_data_save_path = '/tmp/data-access-test_data.zip'
if not os.path.exists(test_data_save_path):
    urllib.request.urlretrieve('https://github.com/QCDIS/multiply-core/raw/master/test/test_data.zip', test_data_save_path)
    with zipfile.ZipFile(test_data_save_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp')
    zip_ref.close()
base_path = '/tmp/test_data/'


OUTPUT_DIR = './test/test_data/aws_s2_download_dir/'


def test_aws_s2_file_system_accessor_get_name():
    assert 'AwsS2FileSystem' == AwsS2FileSystemAccessor.name()


def test_aws_s2_file_system_accessor_create_from_parameters():
    parameters = {'temp_dir': OUTPUT_DIR, 'path': './test/test_data/aws_s2_data/', 'pattern': ''}
    aws_s2_file_system = AwsS2FileSystemAccessor.create_from_parameters(parameters)
    assert type(aws_s2_file_system) == AwsS2FileSystem
    with pytest.raises(ValueError):
        assert AwsS2FileSystemAccessor.create_from_parameters({})


def test_aws_s2_file_system_get_name():
    parameters = {'temp_dir': OUTPUT_DIR, 'path': './test/test_data/aws_s2_data/', 'pattern': ''}
    aws_s2_file_system = AwsS2FileSystemAccessor.create_from_parameters(parameters)
    assert 'AwsS2FileSystem' == aws_s2_file_system.name()
    assert 'AwsS2FileSystem' == AwsS2FileSystem.name()


def test_aws_s2_file_system_get_tile_name():
    parameters = {'temp_dir': OUTPUT_DIR, 'path': './test/test_data/aws_s2_data/', 'pattern': ''}
    aws_s2_file_system = AwsS2FileSystemAccessor.create_from_parameters(parameters)
    assert '30SWJ' == aws_s2_file_system._get_tile_name('30/S/WJ/2016/4/24/0')


def test_aws_s2_file_system_get_aws_index():
    parameters = {'temp_dir': OUTPUT_DIR, 'path': './test/test_data/aws_s2_data/', 'pattern': ''}
    aws_s2_file_system = AwsS2FileSystemAccessor.create_from_parameters(parameters)
    assert 0 == aws_s2_file_system._get_aws_index('30/S/WJ/2016/4/24/0')
    assert 25 == aws_s2_file_system._get_aws_index('30/S/WJ/2016/4/24/25')


def test_aws_s2_file_system_get_parameters_as_dict():
    parameters = {'temp_dir': OUTPUT_DIR, 'path': './test/test_data/aws_s2_data/', 'pattern': ''}
    aws_s2_file_system = AwsS2FileSystemAccessor.create_from_parameters(parameters)
    parameters_as_dict = aws_s2_file_system.get_parameters_as_dict()
    assert 3 == len(parameters_as_dict.keys())
    assert 'temp_dir' in parameters_as_dict.keys()
    assert OUTPUT_DIR == parameters_as_dict['temp_dir']
    assert 'path' in parameters_as_dict.keys()
    assert './test/test_data/aws_s2_data/' == parameters_as_dict['path']
    assert 'pattern' in parameters_as_dict.keys()
    assert '' == parameters_as_dict['pattern']


def test_aws_s2_file_system_is_valid_identifier():
    parameters = {'temp_dir': OUTPUT_DIR, 'path': './test/test_data/aws_s2_data/', 'pattern': ''}
    aws_s2_file_system = AwsS2FileSystemAccessor.create_from_parameters(parameters)
    assert aws_s2_file_system._is_valid_identifier('30/S/WJ/2016/4/1/0')
    assert not aws_s2_file_system._is_valid_identifier('dvghg')


@pytest.mark.skip(reason='Test actually performs downloading and needs authorization')
def test_aws_s2_file_system_get_file_ref():
    try:
        parameters = {'temp_dir': OUTPUT_DIR, 'path': './test/test_data/aws_s2_data/', 'pattern': ''}
        aws_s2_file_system = AwsS2FileSystemAccessor.create_from_parameters(parameters)
        data_set_meta_info = DataSetMetaInfo('doesnt matter here', '2016-04-01', '2016-04-01',
                                             DataTypeConstants.AWS_S2_L1C,
                                             '30/S/WJ/2016/4/1/0')
        metafiles = ['metadata', 'tileInfo']
        file_ref = aws_s2_file_system._get_file_ref(data_set_meta_info, bands=[], metafiles=metafiles)
        assert '{}/30SWJ,2016-04-01,0/30/S/WJ/2016/4/1/0/'.format(OUTPUT_DIR) == file_ref.url
        assert '2016-04-01' == file_ref.start_time
        assert '2016-04-01' == file_ref.end_time
        assert 'application/x-directory' == file_ref.mime_type
    finally:
        path = '{}/30SWJ,2016-04-01,0/'.format(OUTPUT_DIR)
        if os.path.exists(path):
            shutil.rmtree(path)


def test_notify_copied_to_local():
    dir_to_be_deleted = '{}/24CBS,2017-10-16,1/'.format(OUTPUT_DIR)
    other_dir_to_be_deleted = '{}/24/C/BS/2017/10/16/1/'.format(OUTPUT_DIR)
    try:
        parameters = {'temp_dir': OUTPUT_DIR, 'path': './test/test_data/aws_s2_data/', 'pattern': ''}
        aws_s2_file_system = AwsS2FileSystemAccessor.create_from_parameters(parameters)
        if not os.path.exists(dir_to_be_deleted):
            os.mkdir(dir_to_be_deleted)
        if not os.path.exists(other_dir_to_be_deleted):
            os.makedirs(other_dir_to_be_deleted)
        data_set_meta_info = DataSetMetaInfo('something', '2017-10-16', '2017-10-16', 'AWS_S2_L1C',
                                             '24/C/BS/2017/10/16/1')
        aws_s2_file_system._notify_copied_to_local(data_set_meta_info)
        assert not os.path.exists(dir_to_be_deleted)
        assert not os.path.exists(other_dir_to_be_deleted)
    finally:
        if os.path.exists(dir_to_be_deleted):
            shutil.rmtree(dir_to_be_deleted)
