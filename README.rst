============================
QGIS Script Assistant Plugin
============================

.. image:: https://img.shields.io/badge/QGIS%20Python%20Plugin%20Repository-v0.4.1-brightgreen.svg
    :target: https://plugins.qgis.org/plugins/scriptassistant/

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :target: https://github.com/linz/qgis-scriptassistant-plugin/blob/master/LICENSE

.. image:: https://travis-ci.org/linz/qgis-scriptassistant-plugin.svg?branch=master
    :target: https://travis-ci.org/linz/qgis-scriptassistant-plugin

.. image:: https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat&maxAge=86400
    :target: http://qgis-script-assistant-plugin.readthedocs.io/en/latest/?badge=latest

This is a QGIS plugin with three helper tools for QGIS development purposes:

* Reload processing user scripts into QGIS from any existing directory
* Run tests within QGIS in a way that makes them configurable for local and travis-ci testing without any manual amendments
* Add all of the test data referred to in those tests with a click

These tools make life easier if you:

* store user scripts in a .git repository and need to load development versions into QGIS processing (different use case to the QGIS Resource Sharing plugin which allows sharing of finished scripts)
* want to edit scripts and tests in your text editor of choice, and easily reload / run in QGIS
* want to use ``__file__`` - this doesn't work in the QGIS Python Console but does work with the provided test runner

Installation
============

The plugin can be installed in QGIS through the QGIS Official Plugin Repository.

To install it for development purposes, clone this repository and then symlink the ``/scriptassistant`` dir to ``/$user/.qgis2/python/plugins/scriptassistant``.

Documentation
=============

See the full docs on `readthedocs <http://qgis-script-assistant-plugin.readthedocs.io/en/latest/index.html>`_.

Tests
=====

On installation, the plugin is configured to test itself. Click the Test Scripts button to test.

Limitations
===========

* Scripts named in the format ``test_x.py`` must be within the test directory - subdirectories are ignored.
* The ``tests_x.py`` script must have a ``run_tests`` function in order for tests to be called.
* Only ``.shp`` (shapefile) format test data is supported.
