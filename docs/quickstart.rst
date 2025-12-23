##########
Quickstart
##########

************
Installation
************

**structured-tutorials** is published on `PyPI <https://pypi.org/project/structured-tutorials/>`_ and
thus can simply be installed via ``pip`` (or any other package management tool, such as
`uv <https://docs.astral.sh/uv/>`_):

.. code-block:: console

    $ pip install structured-tutorials

To render your tutorials in Sphinx, add the extension and, optionally, where your tutorials are stored
(this can be outside of the Sphinx root):

.. code-block:: python

    extensions = [
        # ... other extensions
        "structured_tutorials.sphinx",
    ]

    # Location where your tutorials are stored (default: same directory as conf.py).
    #structured_tutorials_root = Path(__file__).parent / "tutorials"


*******************
Your first tutorial
*******************

To get started with the simplest possible tutorial, create a minimal configuration file:

.. literalinclude:: /tutorials/quickstart/tutorial.yaml
    :caption: docs/tutorials/quickstart/tutorial.yaml
    :language: yaml

You can run this tutorial straight away:

.. code-block:: console

    user@host:~/example/$ structured-tutorial docs/tutorials/quickstart/tutorial.yaml
    Running part 0...
    + structured-tutorial --help
    usage: structured-tutorial [-h] path
    ...
    + echo "Finished running example tutorial."
    Finished running example tutorial.

Finally, you can render the tutorial in your Sphinx tutorial:

.. literalinclude:: /include/quickstart.rst
    :caption: docs/tutorial.rst
    :language: rst

In fact, above lines are included below, so this is how this tutorial will render in your documentation:

.. include:: /include/quickstart.rst

***********************
A more advanced example
***********************

The above is nice but not very useful. Let's show you a few new cool features next.

Commands, output, file contents and many other parts are rendered using `Jinja templates
<https://jinja.palletsprojects.com/en/stable/>`_. This allows you to reduce repetition of and use different
values for documentation and runtime.

Tutorials can create files (that are shown appropriately in your documentation). The tutorial below shows you
how to create a JSON file that shows up with proper syntax highlighting.

You can test success of a command by checking the status code, output or even if a TCP port was
opened. When checking the output, you can use regular expressions for matching and even named patterns to
update the context with runtime data. Below we create a temporary directory with ``mktemp`` and use it
later to create the file in it.

The following example will create a directory, writes to a file in it and outputs its contents:

.. literalinclude:: /tutorials/templates/tutorial.yaml
    :caption: docs/tutorials/templates/tutorial.yaml
    :language: yaml

Render this tutorial
====================

The code in your reStructuredText doesn't look much different. You render three parts, and the first two
reference the id you have given them in the YAML file.

.. literalinclude:: /include/quickstart-more-features.rst
    :caption: docs/tutorial.rst
    :language: rst

The above file is included below.

.. include:: /include/quickstart-more-features.rst

Run this tutorial
=================

When running this tutorial, it'll do what you instructed the user to do: Create a temporary directory, then a
JSON file in it, and then output it. Cleanup is assured through the cleanup directive, even if one of the
commands would fail:

.. code-block:: console

    user@host:~/example/$ structured-tutorial docs/tutorials/templates/tutorial.yaml
    Running part create-directory...
    + mktemp -d
    Running part create-file...
    Running part 2...
    + cat /tmp/tmp.6G6S9dX0MN/example.txt
    {"key": "run"}
    + cat /tmp/tmp.6G6S9dX0MN/example.txt | python -m json.tool
    ...
    INFO     | Running cleanup commands.
    + rm -r /tmp/tmp.6G6S9dX0M

********************************************
Generating documentation out of the tutorial
********************************************

Long commands wrap automatically
================================

When rendering a tutorial, long commands wrap automatically. With the following YAML file:

.. literalinclude:: /tutorials/long-commands/tutorial.yaml
    :caption: docs/tutorials/long-commands/tutorial.yaml
    :language: yaml

you will get:

.. structured-tutorial:: long-commands/tutorial.yaml

.. structured-tutorial-part::

Note that single-value-options and respective values do not split by default, so `-e DEMO=value` will never
split between option argument and value.

Single-character options will not be split from their respective value:

.. structured-tutorial-part::

.. _quickstart_alternatives:

Show the user alternatives
==========================

Sometimes you want to present the user with different options when following a tutorial. For example, you
might want to show a user how to set up your web application using either PostgreSQL or MySQL.

`structured-tutorials` supports `alternatives`. They render as tabs in documentation, but when running a
tutorial, the user has to specify an alternative. Alternatives can contain either commands or files (and you
could even mix them):

.. literalinclude:: /tutorials/alternatives/tutorial.yaml
    :caption: docs/tutorials/alternatives/tutorial.yaml
    :language: yaml

.. structured-tutorial:: alternatives/tutorial.yaml

The first part will show the user how to install the respective database backend:

.. structured-tutorial-part::

The second part will show the user how to configure your application for the respective database backend.

.. structured-tutorial-part::

Note that this example of course omits configuring the database itself or any other details.

********************
Running the tutorial
********************

Verify success of commands
==========================

You can verify the success of commands by checking the status code, the output or even test if a port is
opened properly. You can add multiple tests, and when testing the output, update the context for successive
commands.

For ports and commands, you can also specify a `retry` to run the test command multiple times before the main
command is considered to have failed. A `delay` will delay the first run of the command and a
`backoff_factor` will introduce an increasing delay between retries. A common use case is a daemon that
will *eventually* open a port, but subsequent commands want to connect to that daemon.

Test status code
----------------

By default, a non-zero status code is considered an error, but you can also require a non-zero status
code:

.. literalinclude:: /tutorials/exit_code/tutorial.yaml
    :caption: docs/tutorials/exit_code/tutorial.yaml
    :language: yaml

Test output
-----------

You can test either the standard output or standard error stream of a command with a regular expression. You
can also use named patterns to update the context for later commands:

.. tab:: Configuration

    .. literalinclude:: /tutorials/test-output/tutorial.yaml
        :caption: docs/tutorials/test-output/tutorial.yaml
        :language: yaml

.. tab:: Documentation

    .. structured-tutorial:: test-output/tutorial.yaml

    .. structured-tutorial-part::

Run a test command
------------------

You can run a test command to verify that the command actually ran successfully:

.. literalinclude:: /tutorials/test-command/tutorial.yaml
    :caption: docs/tutorials/test-command/tutorial.yaml
    :language: yaml

Test port
---------

You can test that a port is opened by the command:

.. literalinclude:: /tutorials/test-port/tutorial.yaml
    :caption: docs/tutorials/test-port/tutorial.yaml
    :language: yaml

Select alternatives
===================

If your tutorial contains alternatives (see :ref:`quickstart_alternatives`), you must select one of them when
running your tutorial. You wouldn't normally install both PostgreSQL and MariaDB, for example:

.. code-block:: console

    user@host:~$ structured-tutorials -a postgresql ...

Ask the user for feedback
=========================

When running a tutorial, you can prompt the user to inspect the current state. You can ask the user to just
press "enter" or even to confirm that the current state looks okay (with answering "yes" or "now").

When rendering a tutorial, prompt parts are simply skipped.

As an example:

.. literalinclude:: /tutorials/interactive-prompt/tutorial.yaml
    :caption: docs/tutorials/interactive-prompt/tutorial.yaml
    :language: yaml

.. structured-tutorial:: interactive-prompt/tutorial.yaml

In Sphinx, you can call ``structured-tutorial-part`` only twice, as prompts are simply skipped. The first
part just creates a file. Since ``temporary_directory: true`` in the configuration, this will run in
a temporary directory that is removed after running the tutorial:

.. structured-tutorial-part::

When running the tutorial, the user will now be prompted to confirm the current state. The prompt would
contain the current working directory. Presumably, the user would check the contents of ``test.txt`` in that
directory.

Prevent shell injection
=======================

You may also specify commands as lists to prevent shell injection. Note that every word of your command is
still rendered as template:

.. tab:: Configuration

    .. literalinclude:: /tutorials/command-as-list/tutorial.yaml
        :caption: docs/tutorials/command-as-list/tutorial.yaml
        :language: yaml

.. tab:: Documentation

    .. structured-tutorial:: command-as-list/tutorial.yaml

    .. structured-tutorial-part::
