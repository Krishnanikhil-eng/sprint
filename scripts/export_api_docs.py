"""
API Documentation Exporter Script.
Exports OpenAPI 3.0 schema (docs/openapi.json) and Postman Collection v2.1 (docs/postman_collection.json).
"""

import json
import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))

from src.api.main import app


def export_openapi() -> Dict[str, Any]:
    """Exports OpenAPI schema dictionary from FastAPI app."""
    return app.openapi()


def convert_openapi_to_postman(openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Converts OpenAPI 3.0 schema dictionary into Postman Collection v2.1 format."""
    info = openapi_spec.get("info", {})
    postman_items: List[Dict[str, Any]] = []

    paths = openapi_spec.get("paths", {})
    for path_key, methods in paths.items():
        for method_key, operation in methods.items():
            if method_key not in ["get", "post", "put", "delete", "patch"]:
                continue

            summary = operation.get("summary", f"{method_key.upper()} {path_key}")
            tags = operation.get("tags", ["Default"])
            tag_name = tags[0] if tags else "Default"

            # Parse path variables / query parameters
            raw_url = "http://127.0.0.1:8000" + path_key
            path_segments = [seg for seg in path_key.split("/") if seg]

            item_dict = {
                "name": summary,
                "request": {
                    "method": method_key.upper(),
                    "header": [],
                    "url": {
                        "raw": raw_url,
                        "protocol": "http",
                        "host": ["127", "0", "0", "1"],
                        "port": "8000",
                        "path": path_segments
                    },
                    "description": operation.get("description", "")
                },
                "response": []
            }

            # Find or create tag folder in postman collection
            folder = next((f for f in postman_items if f.get("name") == tag_name), None)
            if not folder:
                folder = {
                    "name": tag_name,
                    "item": []
                }
                postman_items.append(folder)
            folder["item"].append(item_dict)

    postman_collection = {
        "info": {
            "name": info.get("title", "Nifty 100 Financial Analytics API"),
            "description": info.get("description", "Postman collection for REST API"),
            "version": info.get("version", "1.0.0"),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": postman_items
    }

    return postman_collection


def main():
    os.makedirs("docs", exist_ok=True)
    openapi_spec = export_openapi()
    
    openapi_file = os.path.join("docs", "openapi.json")
    with open(openapi_file, "w", encoding="utf-8") as f:
        json.dump(openapi_spec, f, indent=2)
    print(f"Exported OpenAPI spec to {openapi_file}")

    postman_coll = convert_openapi_to_postman(openapi_spec)
    postman_file = os.path.join("docs", "postman_collection.json")
    with open(postman_file, "w", encoding="utf-8") as f:
        json.dump(postman_coll, f, indent=2)
    print(f"Exported Postman Collection to {postman_file}")


if __name__ == "__main__":
    main()
