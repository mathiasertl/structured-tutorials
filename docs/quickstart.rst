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
