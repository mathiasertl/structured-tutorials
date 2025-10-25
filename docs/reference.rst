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

********************
Documenting commands
********************

Specifying the command
======================

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