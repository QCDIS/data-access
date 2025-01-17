#!/usr/bin/env python

from setuptools import setup

import os


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


on_rtd = os.environ.get('READTHEDOCS') == 'True'
if on_rtd:
    requirements = ['mock']
else:
    requirements = []
requirements = []

__version__ = None
with open('multiply_data_access/version.py') as f:
    exec(f.read())

setup(
    name='multiply-data-access',
    version=__version__,
    description='MULTIPLY Data Access',
    author='MULTIPLY Team',
    packages=['multiply_data_access'],
    install_requires=[],
    package_data={
        'multiply_data_access': ['*.yaml']
    },
    entry_points={
        'file_system_plugins': [
            'local_file_system = multiply_data_access:local_file_system.LocalFileSystemAccessor',
            'aws_s2_file_system = multiply_data_access:aws_s2_file_system.AwsS2FileSystemAccessor',
            'lpdaac_file_system = multiply_data_access:lpdaac_data_access.LpDaacFileSystemAccessor',
            'http_file_system = multiply_data_access:general_remote_access.HttpFileSystemAccessor',
            'vrt_file_system = multiply_data_access:vrt_data_access.VrtFileSystemAccessor',
            'mundi_file_system = multiply_data_access:mundi_data_access.MundiObsFileSystemAccessor',
            'mundi_rest_file_system = multiply_data_access:mundi_data_access.MundiRestFileSystemAccessor',
            'scihub_file_system = multiply_data_access:scihub_data_access.SciHubFileSystemAccessor'
        ],
        'meta_info_provider_plugins': [
            'json_meta_info_provider = multiply_data_access:json_meta_info_provider.JsonMetaInfoProviderAccessor',
            'aws_s2_meta_info_provider = '
            'multiply_data_access:aws_s2_meta_info_provider.AwsS2MetaInfoProviderAccessor',
            'lpdaac_meta_info_provider = '
            'multiply_data_access:lpdaac_data_access.LpDaacMetaInfoProviderAccessor',
            'http_meta_info_provider = multiply_data_access:general_remote_access.HttpMetaInfoProviderAccessor',
            'vrt_meta_info_provider = multiply_data_access:vrt_data_access.VrtMetaInfoProviderAccessor',
            'locally_wrapped_mundi_meta_info_provider = '
            'multiply_data_access:mundi_data_access.LocallyWrappedMundiMetaInfoProviderAccessor',
            'mundi_meta_info_provider = multiply_data_access:mundi_data_access.MundiMetaInfoProviderAccessor',
            'scihub_meta_info_provider = multiply_data_access:scihub_data_access.SciHubMetaInfoProviderAccessor'
        ],
    }
)
