==========
Change Log
==========

All notable changes to this project will be documented in this file.

Unreleased
==========

Added
-----

 * A final summary of the test results is printed to the QGIS Python Console after all testing

Changed
-------

 * Subfolders are now included in test discovery

Removed
-------

 * The option to run plugin tests with a delay and repaint has been removed due to inconsistent behaviour

Fixed
-----

 * Now handles test directories that were valid when configured but were later moved or deleted

0.4.1 - 2017-07-27
==================

Changed
-------

 * More thorough documentation added

0.4.0 - 2017-07-24
==================

Added
-----

 * Save confirmation if settings dialog closed with unsaved settings
 * Directory validation and handling for missing dirs
 * Documentation via readthedocs

Changed
-------

 * Using plugin specific Settings instead of using QGIS Settings
 * Improved self testing

0.3.0 - 2017-05-19
==================

Added
-----

 * New Add Test Data toolbar button - checks tests for .shp and adds these to the map
 * Can now save and manage testing configurations via Settings
 * Option to toggle reload()
 * Option to run plugin tests with 1s delay between actions and .repaint
 * Tests - the plugin tests itself!

Changed
-------

 * Individual scripts can be run from dropdown - no need to open Settings each time
 * Settings windows combined and opened via Settings toolbar button

0.2.1 - 2017-04-26
===================

Added
-----

 * Warning for invalid script folder locations

Fixed
-----

 * Tests can be re-run after changes without exiting QGIS (modules are reloaded)

0.2.0 - 2017-04-21
===================

Added
-----

 * Configuration of script folder and button to reload scripts
 * Configuration of script to test and button to run tests
 * Initial load of supporting files and documentation
