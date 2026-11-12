"""Contacts are displayable only after explicit verification; empty configuration is valid."""

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


def verified_resources(path: Path, region: str | None, today: date | None = None) -> list[dict]:
    if not region:
        return []
    today = today or date.today()
    try:
        body = json.loads(path.read_text())
        resources = body["resources"]
        if body["schema_version"] != 1 or not isinstance(resources, list):
            return []
    except (OSError, ValueError, KeyError, TypeError):
        return []
    verified = []
    for item in resources:
        try:
            if item["region"] != region or item["approved"] is not True:
                continue
            start, end = date.fromisoformat(item["verified_on"]), date.fromisoformat(item["expires_on"])
            source = urlparse(item["official_source"])
            if not start <= today <= end or source.scheme != "https" or not source.hostname:
                continue
            if not all(isinstance(item[k], str) and 0 < len(item[k]) <= 250 for k in ("name", "contact")):
                continue
            verified.append(item)
        except (ValueError, TypeError, KeyError):
            continue
    return verified
