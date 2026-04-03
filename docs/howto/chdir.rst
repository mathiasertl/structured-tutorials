########################
Change working directory
########################

Sometimes you will want to change the working directory where commands are run from. At runtime, this will
change the meaning of relatives paths in commands, when rendering documentation, the prompt will show a
different working directory.

The working directory can changed using the ``chdir`` directive of commands. The value is a path, and is
rendered as a template.

*******
Example
*******

Consider the following tutorial file:

.. literalinclude:: /tutorials/chdir/tutorial.yaml
    :language: yaml

.. structured-tutorial:: chdir/tutorial.yaml

The first commands part shows the user how to switch the working directory and run a command there:

.. structured-tutorial-part::


The second commands part shows the user how to create and switch to another directory, where the path is
determined by a context variable:

.. structured-tutorial-part::

... but will run in a random directory at runtime.

Use a true temporary directory at runtime
=========================================

Since ``chdir`` is a template value and ``update_context`` and/or output tests (that may update the context)
are run before applying it, the best way is simply use mkdir only at runtime:

.. literalinclude:: /tutorials/chdir-with-mkdtemp/tutorial.yaml
    :language: yaml

.. structured-tutorial:: chdir-with-mkdtemp/tutorial.yaml

This will show ``/tmp/docs`` in documentation:

.. structured-tutorial-part::


Switch to a different directory in documentation and at runtime
===============================================================

The best way to do this is to specify a different context for documentation and runtime. The above example
already does this.

Why do I have to specify ``chdir`` at runtime, even though my command already actually changes it?
==================================================================================================

Because the command you specify is launched in a subprocess, and the caller (structured-tutorials) has no idea
what that subprocess does. Your command is still useful (it shows that switching directory will work), but
there is no way to pass this information to the next command.
