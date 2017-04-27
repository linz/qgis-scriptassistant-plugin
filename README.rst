============================
QGIS Script Assistant Plugin
============================
   
.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :target: https://github.com/linz/qgis-importimage-plugin/blob/master/LICENSE

This is a QGIS plugin with two helper tools for QGIS development purposes:

* enables scripts to be reloaded into QGIS from any existing directory
* enable tests to be run within QGIS in a way that makes them configurable for local and travis-ci testing without any manual amendments

These tools make life easier if you:

* store user scripts in a .git repository and need to load development versions into QGIS Processing (different use case to the QGIS Resource Sharing plugin which allows sharing of finished scripts)
* want to edit scripts and tests in your text editor of choice, and easily reload / run in QGIS
* want to use ``__file__`` to get the relative location of test data - this doesn't work in the QGIS Python Console but does work with the provide test runner

Notes:
======

* There must be a ``tests/`` dir within the configured script folder to use these tools.
* Scripts named in the format ``test_x.py`` must be within this directory - subdirectories are ignored.
* The ``tests_x.py`` script must have a ``run_tests`` function in order for tests to be called.

TODO:
=====

* Add tests
* Improve restrictions listed above
* Retain recent folders or add folder management to the configuration
* Separate folder configuration from script reload functionality
* Store test configurations, rather than just **all** or individual
