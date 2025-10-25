#########
Reference
#########

*******
General
*******

Modify the tutorial for documentation or runtime
================================================

Although antithetical to the core promise of this project, sometimes it is unavoidable to run commands
differently from how they are rendered in documentation. Examples are commands that read passwords (and avoid
reading data from stdin):

.. literalinclude:: /tutorials/doc-or-runtime/tutorial.yaml
    :language: yaml

This will render as:

.. structured-tutorial:: doc-or-runtime/tutorial.yaml

.. structured-tutorial-part::

... but in reality will run the sudo command to update the password file directly.

****************
Running commands
****************

Test the status code
====================

``structured-tutorials`` will abort a tutorial if  a specified command does not exit with a status code of
``0``. To check for a different status code, simply specify ``status_code``:

.. literalinclude:: /tutorials/exit_code/tutorial.yaml
    :language: yaml

Cleanup after running a tutorial
================================

To cleanup after after running a tutorial, specify a set of cleanup commands:

.. literalinclude:: /tutorials/cleanup/tutorial.yaml
    :language: yaml

Cleanup commands are not rendered in documentation, so this will simply render as:

.. structured-tutorial:: cleanup/tutorial.yaml

.. structured-tutorial-part::

If multiple cleanup commands are specified, they will run in-order. In case of an error, only cleanup commands
for commands that where actually run will be executed. Consider this example:

.. literalinclude:: /tutorials/cleanup-multiple/tutorial.yaml
    :language: yaml

Assuming ``cmd1`` and ``cmd2`` run successfully (or ``cmd2`` exits with a non-zero status code), this will
run, in order, ``clean3``, ``clean1`` and ``clean2``. Should ``cmd1`` return a non-zero status code, only
``clean1`` and ``clean2`` will be run.

Test a command
==============

To test if a command is indeed running successfully, use the ``test`` specification. A common use case is a
daemon that will *eventually* open a port, but subsequent commands want to connect to that daemon. For that
reason, you can also simply specify a host and port instead of running a command.

You can also specify a `retry` to run the test command multiple times before the main command is considered
to have failed. A `delay` will delay the first run of the command and a `backoff_factor` will introduce an
increasing delay between retries.

With the following tutorial:

.. literalinclude:: /tutorials/test-command/tutorial.yaml
    :language: yaml

The first part will just create a file (and error out if it was not created).

.. structured-tutorial:: test-command/tutorial.yaml

.. structured-tutorial-part::

The second part will test if ``ncat`` is installed and call it after a three-second delay:

.. structured-tutorial-part::

********************
Documenting commands
********************

Show output
===========

To show an output when rendering commands, specify the ``output`` key:

.. literalinclude:: /tutorials/echo/tutorial.yaml
    :language: yaml

This will render as:

.. structured-tutorial:: echo/tutorial.yaml

.. structured-tutorial-part::

Template context
================

Both command and output are rendered as template with the current context. The initial context is specified in
the global context, and each command can update the context before and after being shown:

.. literalinclude:: /tutorials/context/tutorial.yaml
    :language: yaml

This will render as:

.. structured-tutorial:: context/tutorial.yaml

.. structured-tutorial-part::


Update the command prompt
=========================

To configure the initial command prompt, set below context variables in the initial context. You can update
those variables at any time. The following variables influence the prompt:

prompt
    Default: ``"{{ user }}@{{ host }}:{{ cwd }}{% if user == 'root' %}#{% else %}${% endif %} "``

    The template used to render the prompt, which includes the values below.

user
    Default: ``"user"``

    The username rendered in the prompt.

host
    Default: ``"host"``

    The hostname rendered in the prompt.

cwd
    Default: ``"~"``

    The current working directory rendered in the prompt.

.. literalinclude:: /tutorials/prompt/tutorial.yaml
    :language: yaml

This will render as:

.. structured-tutorial:: prompt/tutorial.yaml

.. structured-tutorial-part::
