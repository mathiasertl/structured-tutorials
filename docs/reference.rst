#########
Reference
#########

For a complete model reference, please see the `Swagger UI documentation <_static/swagger-ui/index.html>`_.

For a quick overview, each tutorial file can contain two elements:

parts (required)
    The individual parts of the tutorial. A part can have multiple types, either:

    * ``CommandsPartModel`` for a list of commands to execute.
    * ``FilePartModel`` for a file to create.

configuration (optional)
    Global/initial configuration for the tutorial. This is represented by the ``ConfigurationModel``.
