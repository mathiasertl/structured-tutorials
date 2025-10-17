#########
Reference
#########

****************
Running commands
****************

Test the status code
====================

``structured-tutorials`` will abort a tutorial if  a specified command does not exit with a status code of
``0``. To check for a different status code, simply specify ``status_code``:

.. literalinclude:: /tutorials/exit_code/tutorial.yaml
    :language: yaml