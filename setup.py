#!/usr/bin/env python

from setuptools import setup

requirements = [
    'nose',
    'shapely',
    'pyyaml'
]

__version__ = None
with open('multiply_data_access/version.py') as f:
    exec(f.read())

setup(name='multiply-data-access',
      version=__version__,
      description='MULTIPLY Data Access',
      author='MULTIPLY Team',
      packages=['multiply_data_access'],
      entry_points={
          'file_system_plugins': [
              'local_file_system = multiply_data_access:local_file_system.LocalFileSystemAccessor',
          ],
          'meta_info_provider_plugins': [
              'json_meta_info_provider = multiply_data_access:json_meta_info_provider.JsonMetaInfoProviderAccessor',
          ],
      },
      install_requires=requirements
)
