import glob
import os
import shutil

from datetime import datetime
from typing import List, Sequence

from multiply_core.observations import DataTypeConstants
from multiply_core.util import get_mime_type, FileRef
from multiply_data_access.data_access import DataSetMetaInfo, FileSystemAccessor, MetaInfoProvider, \
    MetaInfoProviderAccessor, FileSystem
from multiply_data_access.locally_wrapped_data_access import LocallyWrappedFileSystem, LocallyWrappedMetaInfoProvider


_META_INFO_PROVIDER_NAME = 'CreoDiasMetaInfoProvider'
_FILE_SYSTEM_NAME = 'CreoDiasFileSystem'
_PROVIDED_DATA_TYPES = [DataTypeConstants.S1_SLC, DataTypeConstants.S2_L1C]


class CreoDiasMetaInfoProvider(LocallyWrappedMetaInfoProvider):

    def _init_wrapped_meta_info_provider(self, parameters: dict) -> None:
        # TODO retrieve here any parameters from the dictionary that may have been passed from the outside. may be pass
        pass

    def _query_wrapped_meta_info_provider(self, query_string: str, local_data_set_meta_infos: List[DataSetMetaInfo]) \
            -> List[DataSetMetaInfo]:
        # TODO the actual query
        # DataSetMetaInfo() requires: coverage as wkt, start_time, end_time,\
        # data_type (DataTypeConstants.S1_SLC or DataTypeConstants.S2_L1C), identifier (name)
        data_types = self.get_data_types_from_query_string(query_string)
        roi = self.get_roi_from_query_string(query_string)
        start_time = datetime.strftime(self.get_start_time_from_query_string(query_string), "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strftime(self.get_end_time_from_query_string(query_string), "%Y-%m-%dT%H:%M:%SZ")
        return []

    def _get_wrapped_parameters_as_dict(self) -> dict:
        # TODO return the parameters that were needed to create this meta info provider. Must be consistent with the dict in init
        return {}

    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    def provides_data_type(self, data_type: str) -> bool:
        return data_type in _PROVIDED_DATA_TYPES

    def get_provided_data_types(self) -> List[str]:
        return _PROVIDED_DATA_TYPES

    def encapsulates_data_type(self, data_type: str) -> bool:
        return False


class CreoDiasMetaInfoProviderCreator(MetaInfoProviderAccessor):

    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> MetaInfoProvider:
        return CreoDiasMetaInfoProvider(parameters)


class CreoDiasFileSystem(LocallyWrappedFileSystem):

    def _init_wrapped_file_system(self, parameters: dict) -> None:
        # TODO retrieve here any parameters from the dictionary that may have been passed from the outside.
        # here we assume that there is a temp dir parameter to which the data is downloaded before it is put into the archive
        if 'temp_dir' not in parameters.keys():
            raise ValueError('No valid temporal directory provided for CreoDias File System')
        if not os.path.exists(parameters['temp_dir']):
            os.makedirs(parameters['temp_dir'])
        self._temp_dir = parameters['temp_dir']

    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        # TODO the actual retrieval
        # FileRef(): Parameters: URL to local file, start_time as str, end_time as str, mime_type
        mime_type = get_mime_type(data_set_meta_info.identifier)
        pass

    def _get_wrapped_parameters_as_dict(self) -> dict:
    # TODO return the parameters that were needed to create this meta info provider. Must be consistent with the dict in init
        return {'temp_dir': self._temp_dir}

    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo) -> None:
        files = glob.glob(f'{self._temp_dir}/{data_set_meta_info.identifier}*')
        for file in files:
            if os.path.exists(file):
                if os.path.isdir(file):
                    shutil.rmtree(file)
                else:
                    os.remove(file)

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    def clear_cache(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)


class CreodiasFileSystemAccessor(FileSystemAccessor):

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> FileSystem:
        return CreoDiasFileSystem(parameters)
