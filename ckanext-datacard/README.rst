.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org/mayureshkunjir/ckanext-datacard.svg?branch=master
    :target: https://travis-ci.org/mayureshkunjir/ckanext-datacard

.. image:: https://coveralls.io/repos/mayureshkunjir/ckanext-datacard/badge.svg
  :target: https://coveralls.io/r/mayureshkunjir/ckanext-datacard

.. image:: https://img.shields.io/pypi/v/ckanext-datacard.svg
    :target: https://pypi.org/project/ckanext-datacard/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/ckanext-datacard.svg
    :target: https://pypi.org/project/ckanext-datacard/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/status/ckanext-datacard.svg
    :target: https://pypi.org/project/ckanext-datacard/
    :alt: Development Status

.. image:: https://img.shields.io/pypi/l/ckanext-datacard.svg
    :target: https://pypi.org/project/ckanext-datacard/
    :alt: License

=============
ckanext-datacard
=============

- Builds data cards (a set of rich metadata) associated to each dataset as it is uploaded to CKAN.
- Enables browsing, searching, visualizing, and comparing datasets through data cards.


------------
Requirements
------------

Tested on CKAN version 2.8.4


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-datacard:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-datacard Python package into your virtual environment::

     pip install ckanext-datacard

3. Add ``datacard`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config settings
---------------

1. Datacard metrics to be used as facets for searching. 
   The directory contains a file for each type of datasets. Supported types include [mltype]. 
   Source contains an example file: <https://github.com/qcri/datacard-ckan/blob/master/ckanext-datacard/ckanext/datacard/config/facets/mltype>

       ckan.datacard.facetsdict = <path to directory containing facets configuration> 


----------------------
Developer installation
----------------------

To install ckanext-datacard for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/mayureshkunjir/ckanext-datacard.git
    cd ckanext-datacard
    pip install -r requirements.txt
    pip install -r dev-requirements.txt
    python setup.py develop

-----
Tests
-----

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.datacard --cover-inclusive --cover-erase --cover-tests


----------------------------------------
Releasing a new version of ckanext-datacard
----------------------------------------

ckanext-datacard should be available on PyPI as https://pypi.org/project/ckanext-datacard.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Make sure you have the latest version of necessary packages::

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version::

       python setup.py sdist bdist_wheel && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI::

       twine upload dist/*

5. Commit any outstanding changes::

       git commit -a

6. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags
