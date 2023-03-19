import os

from multiply_data_access.data_set_meta_info_extraction import AwsS2MetaInfoExtractor, S2L1CMetaInfoExtractor, \
    AwsS2L2MetaInfoExtractor, MODISMCD43MetaInfoExtractor, MODISMCD15A2MetaInfoExtractor, S1SlcMetaInfoExtractor, \
    S1SpeckledMetaInfoExtractor, S2L2MetaInfoExtractor

from shapely import wkt
from shapely.wkt import loads

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"
import urllib.request
import zipfile

test_data_save_path = '/tmp/data-access-test_data.zip'
if not os.path.exists(test_data_save_path):
    urllib.request.urlretrieve('https://github.com/QCDIS/data-access/raw/master/test/test_data.zip', test_data_save_path)
    with zipfile.ZipFile(test_data_save_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp')
    zip_ref.close()
base_path = '/tmp/test_data/'


path_to_s2_dir = base_path + 'aws_s2_data/29/S/QB/2017/9/4/0/'
path_to_s2_l1c_dir = base_path + 'S2B_MSIL1C_20180819T100019_N0206_R122_T32TQR_20180819T141300'
path_to_other_s2_l1c_dir = base_path + 'S2A_MSIL1C_20180510T094031_N0206_R036_T35VNE_20180510T114819'
path_to_aws_s2_l2_dir = base_path + 's2_l2_dir/'
path_to_s2_l2_dir = base_path + 'S2A_MSIL1C_20180510T094031_N0206_R036_T35VNE_20180510T114819-ac'


def test_s1_slc_meta_info_extractor_name():
    extractor = S1SlcMetaInfoExtractor()

    assert 'S1_SLC' == extractor.name()


def test_s1_slc_meta_info_extractor_extract_meta_info():
    extractor = S1SlcMetaInfoExtractor()
    path_to_s1_dir = base_path + 'S1_SLC/S1A_IW_SLC__1SDV_20180603T053307_20180603T053334_022188_026669_A432'
    data_set_meta_info = extractor.extract_meta_info(path_to_s1_dir)
    assert 'S1_SLC' == data_set_meta_info.data_type
    assert 'S1A_IW_SLC__1SDV_20180603T053307_20180603T053334_022188_026669_A432.zip' == data_set_meta_info.identifier
    assert '2018-06-03T05:33:07.493195' == data_set_meta_info.start_time
    assert '2018-06-03T05:33:34.589538' == data_set_meta_info.end_time
    expected_coverage = wkt.loads(
        'POLYGON ((12.121230 52.448013,8.330203 52.855953,8.744157 54.475960, 12.684868 54.064266, '
        '12.121230 52.448013))')
    coverage = wkt.loads(data_set_meta_info.coverage)
    assert coverage.almost_equals(expected_coverage)


def test_s1_speckled_meta_info_extractor_name():
    extractor = S1SpeckledMetaInfoExtractor()

    assert 'S1_Speckled' == extractor.name()


def test_s1_speckled_meta_info_extractor_extract_meta_info():
    extractor = S1SpeckledMetaInfoExtractor()
    path_to_s1_dir = base_path + 's1_speckled/' \
                     'S1A_IW_SLC__1SDV_20170613T054059_20170613T054126_017011_01C547_62FA_GC_RC_No_Su_Co_speckle.nc'
    data_set_meta_info = extractor.extract_meta_info(path_to_s1_dir)
    assert 'S1_Speckled' == data_set_meta_info.data_type
    assert 'S1A_IW_SLC__1SDV_20170613T054059_20170613T054126_017011_01C547_62FA_GC_RC_No_Su_Co_speckle.nc' \
           == data_set_meta_info.identifier
    assert '2017-06-13 05:40:59' == data_set_meta_info.start_time
    assert '2017-06-13 05:41:26' == data_set_meta_info.end_time
    expected_coverage = wkt.loads('POLYGON((9.990013694653712 53.509990658829, 10.00999222657253 53.509990658829, '
                                  '10.00999222657253 53.49001212691018, 9.990013694653712 53.49001212691018, '
                                  '9.990013694653712 53.509990658829))')
    coverage = wkt.loads(data_set_meta_info.coverage)
    assert coverage.almost_equals(expected_coverage)


def test_aws_s2_meta_info_extractor():
    provider = AwsS2MetaInfoExtractor()
    assert 'AWS_S2_L1C' == provider.name()
    data_set_meta_info = provider.extract_meta_info(path_to_s2_dir)
    assert 'AWS_S2_L1C' == data_set_meta_info.data_type
    assert path_to_s2_dir == data_set_meta_info.identifier
    assert '2017-09-04 11:18:25' == data_set_meta_info.start_time
    assert '2017-09-04 11:18:25' == data_set_meta_info.end_time
    coverage = wkt.loads(data_set_meta_info.coverage)
    expected_coverage = wkt.loads('POLYGON((-6.724926539250627 37.92559054724302, '
                                  '-5.477449084961044 37.89483865860684, -5.523445655745983 36.90697181266162,'
                                  '-6.754676710360797 36.93665039721959, -6.724926539250627 37.92559054724302))')
    assert coverage.almost_equals(expected_coverage)


def test_s2_l1c_meta_info_extractor():
    provider = S2L1CMetaInfoExtractor()
    assert 'S2_L1C' == provider.name()
    data_set_meta_info = provider.extract_meta_info(path_to_s2_l1c_dir)
    assert 'S2_L1C' == data_set_meta_info.data_type
    assert path_to_s2_l1c_dir == data_set_meta_info.identifier
    assert '2017-09-10T10:40:21' == data_set_meta_info.start_time
    assert '2017-09-10T10:40:21' == data_set_meta_info.end_time
    assert 'POLYGON((7.434601639013215 55.03692054207882, 9.152753273727466 55.04689020612033, ' \
           '9.149109963691934 54.06011138907911, 7.471920122716345 54.050496442234184, ' \
           '7.434601639013215 55.03692054207882))' == data_set_meta_info.coverage

    other_data_set_meta_info = provider.extract_meta_info(path_to_other_s2_l1c_dir)
    assert 'S2_L1C' == other_data_set_meta_info.data_type
    assert path_to_other_s2_l1c_dir == other_data_set_meta_info.identifier
    assert '2018-05-10T09:40:31' == other_data_set_meta_info.start_time
    assert '2018-05-10T09:40:31' == other_data_set_meta_info.end_time
    expected_wkt = loads('POLYGON((28.394882641284777 58.63040715531772, 28.393297474410343 58.62823859389064, ' \
                         '28.29082169566504 58.486996787971286, 28.18907762762528 58.345753584683216, ' \
                         '28.088319012350805 58.204356444908974, 27.98829962738705 58.06294231078879,' \
                         '27.888678484216804 57.92140960784396, 27.78962872691684 57.77984244002506, ' \
                         '27.698886982431844 57.64936699051037, 26.99966486553254 57.65444945078362, ' \
                         '26.999655468075847 58.64065618624541, 28.394882641284777 58.63040715531772))')
    coverage = loads(other_data_set_meta_info.coverage)
    assert expected_wkt.almost_equals(coverage)


def test_s2_l2_meta_info_extractor():
    provider = S2L2MetaInfoExtractor()
    assert 'S2_L2' == provider.name()
    data_set_meta_info = provider.extract_meta_info(path_to_s2_l2_dir)
    assert 'S2_L2' == data_set_meta_info.data_type
    assert path_to_s2_l2_dir == data_set_meta_info.identifier
    assert '2018-05-10T09:40:31' == data_set_meta_info.start_time
    assert '2018-05-10T09:40:31' == data_set_meta_info.end_time
    expected_wkt = loads('POLYGON((28.394882641284777 58.63040715531772, 28.393297474410343 58.62823859389064, ' \
                         '28.29082169566504 58.486996787971286, 28.18907762762528 58.345753584683216, ' \
                         '28.088319012350805 58.204356444908974, 27.98829962738705 58.06294231078879,' \
                         '27.888678484216804 57.92140960784396, 27.78962872691684 57.77984244002506, ' \
                         '27.698886982431844 57.64936699051037, 26.99966486553254 57.65444945078362, ' \
                         '26.999655468075847 58.64065618624541, 28.394882641284777 58.63040715531772))')
    coverage = loads(data_set_meta_info.coverage)
    assert expected_wkt.almost_equals(coverage)


def test_aws_s2_l2_meta_info_extractor():
    provider = AwsS2L2MetaInfoExtractor()
    assert 'AWS_S2_L2' == provider.name()
    data_set_meta_info = provider.extract_meta_info(path_to_aws_s2_l2_dir)
    assert 'AWS_S2_L2' == data_set_meta_info.data_type
    assert path_to_aws_s2_l2_dir == data_set_meta_info.identifier
    assert '2017-01-19 11:05:33' == data_set_meta_info.start_time
    assert '2017-01-19 11:05:33' == data_set_meta_info.end_time
    expected_wkt_coverage = wkt.loads('POLYGON((-3.000233454377241 39.75026792656398, '
                                      '-1.718719651333537 39.74319619168243, -1.736596780811647 38.7540360477788, '
                                      '-3.00023019602957 38.76086445672779, -3.000233454377241 39.75026792656398))')
    coverage = wkt.loads(data_set_meta_info.coverage)
    assert coverage.almost_equals(expected_wkt_coverage)


def test_modis_mcd43a1_extractor():
    extractor = MODISMCD43MetaInfoExtractor()
    assert 'MCD43A1.006' == extractor.name()
    data_set_meta_info = extractor.extract_meta_info('/some/thing/MCD43A1.A2017015.h17v05.006.2017024094450.hdf')
    assert 'MCD43A1.006' == data_set_meta_info.data_type
    assert 'MCD43A1.A2017015.h17v05.006.2017024094450.hdf' == data_set_meta_info.identifier
    assert '2017-01-15 00:00:00' == data_set_meta_info.start_time
    assert '2017-01-15 23:59:59' == data_set_meta_info.end_time
    coverage = wkt.loads(data_set_meta_info.coverage)
    expected_coverage = wkt.loads('POLYGON ((-13.05407289035348 39.99999999616804, '
                                  '1.127072786096139e-09 39.99999999616804, 9.96954409223065e-10 29.9999999970181, '
                                  '-11.54700538146705 29.9999999970181, -13.05407289035348 39.99999999616804))')
    assert coverage.almost_equals(expected_coverage)


def test_modis_mcd15a2_extractor():
    extractor = MODISMCD15A2MetaInfoExtractor()
    assert 'MCD15A2H.006' == extractor.name()
    data_set_meta_info = extractor.extract_meta_info('/some/thing/MCD15A2H.A2018313.h17v05.006.2018323214613.hdf')
    assert 'MCD15A2H.006' == data_set_meta_info.data_type
    assert 'MCD15A2H.A2018313.h17v05.006.2018323214613.hdf' == data_set_meta_info.identifier
    assert '2018-11-09 00:00:00' == data_set_meta_info.start_time
    assert '2018-11-16 23:59:59' == data_set_meta_info.end_time
    coverage = wkt.loads(data_set_meta_info.coverage)
    expected_coverage = wkt.loads('POLYGON ((-13.05407289035348 39.99999999616804, '
                                  '1.127072786096139e-09 39.99999999616804, 9.96954409223065e-10 29.9999999970181, '
                                  '-11.54700538146705 29.9999999970181, -13.05407289035348 39.99999999616804))')
    assert coverage.almost_equals(expected_coverage)
