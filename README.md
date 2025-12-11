# structured-tutorials

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

`structured-tutorials` allows you to write tutorials that can be rendered as Sphinx documentation and also be
run on your local system to verify correctness.

With `structured-tutorials` you to specify commands in a configuration file. A Sphinx plugin allows you to
render those commands in your project documentation. A command-line tool can load the configuration file and
run it on your local system.

## TODO

* config files that are written to a destination
* Alternatives (e.g. Redis vs. RabbitMQ or MariaDB vs. PostgreSQL)
  * For both commands and config files
* Execute commands locally
  * test output
  * test status code
  * add cleanup actions
  * define tests for successful start
  * define waits (e.g. until port is open, ...)
* Render documentation
  * Show demo output
* Run locally on command line
* Run in vagrant
