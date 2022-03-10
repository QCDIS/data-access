from .data_access import DataSetMetaInfo, MetaInfoProvider, MetaInfoProviderAccessor
from multiply_core.util import get_time_from_string
from typing import List, Optional, Sequence
from shapely.wkt import loads
import json
import os

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

_NAME = 'JsonMetaInfoProvider'


class JsonMetaInfoProvider(MetaInfoProvider):
    """
    A MetaInfoProvider that retrieves its meta information from a JSON file.
    """

    def __init__(self, path_to_json_file: str, supported_data_types: Optional[str]):
        self.path_to_json_file = path_to_json_file
        self.provided_data_types = None
        if supported_data_types is not None:
            self.provided_data_types = supported_data_types.split(',')
        if not os.path.exists(path_to_json_file):
            relative_path = '/'.join(path_to_json_file.split('/')[:-1])
            if not os.path.exists(relative_path):
                os.makedirs(relative_path)
            with open(path_to_json_file, 'w') as json_file:
                json.dump({'data_sets': []}, json_file, indent=2)
        with open(path_to_json_file, "r") as json_file:
            self.data_set_infos = json.load(json_file)
            self._init_provided_data_types_and_sets()

    @classmethod
    def name(cls) -> str:
        """The name of the file system implementation."""
        return _NAME

    def query(self, query_string: str) -> List[DataSetMetaInfo]:
        roi = self.get_roi_from_query_string(query_string)
        query_start_time = self.get_start_time_from_query_string(query_string)
        query_end_time = self.get_end_time_from_query_string(query_string)
        data_types = self.get_data_types_from_query_string(query_string)
        data_set_meta_infos = []
        for data_set_info in self.data_set_infos['data_sets']:
            if data_set_info.get('coverage') is not None and roi is not None:
                data_set_coverage = loads(data_set_info.get('coverage'))
                if not roi.intersects(data_set_coverage):
                    continue
            if query_start_time is not None and data_set_info.get('start_time') is not None:
                data_set_start_time = get_time_from_string(data_set_info.get('start_time'), False)
                if query_end_time < data_set_start_time:
                    continue
            if query_end_time is not None and data_set_info.get('end_time') is not None:
                data_set_end_time = get_time_from_string(data_set_info.get('end_time'), True)
                if data_set_end_time < query_start_time:
                    continue
            if data_set_info.get('data_type') in data_types:
                data_set_meta_info = DataSetMetaInfo(coverage=data_set_info.get('coverage'),
                                                     start_time=data_set_info.get('start_time'),
                                                     end_time=data_set_info.get('end_time'),
                                                     data_type=data_set_info.get('data_type'),
                                                     identifier=data_set_info.get('name'))
                data_set_meta_infos.append(data_set_meta_info)
        return data_set_meta_infos

    def query_local(self, query_string: str) -> List[DataSetMetaInfo]:
        return self.query(query_string)

    def query_non_local(self, query_string: str) -> List[DataSetMetaInfo]:
        return []

    def provides_data_type(self, data_type: str):
        return data_type in self.provided_data_types

    def encapsulates_data_type(self, data_type: str) -> bool:
        return False

    def get_provided_data_types(self) -> List[str]:
        return self.provided_data_types

    def can_update(self) -> bool:
        return True

    def update(self, data_set_meta_info: DataSetMetaInfo):
        data_type = data_set_meta_info.data_type
        if data_type is None:
            raise ValueError('Data must have Data Type')
        if not self.provides_data_type(data_type):
            raise ValueError('Data Type {} is not provided.'.format(data_type))
        if self._contains(data_set_meta_info):
            return
        data_set_info = {}
        if data_set_meta_info.coverage is not None and loads(data_set_meta_info.coverage) is not None:
            data_set_info['coverage'] = data_set_meta_info.coverage
        data_set_start_time = None
        if data_set_meta_info.start_time is not None:
            data_set_start_time = get_time_from_string(data_set_meta_info.start_time, False)
        data_set_end_time = None
        if data_set_meta_info.end_time is not None:
            data_set_end_time = get_time_from_string(data_set_meta_info.start_time, True)
        if data_set_start_time is not None and data_set_end_time is not None and data_set_start_time > data_set_end_time:
            raise ValueError('start time must not be later than end time')
        if data_set_start_time is not None:
            data_set_info['start_time'] = data_set_meta_info.start_time
        if data_set_end_time is not None:
            data_set_info['end_time'] = data_set_meta_info.end_time
        data_set_info['data_type'] = data_type
        data_set_info['name'] = data_set_meta_info.identifier
        self.data_set_infos['data_sets'].append(data_set_info)
        self._update_json_file()

    def _contains(self, data_set_meta_info: DataSetMetaInfo):
        #todo consider making this an interface function
        for data_set_info in self.data_set_infos['data_sets']:
            if data_set_info.get('coverage') != data_set_meta_info.coverage:
                continue
            if data_set_info.get('start_time') != data_set_meta_info.start_time:
                continue
            if data_set_info.get('end_time') != data_set_meta_info.end_time:
                continue
            if data_set_info.get('data_type') != data_set_meta_info.data_type:
                continue
            if data_set_info.get('name') != data_set_meta_info.identifier:
                continue
            return True
        return False

    def remove(self, data_set_meta_info: DataSetMetaInfo):
        for data_set_info in self.data_set_infos['data_sets']:
            if data_set_info.get('coverage') != data_set_meta_info.coverage:
                continue
            if data_set_info.get('start_time') != data_set_meta_info.start_time:
                continue
            if data_set_info.get('end_time') != data_set_meta_info.end_time:
                continue
            if data_set_info.get('data_type') != data_set_meta_info.data_type:
                continue
            if data_set_info.get('name') != data_set_meta_info.identifier:
                continue
            self.data_set_infos['data_sets'].remove(data_set_info)
        self._update_json_file()

    def _update_json_file(self):
        with open(self.path_to_json_file, "w") as json_file:
            json.dump(self.data_set_infos, json_file, indent=2)

    def _init_provided_data_types_and_sets(self):
        if self.provided_data_types is not None and len(self.provided_data_types) > 0:
            removed = False
            for data_set_info in self.data_set_infos['data_sets']:
                if data_set_info.get('data_type') not in self.provided_data_types:
                    self.data_set_infos['data_sets'].remove(data_set_info)
                    removed = True
            if removed:
                self._update_json_file()
        else:
            self.provided_data_types = []
            for data_set_info in self.data_set_infos['data_sets']:
                if data_set_info.get('data_type') not in self.provided_data_types:
                    self.provided_data_types.append(data_set_info.get('data_type'))

    def get_all_data(self) -> Sequence[DataSetMetaInfo]:
        data_set_meta_infos = []
        for data_set_info in self.data_set_infos['data_sets']:
            data_set_meta_info = DataSetMetaInfo(coverage=data_set_info.get('coverage'),
                                                 start_time=data_set_info.get('start_time'),
                                                 end_time=data_set_info.get('end_time'),
                                                 data_type=data_set_info.get('data_type'),
                                                 identifier=data_set_info.get('name'))
            data_set_meta_infos.append(data_set_meta_info)
        return data_set_meta_infos

    def _get_parameters_as_dict(self):
        supported_data_types = ','.join(self.provided_data_types)
        return {'path_to_json_file': self.path_to_json_file, 'supported_data_types': supported_data_types}


class JsonMetaInfoProviderAccessor(MetaInfoProviderAccessor):

    @classmethod
    def name(cls) -> str:
        """The name of the file system implementation."""
        return _NAME

    @classmethod
    def create_from_parameters(cls, parameters: dict) -> JsonMetaInfoProvider:
        if 'path_to_json_file' not in parameters.keys():
            raise ValueError('Required parameter path_to_json_file is missing')
        supported_data_types = None
        if 'supported_data_types' in parameters.keys():
            supported_data_types = parameters['supported_data_types']
        return JsonMetaInfoProvider(path_to_json_file=parameters['path_to_json_file'],
                                    supported_data_types=supported_data_types)