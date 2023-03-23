"""
Description
===========

This module contains the functionality to access data from a remote directory accessible via http.
"""
import logging
import os
import re
import requests
import shutil

from bs4 import BeautifulSoup
from sys import stdout
from typing import List, Sequence
import urllib.request as urllib2

from multiply_core.observations import get_file_pattern, is_valid_for
from multiply_core.util import FileRef, get_mime_type
from multiply_data_access.data_access import DataSetMetaInfo, FileSystemAccessor, MetaInfoProviderAccessor
from multiply_data_access.data_set_meta_info_extraction import get_data_set_meta_info

__author__ = 'Tonio Fincke (Brockmann Consult GmbH),' \
             'José Luis Gómez-Dans (University College London)'

from multiply_data_access.locally_wrapped_data_access import LocallyWrappedFileSystem, LocallyWrappedMetaInfoProvider

_FILE_SYSTEM_NAME = 'HttpFileSystem'
_META_INFO_PROVIDER_NAME = 'HttpMetaInfoProvider'


class HttpMetaInfoProvider(LocallyWrappedMetaInfoProvider):

    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    def _init_wrapped_meta_info_provider(self, parameters: dict) -> None:
        if 'url' not in parameters.keys():
            raise ValueError('No url provided for Http MetaInfoProvider')
        self._url = parameters['url']
        if 'supported_data_types' not in parameters.keys():
            raise ValueError('HttpMetaInfoProvider must receive supported data types as parameter')
        self._data_types = parameters['supported_data_types'].replace(' ', '').split(',')

    def provides_data_type(self, data_type: str) -> bool:
        for provided_data_type in self._data_types:
            if data_type == provided_data_type:
                return True
        return False

    def get_provided_data_types(self) -> List[str]:
        return self._data_types

    def encapsulates_data_type(self, data_type: str) -> bool:
        return False

    def _query_wrapped_meta_info_provider(self, query_string: str, local_data_set_meta_infos: List[DataSetMetaInfo]) \
            -> List[DataSetMetaInfo]:
        data_set_meta_infos = []
        queried_data_types = self.get_data_types_from_query_string(query_string)
        may_continue = False
        for data_type in queried_data_types:
            if data_type in self._data_types:
                may_continue = True
                break
        if not may_continue:
            return data_set_meta_infos
        try:
            request = requests.get(self._url, stream=True)
        except requests.ConnectionError:
            logging.warning('Could not retrieve meta information from {} due to a connection error.'.format(self._url))
            return data_set_meta_infos
        soup = BeautifulSoup(request.content, 'html5lib')
        links = soup.find_all('a')

        roi = self.get_roi_from_query_string(query_string)
        start_time = self.get_start_time_from_query_string(query_string)
        end_time = self.get_end_time_from_query_string(query_string)
        for data_type in queried_data_types:
            if data_type not in self._data_types:
                continue
            file_pattern = get_file_pattern(data_type)
            matcher = re.compile(file_pattern)
            available_files = [link['href'] for link in links if matcher.match(link['href']) is not None]
            for file in available_files:
                if is_valid_for(file, data_type, roi, start_time, end_time):
                    data_set_meta_info = get_data_set_meta_info(data_type, file)
                    if not self._is_provided_locally(data_set_meta_info, local_data_set_meta_infos):
                        data_set_meta_infos.append(data_set_meta_info)
        return data_set_meta_infos

    def _get_wrapped_parameters_as_dict(self) -> dict:
        parameters = {'url': self._url, 'supported_data_types': ','.join(self._data_types)}
        return parameters


class HttpMetaInfoProviderAccessor(MetaInfoProviderAccessor):

    @classmethod
    def name(cls) -> str:
        return _META_INFO_PROVIDER_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> HttpMetaInfoProvider:
        return HttpMetaInfoProvider(parameters)


class HttpFileSystem(LocallyWrappedFileSystem):

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    def _init_wrapped_file_system(self, parameters: dict) -> None:
        if 'url' not in parameters.keys():
            raise ValueError('No url provided for HttpFileSystem')
        self._url = parameters['url']
        if 'temp_dir' not in parameters.keys():
            raise ValueError('No valid temporal directory provided Http File System')
        if not os.path.exists(parameters['temp_dir']):
            os.makedirs(parameters['temp_dir'])
        self._temp_dir = parameters['temp_dir']

    def _get_from_wrapped(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        file_refs = []
        file_name = data_set_meta_info.identifier.split('/')[-1]
        url = '{}/{}'.format(self._url, file_name)
        logging.info(f"Attempting to download from {url}")
        success = self._download_url(url, self._temp_dir, file_name)
        if success:
            destination = os.path.join(self._temp_dir, file_name)
            file_refs.append(FileRef(destination, data_set_meta_info.start_time, data_set_meta_info.end_time,
                                     get_mime_type(file_name)))
            logging.info('Downloaded {}'.format(file_name))
        return file_refs

    def _download_url(self, url: str, destination_dir: str, file_name: str) -> bool:
        destination = os.path.join(destination_dir, file_name)
        try:
            request = requests.get(url, stream=True)
        except ConnectionError:
            logging.warning('Could not retrieve data from {} due to a connection error.'.format(self._url))
            return False
        content_type = urllib2.urlopen(url).info().get_content_type()
        if content_type == 'text/html':
            soup = BeautifulSoup(request.content, 'html5lib')
            links = soup.find_all('a')
            file_names = [link['href'] for link in links
                          if not link['href'].startswith('?') and not link['href'].startswith('/')]
            for file_name in file_names:
                self._download_url('{}/{}'.format(url, file_name), destination, file_name)
        elif request.ok:
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            logging.info('Downloading {}'.format(file_name))
            total_size_in_bytes = int(urllib2.urlopen(url).info()['Content-Length'])
            one_percent = total_size_in_bytes / 100
            downloaded_bytes = 0
            next_threshold = one_percent
            with open(destination, 'wb') as fp:
                for chunk in request.iter_content(chunk_size=1024):
                    if chunk:
                        fp.write(chunk)
                        downloaded_bytes += 1024
                        if downloaded_bytes > next_threshold:
                            stdout.write('\r{} %'.format(int(next_threshold / one_percent)))
                            stdout.flush()
                            next_threshold += one_percent
        return True

    def _notify_copied_to_local(self, data_set_meta_info: DataSetMetaInfo) -> None:
        full_path = '{}/{}'.format(self._temp_dir, data_set_meta_info.identifier)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

    def _get_wrapped_parameters_as_dict(self) -> dict:
        parameters = {'url': self._url, 'temp_dir': self._temp_dir}
        return parameters

    def clear_cache(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)


class HttpFileSystemAccessor(FileSystemAccessor):

    @classmethod
    def name(cls) -> str:
        return _FILE_SYSTEM_NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> HttpFileSystem:
        return HttpFileSystem(parameters)
