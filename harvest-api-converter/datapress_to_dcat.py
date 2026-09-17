#!/usr/bin/env python3
"""
Convert a Datapress export to a static DCAT JSON file for the
ckanext-dcat DCATJSONHarvester (dcat_json harvester type).

Usage:
    python3 scripts/datapress_to_dcat.py <url> <output_file>

Upload the output file to any static host and point a dcat_json harvest
source at its URL.
"""

import json
import os
import subprocess
import sys


def to_dcat(datapress):
    dcat = {
        "identifier": datapress["id"],
        "title": datapress["title"],
        "landingPage": datapress["webpage"],
    }

    if datapress.get("description"):
        dcat["description"] = datapress["description"]
    if datapress.get("createdAt"):
        dcat["issued"] = datapress["createdAt"]
    if datapress.get("updatedAt"):
        dcat["modified"] = datapress["updatedAt"]

    contact = datapress.get("contact")
    if contact:
        publisher = {}
        if contact.get("title"):
            publisher["name"] = contact["title"]
        if contact.get("email"):
            publisher["email"] = contact["email"]
        if publisher:
            dcat["publisher"] = publisher

    distributions = []
    for resource in datapress.get("resources", []):
        url = resource.get("url")
        if not url:
            continue
        file_format = (
            os.path.splitext(resource.get("filename") or "")[1].lower().lstrip(".")
        )
        distribution = {
            "title": resource.get("title") or resource.get("filename") or "",
            "downloadURL": url,
        }
        if file_format:
            distribution["format"] = file_format.upper()
        if resource.get("size"):
            distribution["byteSize"] = resource["size"]
        if resource.get("description"):
            distribution["description"] = resource["description"]
        distributions.append(distribution)
    if distributions:
        dcat["distribution"] = distributions

    return dcat


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <url> <output_file>", file=sys.stderr)
        sys.exit(1)

    url, output_path = sys.argv[1], sys.argv[2]

    try:
        result = subprocess.run(["curl", "-sf", url], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        print(
            f"Error: curl failed fetching {url}: {e.stderr.decode().strip()}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        all_datasets = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error: response from {url} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    public_datasets = [d for d in all_datasets if d.get("sharing") == "public"]
    dcat_datasets = [to_dcat(d) for d in public_datasets]

    with open(output_path, "w") as f:
        json.dump(dcat_datasets, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
