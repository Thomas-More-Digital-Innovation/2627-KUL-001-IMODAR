"""Write the OpenAPI document the frontend types are generated from."""

import json
from pathlib import Path

from imodar.api.main import app

target = Path(__file__).resolve().parent.parent / "openapi" / "imodar.json"
target.write_text(json.dumps(app.openapi(), indent=2) + "\n")
