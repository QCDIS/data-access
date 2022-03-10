# coding=UTF-8
"""
Description
===========

This module contains the MULTIPLY data access API.
"""
import pyproj

from abc import ABCMeta, abstractmethod
from typing import List, Sequence, Optional
from datetime import datetime
from multiply_core.util import FileRef, are_times_equal, are_polygons_almost_equal, get_time_from_string, \
    reproject_to_wgs84
from multiply_core.observations import differs_by_name, get_relative_path
from shapely.wkt import loads
from shapely.geometry import Polygon

__author__ = 'Alexander Löw (Ludwig Maximilians-Universität München), ' \
             'Tonio Fincke (Brockmann Consult GmbH)'


class DataSetMetaInfo(object):
    """
    A representation of meta information about a data set. To be retrieved from a query on a MetaInfoProvider or
    DataStore.
    """

    def __init__(self, coverage: str, start_time: Optional[str], end_time: Optional[str], data_type: str,
                 identifier: str, referenced_data: Optional[str] = None):
        self._coverage = coverage
        self._start_time = start_time
        self._end_time = end_time
        self._data_type = data_type
        self._identifier = identifier
        self._referenced_data = referenced_data

    def __repr__(self):
        return 'Data Set:\n' \
               '  Id: {}, \n' \
               '  Type: {}, \n' \
               '  Start Time: {}, \n' \
               '  End Time: {}, \n' \
               '  Coverage: {}\n'.format(self.identifier, self.data_type, self.start_time, self.end_time, self.coverage)

    @property
    def start_time(self) -> Optional[str]:
        """The dataset's start time. Can be none."""
        return self._start_time

    @property
    def end_time(self) -> Optional[str]:
        """The dataset's end time. Can be none."""
        return self._end_time

    @property
    def coverage(self) -> str:
        """The dataset's spatial coverage, given as WKT string."""
        return self._coverage

    @property
    def data_type(self) -> str:
        """The type of the dataset."""
        return self._data_type

    @property
    def identifier(self) -> str:
        """An identifier so that the data set can be found on the Data Store's File System."""
        return self._identifier

    @property
    def referenced_data(self) -> Optional[str]:
        """A list of additional files that are referenced by this data set. Can be none."""
        return self._referenced_data

    def equals(self, other: object) -> bool:
        """Checks whether two data set meta infos are equal. Does not check for referenced data sets. Only checks for
        the identifier if two different items must always carry different names."""
        equals = self.equals_except_data_type(other) and self._data_type == other.data_type
        if equals and differs_by_name(self._data_type):
            equals = self._identifier.split('/')[-1] == other.identifier.split('/')[-1]
            relative_path = get_relative_path(self._identifier, self._data_type)
            other_relative_path = get_relative_path(other.identifier, other.data_type)
            equals = equals and relative_path == other_relative_path
        return equals

    def equals_except_data_type(self, other: object) -> bool:
        """Checks whether two data set meta infos are equal, except that they may have the same data type.
        Does not check the identifier or referenced data sets!"""
        return type(other) == DataSetMetaInfo and \
            are_times_equal(self._start_time, other.start_time) and \
            are_times_equal(self._end_time, other.end_time) and \
            are_polygons_almost_equal(self.coverage, other.coverage)


class FileSystem(metaclass=ABCMeta):
    """
    An abstraction of a file system on which data sets are physically stored
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """
        :return: The name of the file system implementation.
        """

    @abstractmethod
    def get(self, data_set_meta_info: DataSetMetaInfo) -> Sequence[FileRef]:
        """Retrieves a sequence of 'FileRef's."""

    def get_as_dict(self) -> dict:
        """
        :return: A representation of this file system as dictionary.
        """
        return {'type': self.name(),
                'parameters': self.get_parameters_as_dict()}

    @abstractmethod
    def get_parameters_as_dict(self) -> dict:
        """
        :return: The parameters of this file system as dict
        """

    @abstractmethod
    def can_put(self) -> bool:
        """
        :return: True, if data can be put into this file system.
        """

    @abstractmethod
    def put(self, from_url: str, data_set_meta_info: DataSetMetaInfo) -> DataSetMetaInfo:
        """Adds a data set to the file system by copying it from the given url to the expected location within
        the file system. Returns an updated data set meta info."""

    @abstractmethod
    def remove(self, data_set_meta_info: DataSetMetaInfo):
        """Removes all data sets from the file system that are described by the data set meta info"""

    @abstractmethod
    def scan(self) -> Sequence[DataSetMetaInfo]:
        """Retrieves a sequence of data set meta informations of all file refs found in the file system."""

    @abstractmethod
    def clear_cache(self):
        """
        Removes any cached data that this file system might hold.
        :return:
        """


class FileSystemAccessor(metaclass=ABCMeta):

    @classmethod
    def name(cls) -> str:
        """The name of the file system implementation."""

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> FileSystem:
        """Returns a FileSystem object."""


class MetaInfoProvider(metaclass=ABCMeta):
    """
    An abstraction of a provider that contains meta information about the files provided by a data store.
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """The name of the file system implementation."""

    @abstractmethod
    def query(self, query_string: str) -> List[DataSetMetaInfo]:
        """
        Processes a query and retrieves a result. The result will consist of all the data sets that satisfy the query.
        :return: A list of meta information about data sets that fulfill the query.
        """

    @abstractmethod
    def query_local(self, query_string: str) -> List[DataSetMetaInfo]:
        """
        Processes a query and retrieves a result. The result will consist of all the data sets that satisfy the query
        that do not require to be downloaded.
        :return: A list of meta information about data sets that fulfill the query.
        """

    @abstractmethod
    def query_non_local(self, query_string: str) -> List[DataSetMetaInfo]:
        """
        Processes a query and retrieves a result. The result will consist of all the data sets that satisfy the query
        that must be downloaded first.
        :return: A list of meta information about data sets that fulfill the query.
        """

    @abstractmethod
    def provides_data_type(self, data_type: str) -> bool:
        """
        Whether the meta info provider provides access to data of the queried type
        :param data_type: A string labelling the data
        :return: True if data of that type can be requested from the meta info provider
        """

    @abstractmethod
    def get_provided_data_types(self) -> List[str]:
        """
        :return: A list of the data types provided by this data store.
        """

    @abstractmethod
    def encapsulates_data_type(self, data_type: str) -> bool:
        """
        Whether the meta info provider provides encapsulated access to data of the queried type. Data access is
        considered encapsulated when the data is not provided directly from the meta info provider, but indirectly by
        requesting a provided data type which in some form relies on the encapsulated data.
        :param data_type: A string labelling the data
        :return: True if data of that type is encapsulated by one of the meta infor provider's provided data types.
        """

    @staticmethod
    def get_roi_from_query_string(query_string: str) -> Optional[Polygon]:
        split_query_string = query_string.split(';')
        roi_as_wkt = split_query_string[0]
        if roi_as_wkt == '':
            return None
        if len(split_query_string) == 4:
            roi = loads(roi_as_wkt)
        else:
            roi_grid = split_query_string[4]
            roi = reproject_to_wgs84(roi_as_wkt, roi_grid)
            roi = loads(roi)
        # todo also allow MultiPolygons
        if not isinstance(roi, Polygon):
            raise ValueError('ROI must be a polygon')
        return roi

    @staticmethod
    def get_start_time_from_query_string(query_string: str) -> Optional[datetime]:
        start_time_as_string = query_string.split(';')[1]
        return get_time_from_string(start_time_as_string, False)

    @staticmethod
    def get_end_time_from_query_string(query_string: str) -> Optional[datetime]:
        end_time_as_string = query_string.split(';')[2]
        return get_time_from_string(end_time_as_string, True)

    @staticmethod
    def get_data_types_from_query_string(query_string: str) -> List[str]:
        data_types = query_string.split(';')[3].split(',')
        if len(data_types) == 1 and data_types[0] == '':
            return []
        for i, data_type in enumerate(data_types):
            data_types[i] = data_type.strip()
        return data_types

    def get_as_dict(self) -> dict:
        """
        :return: A representation of this file system as dictionary.
        """
        return {'type': self.name(),
                'parameters': self._get_parameters_as_dict()}

    @abstractmethod
    def _get_parameters_as_dict(self) -> dict:
        """
        :return: The parameters of this file system as dict
        """

    def notify_got(self, data_set_meta_info: DataSetMetaInfo) -> None:
        """Informs the meta info provider that the data set has been retrieved from the file system."""
        pass

    @abstractmethod
    def can_update(self) -> bool:
        """
        :return: true if this meta info provider can be updated.
        """

    @abstractmethod
    def update(self, data_set_meta_info: DataSetMetaInfo):
        """Adds information about the data set to its internal registry."""

    @abstractmethod
    def remove(self, data_set_meta_info: DataSetMetaInfo):
        """Removes information about this data set from its internal registry."""

    @abstractmethod
    def get_all_data(self) -> Sequence[DataSetMetaInfo]:
        """Returns all available data set meta infos."""


class MetaInfoProviderAccessor(metaclass=ABCMeta):

    @classmethod
    def name(cls) -> str:
        """The name of the meta info provider implementation."""

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> MetaInfoProvider:
        """Returns a MetaInfoProvider object."""
