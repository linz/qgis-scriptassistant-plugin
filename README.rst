============================
QGIS Script Assistant Plugin
============================

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :target: https://github.com/linz/qgis-importimage-plugin/blob/master/LICENSE

.. image:: https://travis-ci.com/linz/qgis-scriptassistant-plugin.svg?token=K4ECbFVBqQndQscY6xjY&branch=master
    :target: https://travis-ci.org/linz/qgis-scriptassistant-plugin

This is a QGIS plugin with three helper tools for QGIS development purposes:

* Reload scripts into QGIS from any existing directory
* Run tests within QGIS in a way that makes them configurable for local and travis-ci testing without any manual amendments
* Add all of the test data referred to in those tests with a click

These tools make life easier if you:

* store user scripts in a .git repository and need to load development versions into QGIS Processing (different use case to the QGIS Resource Sharing plugin which allows sharing of finished scripts)
* want to edit scripts and tests in your text editor of choice, and easily reload / run in QGIS
* want to use ``__file__`` - this doesn't work in the QGIS Python Console but does work with the provided test runner

Notes:
======

* Scripts named in the format ``test_x.py`` must be within the test directory - subdirectories are ignored.
* The ``tests_x.py`` script must have a ``run_tests`` function in order for tests to be called.
* Only .shp (shapefile) format test data is supported.
