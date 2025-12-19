"""Script to generate an OpenAPI schema."""

import argparse
import json
from pathlib import Path
from typing import Any

import jinja2
from pydantic import BaseModel

from structured_tutorials.models.tutorial import TutorialModel

parser = argparse.ArgumentParser()
parser.add_argument("--swagger-path", type=Path, default=Path.cwd() / "docs" / "_static" / "swagger-ui")
parser.add_argument(
    "-o", "--output", action="store_true", default=False, help="Write schema to stdout as well."
)
args = parser.parse_args()

swagger_initializer = """window.onload = function() {
  //<editor-fold desc="Changeable Configuration Block">

  // the following lines will be replaced by docker/configurator, when it runs in a docker-container
  window.ui = SwaggerUIBundle({
    spec: {{ spec }},
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ],
    layout: "StandaloneLayout"
  });

  //</editor-fold>
}"""


def generate_openapi_schema(
    model: type[BaseModel], title: str = "Structured Tutorials model reference", version: str = "1.0.0"
) -> dict[str, Any]:
    """Generate the OpenAPI schema for the given model."""
    # Generate Pydantic v2 JSON schema
    schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
    schemas = schema.get("$defs", {}).copy()
    schemas[model.__name__] = schema

    # Minimal OpenAPI 3.0.0 document with only components
    openapi = {
        "openapi": "3.0.0",
        "info": {"title": title, "version": version},
        "paths": {},  # no API paths
        "components": {"schemas": schemas},
    }
    return openapi


openapi = generate_openapi_schema(TutorialModel)

env = jinja2.Environment()
template = env.from_string(swagger_initializer)
swagger_js = template.render(spec=json.dumps(openapi, indent=4, sort_keys=True))
with open(args.swagger_path / "swagger-initializer.js", "w") as fh:
    fh.write(swagger_js)

if args.output:
    print(json.dumps(openapi, indent=4, sort_keys=True))
