"""
Description
===========

This module contains functionality for wrapping file systems or meta info providers with locally available file systems
or meta info providers. This is done with the objective to facilitate the handling of data that needs to be downloaded
(or is in another way hard to access) by putting it in a local data store.
by
"""

from abc import abstractmethod
import logging
from multiply_core.util import FileRef
from multiply_data_access.data_access import DataSetMetaInfo, FileSystem, MetaInfoProvider
from multiply_data_access.local_file_system import LocalFileSystem
from multiply_data_access.json_meta_info_provider import JsonMetaInfoProvider
from typing import List, Sequence

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'


class LocallyWrappedFileSystem(FileSystem):

    def __init__(self, parameters: dict):
        if 'path' not in parameters.keys():
            raise ValueError('Missing parameter \'path\'')
        if 'pattern' not in parameters.keys():
            raise ValueError('Missing parameter \'pattern\'')
        self._local_file_system = LocalFileSystem(parameters['path'], parameters['pattern'])
        self._init_wrapped_file_system(parameters)

    @abstractmethod
    def _init_wrapped_file_system(self, parameters: dict) -> None:
        """Initializes the file system wrapped by the LocallyWrappingFileSystem. To be called instead of __init__"""

    def get(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        file_refs = self._local_file_system.get(data_set_meta_info)
        if len(file_refs) > 0:
            return file_refs
        file_refs_from_wrapped = self._get_from_wrapped(data_set_meta_info)
        if len(file_refs_from_wrapped) == 0:
            return []
        self._local_file_system.put(file_refs_from_wrapped[0].url, data_set_meta_info)
        self._notify_copied_to_local(data_set_meta_info)
        return self._local_file_system.get(data_set_meta_info)

    @abstractmethod
    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        """Retrieves the file ref from the wrapped file system."""

    @abstractmethod
    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo) -> None:
        """Called when the data set has been copied to the local file system."""

    def get_parameters_as_dict(self) -> dict:
        local_parameters = self._local_file_system.get_parameters_as_dict()
        wrapped_parameters = self._get_wrapped_parameters_as_dict()
        local_parameters.update(wrapped_parameters)
        return local_parameters

    @abstractmethod
    def _get_wrapped_parameters_as_dict(self) -> dict:
        """
        :return: The parameters of this wrapped file system as dict
        """

    def can_put(self) -> bool:
        return False

    def put(self, from_url: str, data_set_meta_info: DataSetMetaInfo) -> DataSetMetaInfo:
        raise UserWarning('Method not supported')

    def remove(self, data_set_meta_info: DataSetMetaInfo):
        raise UserWarning('Method not supported')

    def scan(self) -> Sequence[DataSetMetaInfo]:
        logging.info('Scanning local file system, not remote')
        return self._local_file_system.scan()


class LocallyWrappedMetaInfoProvider(MetaInfoProvider):

    def __init__(self, parameters: dict):
        if 'path_to_json_file' not in parameters.keys():
            raise ValueError('Missing path to json file')
        if 'supported_data_types' in parameters.keys():
            provided_data_types = parameters['supported_data_types']
        else:
            provided_data_types = ','.join(self.get_provided_data_types())
        self._json_meta_info_provider = JsonMetaInfoProvider(parameters['path_to_json_file'], provided_data_types)
        self._init_wrapped_meta_info_provider(parameters)

    @abstractmethod
    def _init_wrapped_meta_info_provider(self, parameters: dict) -> None:
        """Initializes the meta info provider wrapped by the LocallyWrappingMetaInfoProvider.
        To be called instead of __init__"""

    def query(self, query_string: str) -> List[DataSetMetaInfo]:
        local_data_meta_set_infos = self._json_meta_info_provider.query(query_string)
        wrapped_data_set_meta_infos = self._query_wrapped_meta_info_provider(query_string, local_data_meta_set_infos)
        to_be_appended = []
        for wrapped_data_set_meta_info in wrapped_data_set_meta_infos:
            already_contained = False
            for local_data_meta_set_info in local_data_meta_set_infos:
                if wrapped_data_set_meta_info.equals(local_data_meta_set_info):
                    already_contained = True
                    break
            if not already_contained:
                to_be_appended.append(wrapped_data_set_meta_info)
        for data_set_meta_info in to_be_appended:
            local_data_meta_set_infos.append(data_set_meta_info)
        return local_data_meta_set_infos

    def query_local(self, query_string: str) -> List[DataSetMetaInfo]:
        return self._json_meta_info_provider.query(query_string)

    def query_non_local(self, query_string: str) -> List[DataSetMetaInfo]:
        local_data_meta_set_infos = self._json_meta_info_provider.query(query_string)
        return self._query_wrapped_meta_info_provider(query_string, local_data_meta_set_infos)

    @staticmethod
    def _is_provided_locally(data_set_meta_info: DataSetMetaInfo,
                                 local_data_set_meta_infos: List[DataSetMetaInfo]) -> bool:
        for local_data_set_meta_info in local_data_set_meta_infos:
            if local_data_set_meta_info.equals(data_set_meta_info):
                return True
        return False

    @abstractmethod
    def _query_wrapped_meta_info_provider(self, query_string: str, local_data_set_meta_infos: List[DataSetMetaInfo]) \
            -> List[DataSetMetaInfo]:
        """Queries a wrapped file system."""

    def _get_parameters_as_dict(self) -> dict:
        local_parameters = self._json_meta_info_provider._get_parameters_as_dict()
        del local_parameters['supported_data_types']
        wrapped_parameters = self._get_wrapped_parameters_as_dict()
        local_parameters.update(wrapped_parameters)
        return local_parameters

    @abstractmethod
    def _get_wrapped_parameters_as_dict(self) -> dict:
        """
        :return: The parameters of this wrapped meta info provider as dict
        """

    def notify_got(self, data_set_meta_info: DataSetMetaInfo):
        self._json_meta_info_provider.update(data_set_meta_info)

    def can_update(self) -> bool:
        return True

    def update(self, data_set_meta_info: DataSetMetaInfo):
        logging.info('Updating local meta info provider, not remote')
        if self.provides_data_type(data_set_meta_info.data_type):
            self._json_meta_info_provider.update(data_set_meta_info)

    def remove(self, data_set_meta_info: DataSetMetaInfo):
        self._json_meta_info_provider.remove(data_set_meta_info)

    def get_all_data(self) -> Sequence[DataSetMetaInfo]:
        return self._json_meta_info_provider.get_all_data()
