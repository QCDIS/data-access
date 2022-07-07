"""
Description
===========

This module contains MULTIPLY Data Set Meta Info Providers. The purpose of these is to extract meta data information
from an existing file.
"""

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

from abc import ABCMeta, abstractmethod
from multiply_data_access.data_access import DataSetMetaInfo
from multiply_core.observations import DataTypeConstants, get_relative_path
from multiply_core.util import reproject, get_time_from_year_and_day_of_year, get_time_from_string
from multiply_data_access.modis_tile_coverage_provider import get_tile_coverage
from datetime import timedelta
from shapely.geometry import Polygon
from typing import Optional
from osgeo import gdal, osr
import xarray
import os
import zipfile
from xml.etree import ElementTree
from lxml.etree import XML

GLOBAL = 'POLYGON((-180.0 90.0, 180.0 90.0, 180.0 -90.0, -180.0 -90.0, -180.0 90.0))'


def _get_xml_root(xml_file_name: str):
    tree = ElementTree.parse(xml_file_name)
    return tree.getroot()


class DataSetMetaInfoExtractor(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """The name of the data type supported by this checker."""

    @abstractmethod
    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        """Whether the data at the given path is a valid data product for the type."""


class S1SlcMetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.S1_SLC

    def extract_meta_info(self, path: str) -> Optional[DataSetMetaInfo]:
        if not path.endswith('.zip'):
            path = f'{path}.zip'
        if not os.path.exists(path):
            return None
        s1_slc_archive = zipfile.ZipFile(path, 'r')
        for file in s1_slc_archive.filelist:
            if file.filename.endswith('manifest.safe'):
                return self._create_data_set_meta_info(path, s1_slc_archive.read(file))
        return None

    def _create_data_set_meta_info(self, path: str, manifest_file):
        manifest = XML(manifest_file)
        coverage = self._extract_coverage(manifest)
        start_time = self._extract_start_time(manifest)
        end_time = self._extract_stop_time(manifest)
        id = path.split('/')[-1]
        return DataSetMetaInfo(identifier=id, coverage=coverage, start_time=start_time, end_time=end_time,
                           data_type=DataTypeConstants.S1_SLC)

    def _extract_coverage(self, manifest) -> str:
        for child in manifest:
            for x in child.findall("metadataObject"):
                if x.attrib['ID'] == 'measurementFrameSet':
                    coords = x.find('metadataWrap/xmlData/{http://www.esa.int/safe/sentinel-1.0}frameSet/'
                                    '{http://www.esa.int/safe/sentinel-1.0}frame/'
                                    '{http://www.esa.int/safe/sentinel-1.0}footPrint/'
                                    '{http://www.opengis.net/gml}coordinates').text
                    coords = coords.replace(' ', ',').split(',')
                    return f'POLYGON(({coords[1]} {coords[0]}, {coords[3]} {coords[2]}, {coords[5]} {coords[4]}, ' \
                           f'{coords[7]} {coords[6]}, {coords[1]} {coords[0]}))'
        return ''

    def _extract_start_time(self, manifest) -> str:
        for child in manifest:
            for x in child.findall("metadataObject"):
                if x.attrib['ID'] == 'acquisitionPeriod':
                    return x.find('metadataWrap/xmlData/{http://www.esa.int/safe/sentinel-1.0}acquisitionPeriod/'
                                  '{http://www.esa.int/safe/sentinel-1.0}startTime').text
        return ''

    def _extract_stop_time(self, manifest) -> str:
        for child in manifest:
            for x in child.findall("metadataObject"):
                if x.attrib['ID'] == 'acquisitionPeriod':
                    return x.find('metadataWrap/xmlData/{http://www.esa.int/safe/sentinel-1.0}acquisitionPeriod/'
                                  '{http://www.esa.int/safe/sentinel-1.0}stopTime').text
        return ''


class S1SpeckledMetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.S1_SPECKLED

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        id = path.split('/')[-1]
        dataset = xarray.open_dataset(path)
        if 'lat' in dataset.coords and 'lon' in dataset.coords:
            lat_min = dataset.lat.min().values.item(0)
            lat_max = dataset.lat.max().values.item(0)
            lon_min = dataset.lon.min().values.item(0)
            lon_max = dataset.lon.max().values.item(0)
        coverage = f'POLYGON(({lon_min} {lat_max}, {lon_max} {lat_max}, {lon_max} {lat_min}, ' \
                   f'{lon_min} {lat_min}, {lon_min} {lat_max}))'
        dataset.close()
        start_time = get_time_from_string(id[17:32]).strftime('%Y-%m-%d %H:%M:%S')
        end_time = get_time_from_string(id[33:48]).strftime('%Y-%m-%d %H:%M:%S')
        return DataSetMetaInfo(identifier=id, coverage=coverage, start_time=start_time, end_time=end_time,
                               data_type=DataTypeConstants.S1_SPECKLED)


class AwsS2MetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return 'AWS_S2_L1C'

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        coverage = self._extract_coverage(path)
        time = self._extract_time_from_metadata_file(path)
        return DataSetMetaInfo(coverage, time, time, self.name(), path)

    @staticmethod
    def _get_xml_root(xml_file_name: str):
        tree = ElementTree.parse(xml_file_name)
        return tree.getroot()

    def _extract_time_from_metadata_file(self, filename: str) -> str:
        """Parses the XML metadata file to extract the sensing time."""
        root = self._get_xml_root(filename + '/metadata.xml')
        for child in root:
            for x in child.findall("SENSING_TIME"):
                time = x.text.replace('T', ' ').replace('Z', '')
                time = time[:time.rfind('.')]
                return time

    def _extract_coverage(self, filename: str) -> str:
        """Parses the XML metadata file to extract the sensing time."""
        root = self._get_xml_root(filename + '/metadata.xml')
        ulx = 0
        uly = 0
        x_dim = 0
        y_dim = 0
        n_rows = 0
        n_cols = 0
        for child in root:
            tile_geocoding_element = child.find('Tile_Geocoding')
            if tile_geocoding_element is not None:
                for element in tile_geocoding_element:
                    if element.tag == 'Size' and element.attrib['resolution'] == '60':
                        n_rows = float(element.find('NROWS').text)
                        n_cols = float(element.find('NCOLS').text)
                    elif element.tag == 'Geoposition' and element.attrib['resolution'] == '60':
                        ulx = float(element.find('ULX').text)
                        uly = float(element.find('ULY').text)
                        x_dim = float(element.find('XDIM').text)
                        y_dim = float(element.find('YDIM').text)
        llx = ulx + n_rows * x_dim
        lly = uly + n_cols * y_dim
        gdal_dataset = gdal.Open(filename + '/B01.jp2')
        source_srs = reproject.get_spatial_reference_system_from_dataset(gdal_dataset)
        target_srs = osr.SpatialReference()
        target_srs.SetWellKnownGeogCS('EPSG:4326')
        coords = [ulx, uly, llx, uly, llx, lly, ulx, lly]
        transformed_coords = reproject.transform_coordinates(source_srs, target_srs, coords)
        return 'POLYGON(({0} {1}, {2} {3}, {4} {5}, {6} {7}, {0} {1}))'.format(transformed_coords[0],
                                                                               transformed_coords[1],
                                                                               transformed_coords[2],
                                                                               transformed_coords[3],
                                                                               transformed_coords[4],
                                                                               transformed_coords[5],
                                                                               transformed_coords[6],
                                                                               transformed_coords[7])

    def _extract_tile_id(self, filename: str) -> str:
        """Parses the XML metadata file to extract the tile id."""
        root = self._get_xml_root(filename + '/metadata.xml')
        for child in root:
            for x in child.findall("TILE_ID"):
                return x.text


class S2L1CMetaInfoExtractor(DataSetMetaInfoExtractor):

    def __init__(self):
        self._footprint_element_names = \
            ['{https://psd-14.sentinel2.eo.esa.int/PSD/User_Product_Level-1C.xsd}Geometric_Info', 'Product_Footprint',
             'Product_Footprint', 'Global_Footprint', 'EXT_POS_LIST']
        self._time_element_names = \
            ['{https://psd-14.sentinel2.eo.esa.int/PSD/User_Product_Level-1C.xsd}General_Info', 'Product_Info']
        self._start_time_element = 'PRODUCT_START_TIME'
        self._stop_time_element = 'PRODUCT_STOP_TIME'
        self._polygon_format = 'POLYGON(({1} {0}, {3} {2}, {5} {4}, {7} {6}, {9} {8}))'

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.S2_L1C

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        coverage = self._extract_coverage(path)
        start_time = self._extract_start_time(path)
        end_time = self._extract_end_time(path)
        return DataSetMetaInfo(coverage, start_time, end_time, self.name(), path)

    @staticmethod
    def _get_xml_root(xml_file_name: str):
        tree = ElementTree.parse(xml_file_name)
        return tree.getroot()

    def _extract_coverage(self, path: str) -> str:
        element = self._get_xml_root(path + '/MTD_MSIL1C.xml')
        for footprint_element_name in self._footprint_element_names:
            element = element.find(footprint_element_name)
            if element is None:
                return ''
        coords = element.text.split(' ')
        if len(coords) < 10:
            return ''
        formatted_coords = []
        for index in range(int(len(coords) / 2)):
            formatted_coords.append(f'{coords[2 * index + 1]} {coords[2 * index]}')
        return f"POLYGON(({', '.join(formatted_coords)}))"

    def _extract_start_time(self, path: str) -> str:
        return self._extract_time(path, self._start_time_element)

    def _extract_end_time(self, path: str) -> str:
        return self._extract_time(path, self._stop_time_element)

    def _extract_time(self, path: str, final_element_name: str) -> str:
        element = self._get_xml_root(path + '/MTD_MSIL1C.xml')
        time_element_names = self._time_element_names.copy()
        time_element_names.append(final_element_name)
        for time_element_name in time_element_names:
            element = element.find(time_element_name)
            if element is None:
                return ''
        return element.text.split('.')[0]


class S2L2MetaInfoExtractor(DataSetMetaInfoExtractor):

    def __init__(self):
        self._footprint_element_names = \
            ['{https://psd-14.sentinel2.eo.esa.int/PSD/User_Product_Level-1C.xsd}Geometric_Info', 'Product_Footprint',
             'Product_Footprint', 'Global_Footprint', 'EXT_POS_LIST']
        self._time_element_names = \
            ['{https://psd-14.sentinel2.eo.esa.int/PSD/User_Product_Level-1C.xsd}General_Info', 'Product_Info']
        self._start_time_element = 'PRODUCT_START_TIME'
        self._stop_time_element = 'PRODUCT_STOP_TIME'
        self._polygon_format = 'POLYGON(({1} {0}, {3} {2}, {5} {4}, {7} {6}, {9} {8}))'

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.S2_L2

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        coverage = self._extract_coverage(path)
        start_time = self._extract_start_time(path)
        end_time = self._extract_end_time(path)
        return DataSetMetaInfo(coverage, start_time, end_time, self.name(), path)

    @staticmethod
    def _get_xml_root(xml_file_name: str):
        tree = ElementTree.parse(xml_file_name)
        return tree.getroot()

    def _extract_coverage(self, path: str) -> str:
        element = self._get_xml_root(path + '/MTD_MSIL1C.xml')
        for footprint_element_name in self._footprint_element_names:
            element = element.find(footprint_element_name)
            if element is None:
                return ''
        coords = element.text.split(' ')
        if len(coords) < 10:
            return ''
        formatted_coords = []
        for index in range(int(len(coords) / 2)):
            formatted_coords.append(f'{coords[2 * index + 1]} {coords[2 * index]}')
        return f"POLYGON(({', '.join(formatted_coords)}))"

    def _extract_start_time(self, path: str) -> str:
        return self._extract_time(path, self._start_time_element)

    def _extract_end_time(self, path: str) -> str:
        return self._extract_time(path, self._stop_time_element)

    def _extract_time(self, path: str, final_element_name: str) -> str:
        element = self._get_xml_root(path + '/MTD_MSIL1C.xml')
        time_element_names = self._time_element_names.copy()
        time_element_names.append(final_element_name)
        for time_element_name in time_element_names:
            element = element.find(time_element_name)
            if element is None:
                return ''
        return element.text.split('.')[0]


class AwsS2L2MetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.AWS_S2_L2

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        coverage = self._extract_coverage(path)
        time = self._extract_time_from_metadata_file(path)
        return DataSetMetaInfo(coverage, time, time, self.name(), path)

    @staticmethod
    def _get_xml_root(xml_file_name: str):
        tree = ElementTree.parse(xml_file_name)
        return tree.getroot()

    def _extract_time_from_metadata_file(self, filename: str) -> str:
        """Parses the XML metadata file to extract the sensing time."""
        root = self._get_xml_root(filename + '/metadata.xml')
        for child in root:
            for x in child.findall("SENSING_TIME"):
                time = x.text.replace('T', ' ').replace('Z', '')
                time = time[:time.rfind('.')]
                return time

    def _extract_coverage(self, filename: str) -> str:
        """Parses the XML metadata file to extract the coverage."""
        root = self._get_xml_root(filename + '/metadata.xml')
        ulx = 0
        uly = 0
        x_dim = 0
        y_dim = 0
        n_rows = 0
        n_cols = 0
        for child in root:
            tile_geocoding_element = child.find('Tile_Geocoding')
            if tile_geocoding_element is not None:
                for element in tile_geocoding_element:
                    if element.tag == 'Size' and element.attrib['resolution'] == '60':
                        n_rows = float(element.find('NROWS').text)
                        n_cols = float(element.find('NCOLS').text)
                    elif element.tag == 'Geoposition' and element.attrib['resolution'] == '60':
                        ulx = float(element.find('ULX').text)
                        uly = float(element.find('ULY').text)
                        x_dim = float(element.find('XDIM').text)
                        y_dim = float(element.find('YDIM').text)
        llx = ulx + n_rows * x_dim
        lly = uly + n_cols * y_dim
        gdal_dataset = gdal.Open(filename + '/B01_sur_unc.tif')
        source_srs = reproject.get_spatial_reference_system_from_dataset(gdal_dataset)
        target_srs = osr.SpatialReference()
        target_srs.SetWellKnownGeogCS('EPSG:4326')
        coords = [ulx, uly, llx, uly, llx, lly, ulx, lly]
        transformed_coords = reproject.transform_coordinates(source_srs, target_srs, coords)
        return 'POLYGON(({0} {1}, {2} {3}, {4} {5}, {6} {7}, {0} {1}))'.format(transformed_coords[0],
                                                                               transformed_coords[1],
                                                                               transformed_coords[2],
                                                                               transformed_coords[3],
                                                                               transformed_coords[4],
                                                                               transformed_coords[5],
                                                                               transformed_coords[6],
                                                                               transformed_coords[7])

    def _extract_tile_id(self, filename: str) -> str:
        """Parses the XML metadata file to extract the tile id."""
        root = self._get_xml_root(filename + '/metadata.xml')
        for child in root:
            for x in child.findall("TILE_ID"):
                return x.text


class AsterMetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.ASTER

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        path_lat_id = path[-14:-12]
        path_lat = float(path[-14:-12])
        if path_lat_id == 'S':
            path_lat *= -1
        path_lon_id = path[-12:-11]
        path_lon = float(path[-11:-8])
        if path_lon_id == 'W':
            path_lon *= -1
        coverage = Polygon([[path_lon, path_lat], [path_lon, path_lat + 1], [path_lon + 1, path_lat + 1],
                            [path_lon + 1, path_lat]])
        return DataSetMetaInfo(coverage.wkt, None, None, DataTypeConstants.ASTER, path)


class MODISMetaInfoExtractor(DataSetMetaInfoExtractor):

    def __init__(self):
        self._X_STEP = -463.31271653 * 2400
        self._Y_STEP = 463.31271653 * 2400
        self._M_Y0 = -20015109.354
        self._M_X0 = 10007554.677
        wgs84_srs = osr.SpatialReference()  # Define a SpatialReference object
        wgs84_srs.ImportFromEPSG(4326)  # And set it to WGS84 using the EPSG code
        modis_sinu_srs = osr.SpatialReference()  # define the SpatialReference object
        modis_sinu_srs.ImportFromProj4(
            "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")
        self._wgs84_to_modis = osr.CoordinateTransformation(wgs84_srs, modis_sinu_srs)
        self._modis_to_wgs84 = osr.CoordinateTransformation(modis_sinu_srs, wgs84_srs)

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        h = int(path[-27:-25])
        v = int(path[-24:-22])
        tile_coverage = get_tile_coverage(h, v).wkt
        year = int(path[-36:-32])
        doy = int(path[-32:-29])
        start_time = get_time_from_year_and_day_of_year(year, doy)
        end_time = self._get_end_time(year, doy)
        return DataSetMetaInfo(tile_coverage, start_time.strftime('%Y-%m-%d %H:%M:%S'),
                               end_time.strftime('%Y-%m-%d %H:%M:%S'), self.name(), path[path.find('MCD'):])

    @abstractmethod
    def _get_end_time(self, year: int, doy: int):
        pass


class MODISMCD43MetaInfoExtractor(MODISMetaInfoExtractor):

    def _get_end_time(self, year: int, doy: int):
        time = get_time_from_year_and_day_of_year(year, doy, set_to_end=True)
        return time

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.MODIS_MCD_43


class MODISMCD15A2MetaInfoExtractor(MODISMetaInfoExtractor):

    def _get_end_time(self, year: int, doy: int):
        time = get_time_from_year_and_day_of_year(year, doy, set_to_end=True)
        time += timedelta(days=7)
        return time

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.MODIS_MCD_15_A2


class S2aMetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.S2A_EMULATOR

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        return DataSetMetaInfo(GLOBAL, None, None, DataTypeConstants.S2A_EMULATOR, path)


class S2bMetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.S2B_EMULATOR

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        return DataSetMetaInfo(GLOBAL, None, None, DataTypeConstants.S2B_EMULATOR, path)


class WvMetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.WV_EMULATOR

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        return DataSetMetaInfo(GLOBAL, None, None, DataTypeConstants.WV_EMULATOR, path)


class CamsMetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.CAMS

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        return DataSetMetaInfo(GLOBAL, path[-13:-3], path[-13:-3], DataTypeConstants.CAMS, path)


class CamsTiffMetaInfoExtractor(DataSetMetaInfoExtractor):

    @classmethod
    def name(cls) -> str:
        return DataTypeConstants.CAMS_TIFF

    def extract_meta_info(self, path: str) -> DataSetMetaInfo:
        relative_path = get_relative_path(path, DataTypeConstants.CAMS_TIFF)
        return DataSetMetaInfo(GLOBAL, relative_path.replace('_', '-'), relative_path.replace('_', '-'),
                               DataTypeConstants.CAMS_TIFF, relative_path)


DATA_SET_META_INFO_PROVIDERS = []


def add_data_set_meta_info_extractor(data_set_meta_info_provider: DataSetMetaInfoExtractor):
    DATA_SET_META_INFO_PROVIDERS.append(data_set_meta_info_provider)


add_data_set_meta_info_extractor(S1SlcMetaInfoExtractor())
add_data_set_meta_info_extractor(S1SpeckledMetaInfoExtractor())
add_data_set_meta_info_extractor(AwsS2MetaInfoExtractor())
add_data_set_meta_info_extractor(AwsS2L2MetaInfoExtractor())
add_data_set_meta_info_extractor(S2L1CMetaInfoExtractor())
add_data_set_meta_info_extractor(S2L2MetaInfoExtractor())
add_data_set_meta_info_extractor(AsterMetaInfoExtractor())
add_data_set_meta_info_extractor(S2aMetaInfoExtractor())
add_data_set_meta_info_extractor(S2bMetaInfoExtractor())
add_data_set_meta_info_extractor(WvMetaInfoExtractor())
add_data_set_meta_info_extractor(CamsMetaInfoExtractor())
add_data_set_meta_info_extractor(MODISMCD43MetaInfoExtractor())
add_data_set_meta_info_extractor(MODISMCD15A2MetaInfoExtractor())
add_data_set_meta_info_extractor(CamsTiffMetaInfoExtractor())


def get_data_set_meta_info(data_type: str, path: str) -> Optional[DataSetMetaInfo]:
    for data_set_meta_info_provider in DATA_SET_META_INFO_PROVIDERS:
        if data_set_meta_info_provider.name() == data_type:
            return data_set_meta_info_provider.extract_meta_info(path)
