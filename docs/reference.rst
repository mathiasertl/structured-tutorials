#########
Reference
#########

Each tutorial file can contain two elements:

parts (required, type: :ref:`Parts <reference_parts>`)
    The individual parts of the tutorial. See :ref:`Parts <reference_parts>` for more information.
configuration (optional, type: :ref:`Parts <reference_configuration>`)
    Global/initial configuration for the tutorial. See :ref:`Configuration <reference_configuration>` for
    more information.

.. _reference_parts:

*****
parts
*****

Parts is a list of individual "chapters" of your tutorial. For example, a chapter might be a set of commands
to install a software, or a configuration file that the user is instructed to create.


file parts
==========

File parts are intended to create a file when running a tutorial, and to e.g. instruct the user to create that
file when rendering the tutorial in documentation. A full example:

.. literalinclude:: /tutorials/file-full-example/tutorial.yaml
    :language: yaml

The above tutorial will render a file block when rendered:

.. structured-tutorial:: file-full-example/tutorial.yaml

.. structured-tutorial-part::

The configuration options are:

parts[n].contents (optional, str)
    The contents of the file. Mutually exclusive to ``source``.
parts[n].source (optional, str)
    Path of the original file. Mutually exclusive to ``contents``.
parts[n].destination (optional, str)
    Where to create the new file.
parts[n].template (optional, bool)
    Default: ``True``

    Set to ``False`` if this file should not be rendered as a template. This can be used to copy binary
    files and cannot be read as text files, or if you want the destination file to be a template.
parts[n].doc (optional, type: :ref:`parts[n]doc <reference_parts_n_doc>`)
    See :ref:`parts[n]doc <reference_parts_n_doc>` for details.
parts[n].run
    No options are supported thus far.

.. _reference_parts_n_doc:

parts[n].doc
------------

language (optional, str)
    Language used for syntax highlighting.
ignore_spelling (optional, bool)
    Default: ``False``

    Set to ``True`` to wrap the `caption` option in a ``:spelling:ignore:`` directive for
    `sphinxcontrib-spelling <https://github.com/sphinx-contrib/spelling>`_.

In addition, any option of the `code-block
<https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block>`_ directive
are also supported.

commands parts
==============

.. _reference_configuration:

*************
configuration
*************

configuration.doc
=================

configuration.doc.context (dict)
    Default: ``{"doc": True, "run": False, "cwd": "~", ...}``

    The initial context for rendering template strings. Additional variables in the context are used to
    influence the appearance of the prompt in console blocks:

    user
        Default: ``"user"``
    host
        Default: ``"host"``
    cwd
        Default: ``"~"``
    prompt_template
        Default: ``"{{ user }}@{{ host }}:{{ cwd }}{% if user == 'root' %}#{% else %}${% endif %} "``

configuration.run
=================

configuration.run.context (dict)
    Default: ``{"doc": True, "run": False, "cwd": Path.cwd()}``

    The initial context for rendering template strings.

configuration.run.git_export (optional, bool)
    Default: ``False``

    If set to ``True``, perform a git export before running the tutorial. The current working directory will
    change to the git export. After the tutorial, the export directory will be removed. This setting
    overrides ``temporary_directory``.

    If set, the ``cwd`` context variable will point to the temporary directory where the git repository was
    exported to. The original/initial working directory is available as ``orig_cwd``.

configuration.run.temporary_directory (optional, bool)
    Default: ``False``

    If set to ``True``, switch to an empty, temporary directory before running the tutorial. The empty
    directory will be removed once the tutorial is completed.

    If set, the ``cwd`` context variable will point to the temporary directory. The original/initial working
    directory is available as ``orig_cwd``.
