#############
Test commands
#############

When running commands, there are various ways to test if the command succeeded and ran as expected.

You can also use tests to update the context for subsequent commands based on the output of a command.

.. NOTE:: You can specify multiple tests as well (e.g. test the output *and* check if a port was opened).

********************
Test the status code
********************

``structured-tutorials`` will abort a tutorial if  a specified command does not exit with a status code of
``0``. To check for a different status code, simply specify ``status_code``:

.. literalinclude:: /tutorials/exit_code/tutorial.yaml
    :language: yaml

**************************
Test output of the command
**************************

You can test either the standard output or standard error stream of a command with a regular expression. You
can also test line and character count. Regular expressions with named patterns can be used to update the
context for later commands:

.. tab:: Configuration

    .. literalinclude:: /tutorials/test-output/tutorial.yaml
        :caption: docs/tutorials/test-output/tutorial.yaml
        :language: yaml

.. tab:: Documentation

    .. structured-tutorial:: test-output/tutorial.yaml

    .. structured-tutorial-part::


******************
Run a test command
******************

You can run a test command to verify that the command actually ran successfully:

.. literalinclude:: /tutorials/test-command/tutorial.yaml
    :caption: docs/tutorials/test-command/tutorial.yaml
    :language: yaml

Note that you can also retry commands, as shown for ports below.

*********
Test port
*********

You can test that a port is opened by the command:

.. literalinclude:: /tutorials/test-port/tutorial.yaml
    :caption: docs/tutorials/test-port/tutorial.yaml
    :language: yaml

For ports and commands, you can also specify a `retry` to run the test command multiple times before the main
command is considered to have failed. A `delay` will delay the first run of the command and a
`backoff_factor` will introduce an increasing delay between retries. A common use case is a daemon that
will *eventually* open a port, but subsequent commands want to connect to that daemon.
