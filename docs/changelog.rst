#########
ChangeLog
#########

******************
0.3.0 (2025-12-26)
******************

* Tutorials can now be configured to pass a clear environment to all processes.
* Tutorials can now configure additional environment variables passed to all processes.
* Single commands can now update the environment for all subsequent commands. Values are rendered as
  templates, so you can add (parts of) the output of a command to the environment by combining a test for
  the command output that uses a named pattern in a regular expression for the output.
* ``parts.{commands}.{command}.run.{chdir}`` is now a template. This allows you to change the directory based
  on the output of a previous command.
* Bugfix: Individual commands marked as skipped for documentation, are now actually skipped.

******************
0.2.0 (2025-12-23)
******************

Documentation
=============

* Continue reworking the documentation.
* Add option to render extra text before/after a part. The text is rendered as a template.
* Parts can now have an ID that you can reference when rendering parts to make sure that you render what
  you actually think you render (useful for longer tutorials).
* Add ``structured_tutorials_context`` option to pass extra context variables to a tutorial.
* Rename the ``tutorial_root`` option to ``structured_tutorials_root``.
* rename the ``structured_tutorial_command_text_width`` option to ``structured_tutorials_command_text_width``.

Command-line
============

* Add option ``--define {key} {value}`` to pass extra context variables.
* Greatly improve error handling.
* Parts can now have a name that is shown before running a tutorial part.
* Add option to clear the environment for a command.
* Add option to add extra environment variables for a command. Environment variables are rendered as
  templates.
* Add ability to pass input to a process.
* Command output can now also be tested for line or character count. You can specify an exact match, or a
  minimum and/or maximum.

******************
0.1.0 (2025-12-22)
******************

Initial version.
