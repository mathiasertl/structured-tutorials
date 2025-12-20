#!/bin/bash -ex

SWAGGER_UI_RELEASE=5.30.3

wget https://github.com/swagger-api/swagger-ui/archive/refs/tags/v${SWAGGER_UI_RELEASE}.tar.gz
tar xf v${SWAGGER_UI_RELEASE}.tar.gz -C docs/_static/ --strip=1 swagger-ui-${SWAGGER_UI_RELEASE}/dist/ --transform s/dist/swagger-ui/