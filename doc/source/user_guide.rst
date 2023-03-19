==========
User Guide
==========

The MULTIPLY Data Access Component is supposed to be used via its Python API.
Therefore, most of this section will deal with the :ref:`ug_00`.
To see how to manually manipulate the data stores file, see :ref:`con_03`.
If you want to register a new data store from data that is saved on local disk, see :ref:`ug_03`.
Finally, if you find that the Data Access Component is missing functionality, you can extend it by :ref:`ug_04` or
:ref:`ug_05`.
When you have these two set up, you can create a new data store by editing the default data stores yaml file.

* implementing new file systems
* implementing new meta info providers
* implementing new data types

.. _ug_00:

Usage via the Python API
========================

This section gives an overview about how the Data Access Component can be used within Python.
The only component that is supposed to be used directly is the DataAccessComponent object.

.. _ug_01:

-------------------
DataAccessComponent
-------------------

.. autoclass:: multiply_data_access.data_access_component.DataAccessComponent
    :members:

.. _ug_02:

---------------
DataSetMetaInfo
---------------

.. autoclass:: multiply_data_access.data_access.DataSetMetaInfo
    :members:


.. _ug_03:

How to add new Local Data Stores
================================

You can add a new local data store via the Python API like this.
This will create a new data store consisting of a LocalFileSystem and a JsonMetaInfoProvider.

.. code-block:: console
    $ dac = DataAccessComponent()
    INFO:root:Read data store aws_s2
    INFO:root:Read data store cams
    INFO:root:Read data store emulators
    INFO:root:Read data store wv_emulator
    INFO:root:Read data store aster_dem
    INFO:root:Read data store modis_mcd43a1
    INFO:root:Read data store S2L2
    INFO:root:Scanning local file system, not remote
    INFO:root:Scanning local file system, not remote
    INFO:root:Scanning local file system, not remote
    INFO:root:Scanning local file system, not remote
    INFO:root:Scanning local file system, not remote
    INFO:root:Scanning local file system, not remote
    $ dac.create_local_data_store(base_dir='/user/dir/', , meta_info_file='/user/dir/meta_store.json', base_pattern='MM/dt/', id='cgfsvt', supported_data_types='TYPE_A,TYPE_B')
    INFO:root:Added local data store cgfsvt


All parameters are optional.
The default for the base directory is the ``.multiply``-folder in the user's home directory.
The base directory will be checked for any pre-existing data.
This data will be registered in the store if it is of any of the supported data types.
If you do not specify the supported data types, the Data Access Component will determine these from the entries in the
JSON metainfo file.
If no metadata file is provided, the data types will be determined from the data in the base directory.
If finally no data can be found there, the data store is not created.

Implementing new Data Stores
============================

If you need to create a completely new data store, you will probably need to implement both a new File System and a new
Meta Info Provider (we advise to check whether you can re-use existing File Systems and Meta Info Providers).
This section is a guideline on how to do so.
It is recommended to consider :ref:`bc_00` first.

.. _ug_04:

------------------------------
Implementing a new File System
------------------------------

The basic decision is whether the file system shall be wrapped by a local file system or not.
The wrapping functionality is provided by the ``LocallyWrappedFileSystem`` in ``locally_wrapped_data_access.py``.
Choose this if you want to access remote data but don't want to bother with how to organize the data on the local disk.

Implementing a Non-Locally Wrapped File System
----------------------------------------------

For this, you need to adher to the interfaces ``FileSystemAccessor`` and ``FileSystem`` defined in ``data_access.py``.
The following lists the methods of the interface that need to be implemented:

.. autoclass:: multiply_data_access.data_access.FileSystemAccessor
    :members:

``name``: Shall return the name of the file system.

``create_from_parameters``: Will receive a list of parameters and create a file system by handing these in as the
initialization parameters.
Shall correspond to the dictionary handed out by FileSystem's ``get_parameters_as_dict``.

.. autoclass:: multiply_data_access.data_access.FileSystem
    :members: name, get, get_parameters_as_dict, can_put, put, remove, scan

``name``: Shall simply return the name of the file system.
This will serve as identifier.

``get``: From a list of :ref:`ug_02`s, this returns FileRefs to the data that is ready to be accessed, i.e.,
is provided locally.
This part would perform a download if necessary.

``get_parameters_as_dict``: This will return the parameters that are needed to reconstruct the file system.
The parameters will eventually be written to the data stores file.
Shall correspond to the dictionary handed in by the FileSystemAccessors's ``create_from_parameters``.

``can put``: Shall return true when the Data Access Component can add data to the file system.

``put``: Will copy the data located from the url to the file system and update the data set meta info.
You might throw a User Warning here if you do not support this operation.
You can use the identifier of the data set meta info to later relocate the file on the file system more easily.

``remove``: Shall remove the file identified by the data set meta info from the file system.
You might throw a User Warning here if you do not support this operation.

``scan``: Retrieves data set meta infos for all data that is found on the file system.
This expects to find the data that is directly, i.e, locally available.

To later have the file system available in the data access component,
you need to register it in the ``setup.py`` of your python package.
The registration should look like this:

.. code-block:: console

setup(name='my-multiply-data-access-extension',
      version=1.0,
      packages=['my_multiply_package'],
      entry_points={
          'file_system_plugins': [
              'my_file_system = my_multiply_package:my_file_system.MyFileSystemAccessor'
          ],
      },
      )


Implementing a Locally Wrapped File System
------------------------------------------

A locally wrapped file system requires a FileSystemAccessor that should be defined as above.
The ``LocallyWrappedFileSystem`` base class already implements some of the methods,
but puts up other method stubs that need to be implemented.
Note that all these methods are private.

Already implemented methods are:
* get
* get_parameters_as_dict
* can_put
* put
* remove
* scan
So, actually the only method from the ``FileSystem`` interface that still needs implementing is ``name``.

.. autoclass:: multiply_data_access.locally_wrapped_data_access.LocallyWrappedFileSystem
    :members: _init_wrapped_file_system, _get_from_wrapped, _notify_copied_to_local, _get_wrapped_parameters_as_dict

``_init_wrapped_file_system``: This method is called right after the creation of the object.
Implement it to initialize the file system with parameters.
Shall correspond to the dictionary handed out by ``_get_wrapped_parameters_as_dict``.
``_get_from_wrapped``: Like ``get`` from the File System: Will retrieve FileRefs to data.
This data has to be provided locally, so any downloading has to be performed here.
``_notify_copied_to_local``: Informs the File System that the data desidnated by the data set meta info has been put to
the local file system.
You do not have to do anythin here, but in case you have downloaded the data to a temporary directory,
this is a good time to delete it from there.
``_get_wrapped_parameters_as_dict``: Similar to the ``FileSystem``'s ``get_parameters_as_dict``, this method will return
the required initialization parameters in the form of a dictionary.
Shall correspond to the dictionary handed in to ``_init_wrapped_file_system``.


.. _ug_05:

-------------------------------------
Implementing a new Meta Info Provider
-------------------------------------

In many cases when you require your own dedicated File System, you will want to add a Meta Info Provider.
As for the File System, you also have the choice to create a locally wrapped version of it or not.
The wrapping functionality is provided by the ``LocallyWrappedMetaInfoProvider`` in ``locally_wrapped_data_access.py``.
Choose this if you want to provide information about remotely stored data and keep it separated from information
about data from this source that has already been downloaded.

Implementing a Non-Locally Wrapped Meta Info Provider
-----------------------------------------------------

To implement a regular Meta Info Provider, you need to create realizations of the interfaces
``MetaInfoProviderAccessor`` and ``MetaInfoProvider`` defined in ``data_access.py``.
The MetaInfoProviderAccessor is required by the DataAccessComponent so that MetaInfoProviders can be registered and
created.
The following lists the methods of the MetaInfoProviderAccessor interface that need to be implemented:

.. autoclass:: multiply_data_access.data_access.MetaInfoProviderAccessor
    :members:

``name``: Shall return the name of the meta info provider.

``create_from_parameters``: Will receive a list of parameters and create a meta infor provider by handing the
parameters in as the initialization parameters.
Shall correspond to the dictionary handed out by the MetaInfoProvider's ``_get_parameters_as_dict``.

The methods to be implemented for the MetaInfoProvider are:

.. autoclass:: multiply_data_access.data_access.MetaInfoProvider
    :members: name, query, provides_data_type, get_provided_data_types, _get_parameters_as_dict, can_update, update,
        remove,
        get_all_data

``name``: Shall simply return the name of the meta info provider.
This will serve as identifier.

``query``: Evaluates a query string and returns a list of data set meta infos about available data that fulfils the
query.
A query string consists of a geometry in the form of a wkt string, a start time in UTC format,
an end time in UTC format, and a comma-separated list of data types.

``provides_data_type``: True, if the meta info provider is apt for this data.
Returning true here does not necessarilyy mean that data of this type is currently stored.

``get_provided_data_types``: Returns a list of all data types that this meta info provider supports.

``_get_parameters_as_dict``: A private method that will return the parameters that are needed to reconstruct
the meta info provider.
The parameters will eventually be written to the data stores file.
Shall correspond to the dictionary handed in by the MetaInfoProviderAccessors's ``create_from_parameters``.

``can_update``: Shall return true when entries about data available on the file system can be added to this
meta info provider.

``update``: Hands in a data set that has been put to the file system.
The meta info provider is expected to store this information and retrieve it when it meets an incoming query.
If this is not implemented, make sure that ``can_update`` returns false.


``remove``: Shall remove the entry associated with the data set meta info from the provider's registry.
If this is not implemented, make sure that ``can_update`` returns false.

``get_all_data``: Shall return data set meta infos about all available data.

As for the File System, the Meta Info Provider needs to be registered in the ``setup.py`` of the python package to
make it available for the data access component.
The registration should look like this:

.. code-block:: console

setup(name='my-multiply-data-access-extension',
      version=1.0,
      packages=['my_multiply_package'],
      entry_points={
          'meta_info_provider_plugins': [
              'my_meta_info_provider = my_multiply_package:my_meta_info_provider.MyMetaInfoProviderAccessor'
          ],
      },
      )

Implementing a Locally Wrapped Meta Info Provider
-------------------------------------------------

A locally wrapped meta info provider is a special type of meta info provider and requires a MetaInfoProviderAccessor
that should be defined as above.
The ``LocallyWrappedMetaInfoProvider`` base class already implements some of the methods,
but puts up other method stubs that need to be implemented.
Note that all these methods are private and are never to be called from another class.

Already implemented methods are:
* query
* _get_parameters_as_dict
* can_update
* update
* remove
* get_all_data
So, the only methods from the ``MetaInfoProvider`` interface that still needs implementing are ``name``,
``provides_data_type``, and ``get_provided_data_types``.

.. autoclass:: multiply_data_access.locally_wrapped_data_access.LocallyWrappedFileSystem
    :members: _init_wrapped_meta_info_provider, _query_wrapped_meta_info_provider, _get_wrapped_parameters_as_dict

``_init_wrapped_meta_info_provider``: This method is called right after the creation of the object.
Implement it to initialize the meta info provider with parameters.
Shall correspond to the dictionary handed out by ``_get_wrapped_parameters_as_dict``.

``_query_wrapped_meta_info_provider``: Evaluates a query string and returns a list of data set meta infos about
available data that fulfils the query.
A query string consists of a geometry in the form of a wkt string, a start time in UTC format,
an end time in UTC format, and a comma-separated list of data types.

``_get_wrapped_parameters_as_dict``: Similar to the ``FileSystem``'s ``get_parameters_as_dict``, this method will return
the required initialization parameters in the form of a dictionary.
Shall correspond to the dictionary handed in to ``_init_wrapped_file_system``.
