##########
Quickstart
##########

************
Installation
************

To do: show how to install wheel once it exists.

To configure Sphinx, you need to add an extension and, optionally, the root directory where the tutorials are
located:

.. code-block:: python

    extensions = [
        # ... other extensions
        "structured_tutorials.sphinx",
    ]

    DOC_ROOT = Path(__file__).parent

    # configure the root directory where tutorials are located. Defaults to
    # the Sphinx source directory.
    tutorial_root = DOC_ROOT / "tutorials"


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
    usage: structured-tutorial [-h] path
    ...

Finally, you can render the tutorial in your Sphinx tutorial:

.. literalinclude:: /include/quickstart.rst
    :caption: docs/tutorial.rst
    :language: rst

In fact, above lines are included below, so this is how this tutorial will render in your documentation:

.. include:: /include/quickstart.rst

***********************
Tutorials are templates
***********************

Commands as well as output are rendered using `Jinja <https://jinja.palletsprojects.com/en/stable/>`_
templates. This allows you to reduce repetition of values or cases where a tutorial should behave differently
from runtime when rendering documentation.

The following example will create a directory, writes to a file in it and outputs the contents of said file:

.. literalinclude:: /tutorials/templates/tutorial.yaml
    :caption: docs/tutorials/templates/tutorial.yaml
    :language: yaml

This is how the documentation renders:

.. structured-tutorial:: templates/tutorial.yaml

.. structured-tutorial-part::

However, when running, you will just get:

.. code-block:: console

    user@host:~$ structured-tutorial docs/tutorials/templates/tutorial.yaml
    real data

***************************
Tutorials can contain files
***************************

Tutorials can contain files that are also rendered as templates.

The following example tutorial could be used to instruct the user to create a JSON file in
``/tmp/example.json`` and then call ``python`` to verify the syntax.

Using this YAML file:

.. literalinclude:: /tutorials/simple-file/tutorial.yaml
    :caption: docs/tutorials/simple-file/tutorial.yaml
    :language: yaml

you could render a Tutorial like this:

.. structured-tutorial:: simple-file/tutorial.yaml

Create a configuration file with the following contents:

.. structured-tutorial-part::

and make sure it is valid JSON:

.. structured-tutorial-part::

********************************
Long commands wrap automatically
********************************

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

*************************
Ask the user for feedback
*************************

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
