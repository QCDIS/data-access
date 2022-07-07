"""
Description
===========

This module contains the functionality to access data that is encapsulated in the form of a single file in the .vrt
format that is globally an.
"""

from osgeo import gdal
import os
import shutil
import xml.etree.ElementTree as ET

from shapely.geometry import Polygon
from shapely.ops import cascaded_union
from shapely.wkt import loads
from typing import List, Sequence

from multiply_core.util import FileRef, get_mime_type
from multiply_data_access.data_access import DataSetMetaInfo, FileSystem, FileSystemAccessor, MetaInfoProvider, \
    MetaInfoProviderAccessor
from multiply_data_access.registrations import create_meta_info_provider_from_dict, create_file_system_from_dict

_META_INFO_PROVIDER_NAME = 'VrtMetaInfoProvider'
_FILE_SYSTEM_NAME = 'VrtFileSystem'


class VrtMetaInfoProvider(MetaInfoProvider):

    def __init__(self, parameters: dict):
        if 'path_to_vrt_file' not in parameters:
            raise ValueError('No vrt file provided')
        self._path_to_vrt_file = parameters['path_to_vrt_file']
        if 'encapsulated_data_type' not in parameters:
            raise ValueError('Vrt meta info provider must know encapsulated data type')
        self._encapsulated_data_type = parameters['encapsulated_data_type']
        if 'accessed_meta_info_provider' not in parameters:
            raise ValueError('Vrt meta info provider must access other meta info provider')
        meta_info_provider_as_dict = {'type': parameters['accessed_meta_info_provider'], 'parameters': parameters}
        meta_info_provider_as_dict['parameters']['supported_data_types'] = parameters['encapsulated_data_type']
        self._wrapped_meta_info_provider = create_meta_info_provider_from_dict(meta_info_provider_as_dict)
        if 'provided_data_type' not in parameters:
            raise ValueError('Vrt meta info provider must know provided data type')
        self._provided_data_type = parameters['provided_data_type']

    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    def query(self, query_string: str) -> List[DataSetMetaInfo]:
        if self._provided_data_type not in self.get_data_types_from_query_string(query_string):
            return []
        roi = self.get_roi_from_query_string(query_string)
        coverages, referenced_data = self._get_coverages_from_local_meta_info_provider()
        coverage = cascaded_union(coverages)
        if not roi.within(coverage):
            additional_coverages, additional_files = self._get_coverages_from_wrapped_meta_info_provider(query_string)
            for i in range(len(additional_files)):
                if additional_files[i] not in referenced_data:
                    referenced_data.append(additional_files[i])
                    coverages.append(additional_coverages[i])
            coverage = cascaded_union(coverages)
        referenced_data = ';'.join(referenced_data)
        data_set_meta_info = DataSetMetaInfo(coverage.wkt, None, None, self._provided_data_type,
                                             self._path_to_vrt_file, referenced_data)
        return [data_set_meta_info]

    def query_local(self, query_string: str) -> List[DataSetMetaInfo]:
        if self._provided_data_type not in self.get_data_types_from_query_string(query_string):
            return []
        roi = self.get_roi_from_query_string(query_string)
        coverages, referenced_data = self._get_coverages_from_local_meta_info_provider()
        coverage = cascaded_union(coverages)
        if not roi.within(coverage):
            return []
        referenced_data = ';'.join(referenced_data)
        data_set_meta_info = DataSetMetaInfo(coverage.wkt, None, None, self._provided_data_type,
                                             self._path_to_vrt_file, referenced_data)
        return [data_set_meta_info]

    def query_non_local(self, query_string: str) -> List[DataSetMetaInfo]:
        if self._provided_data_type not in self.get_data_types_from_query_string(query_string):
            return []
        roi = self.get_roi_from_query_string(query_string)
        coverages, referenced_data = self._get_coverages_from_local_meta_info_provider()
        coverage = cascaded_union(coverages)
        if roi.within(coverage):
            return []
        additional_coverages, additional_files = self._get_coverages_from_wrapped_meta_info_provider(query_string)
        for i in range(len(additional_files)):
            if additional_files[i] not in referenced_data:
                referenced_data.append(additional_files[i])
                coverages.append(additional_coverages[i])
        coverage = cascaded_union(coverages)
        referenced_data = ';'.join(referenced_data)
        data_set_meta_info = DataSetMetaInfo(coverage.wkt, None, None, self._provided_data_type,
                                             self._path_to_vrt_file, referenced_data)
        return [data_set_meta_info]

    def _get_referenced_data_sets_from_vrt(self) -> List[str]:
        referenced_data_sets = []
        if not os.path.exists(self._path_to_vrt_file):
            return referenced_data_sets
        tree = ET.parse(self._path_to_vrt_file)
        root = tree.getroot()
        raster_bands = root.find('VRTRasterBand').findall('SimpleSource')
        for raster_band in raster_bands:
            referenced_data_set = raster_band.find('SourceFilename').text
            referenced_data_sets.append(referenced_data_set.split('/')[-1])
        return referenced_data_sets

    def _get_coverages_from_local_meta_info_provider(self) -> (List[Polygon], List[str]):
        local_data_meta_set_infos = self._wrapped_meta_info_provider.get_all_data()
        coverages = []
        names = []
        for data_set_meta_info in local_data_meta_set_infos:
            coverages.append(loads(data_set_meta_info.coverage))
            names.append(data_set_meta_info.identifier)
        return coverages, names

    def _get_coverages_from_wrapped_meta_info_provider(self, query_string: str) -> (List[Polygon], List[str]):
        split_string = query_string.split(';')
        split_string[3] = self._encapsulated_data_type
        new_query_string = ';'.join(split_string)
        encapsulated_data_meta_set_infos = self._wrapped_meta_info_provider.query(new_query_string)
        coverages = []
        names = []
        for data_set_meta_info in encapsulated_data_meta_set_infos:
            coverages.append(loads(data_set_meta_info.coverage))
            names.append(data_set_meta_info.identifier)
        return coverages, names

    def provides_data_type(self, data_type: str) -> bool:
        return data_type == self._provided_data_type

    def get_provided_data_types(self) -> List[str]:
        return [self._provided_data_type]

    def encapsulates_data_type(self, data_type: str) -> bool:
        return data_type == self._encapsulated_data_type

    def _get_parameters_as_dict(self) -> dict:
        parameters = {'path_to_vrt_file': self._path_to_vrt_file,
                      'encapsulated_data_type': self._encapsulated_data_type,
                      'provided_data_type': self._provided_data_type,
                      'accessed_meta_info_provider': self._wrapped_meta_info_provider.name()}
        parameters.update(self._wrapped_meta_info_provider.get_as_dict()['parameters'])
        del parameters['supported_data_types']
        return parameters

    def can_update(self) -> bool:
        return self._wrapped_meta_info_provider.can_update()

    def update(self, data_set_meta_info: DataSetMetaInfo):
        if data_set_meta_info.data_type == self._encapsulated_data_type:
            self._wrapped_meta_info_provider.update(data_set_meta_info)

    def remove(self, data_set_meta_info: DataSetMetaInfo):
        self._wrapped_meta_info_provider.remove(data_set_meta_info)

    def get_all_data(self) -> Sequence[DataSetMetaInfo]:
        return self._wrapped_meta_info_provider.get_all_data()


class VrtMetaInfoProviderAccessor(MetaInfoProviderAccessor):

    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> VrtMetaInfoProvider:
        return VrtMetaInfoProvider(parameters)


class VrtFileSystem(FileSystem):

    def __init__(self, parameters: dict):
        if 'path_to_vrt_file' not in parameters:
            raise ValueError('No vrt file provided')
        self._path_to_vrt_file = parameters['path_to_vrt_file']
        if 'encapsulated_data_type' not in parameters:
            raise ValueError('Vrt meta info provider must know encapsulated data type')
        self._encapsulated_data_type = parameters['encapsulated_data_type']
        file_system_as_dict = {'type': parameters['accessed_file_system'], 'parameters': parameters}
        self._file_system = create_file_system_from_dict(file_system_as_dict)

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    def get(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        if data_set_meta_info.referenced_data is None:
            return []
        required_datasets = []
        referenced_data_sets = data_set_meta_info.referenced_data.split(';')
        for data_set in referenced_data_sets:
            # coverage is wrong here. We leave it as it makes no difference.
            file_refs = self._file_system.get(DataSetMetaInfo(data_set_meta_info.coverage, None, None,
                                                              self._encapsulated_data_type, data_set))
            for file_ref in file_refs:
                if file_ref.url not in required_datasets:
                    required_datasets.append(file_ref.url.replace('//', '/'))
        vrt_dataset = gdal.BuildVRT(self._path_to_vrt_file, required_datasets)
        vrt_dataset.SetMetadataItem('COVERAGE', data_set_meta_info.coverage)
        vrt_dataset.FlushCache()
        self._set_absolute_sources(required_datasets)
        return [FileRef(self._path_to_vrt_file, None, None, get_mime_type(self._path_to_vrt_file))]

    def _set_absolute_sources(self, file_refs: List[str]):
        if not os.path.exists(self._path_to_vrt_file):
            return
        tree = ET.parse(self._path_to_vrt_file)
        root = tree.getroot()
        raster_bands = root.findall('VRTRasterBand')
        for raster_band in raster_bands:
            source_file_name_element = raster_band.find('SimpleSource').find('SourceFilename')
            if 'relativeToVRT' in source_file_name_element.attrib and \
                    source_file_name_element.attrib['relativeToVRT'] == '1':
                file_name = source_file_name_element.text.split('/')[-1]
                for file_ref in file_refs:
                    if file_ref.split('/')[-1] == file_name:
                        source_file_name_element.text = file_ref
                        source_file_name_element.attrib['relativeToVRT'] = '0'
        tree.write(self._path_to_vrt_file)

    def get_parameters_as_dict(self) -> dict:
        parameters = {'path_to_vrt_file': self._path_to_vrt_file,
                      'encapsulated_data_type': self._encapsulated_data_type,
                      'accessed_file_system': self._file_system.name()}
        parameters.update(self._file_system.get_as_dict()['parameters'])
        return parameters

    def can_put(self):
        return False

    def put(self, from_url: str, data_set_meta_info: DataSetMetaInfo):
        raise UserWarning('Method not supported')

    def remove(self, data_set_meta_info: DataSetMetaInfo):
        raise UserWarning('Method not supported')

    def scan(self) -> Sequence[DataSetMetaInfo]:
        return self._file_system.scan()

    def clear_cache(self):
        self._file_system.clear_cache()


class VrtFileSystemAccessor(FileSystemAccessor):

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> FileSystem:
        return VrtFileSystem(parameters)
