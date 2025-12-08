###########
Development
###########

***************
Swagger UI docs
***************

To generate the Swagger UI documentation locally

* Download the `latest release <https://github.com/swagger-api/swagger-ui/releases>`_.
* Extract the `dist` folder:

  .. code-block:: console

     tar xf v5.30.3.tar.gz -C docs/_static/ --strip=1 swagger-ui-5.30.3/dist/ --transform s/dist/swagger-ui/

* Generate schema:

