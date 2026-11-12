"""Package the current synthetic prototype and evidence without runtimes or local session data."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = [
        ROOT / name
        for name in [
            "README.md",
            "pyproject.toml",
            "uv.lock",
            ".env.example",
            ".gitignore",
            "app.py",
            ".streamlit/config.toml",
        ]
    ]
    for folder in [
        "assets",
        "config",
        "data",
        "docs",
        "mannsahara",
        "prompts",
        "scripts",
        "tests",
        "evidence",
    ]:
        paths.extend(
            p
            for p in (ROOT / folder).rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix != ".pyc"
            and not p.name.startswith("package-sha256")
        )
    paths.extend((ROOT / "output/pdf").glob("group-09-mannsahara-specification.*"))
    # The earlier results visualization is explicitly historical after the prompt/model change.
    if (ROOT / "output/mannsahara-results.html").exists():
        paths.append(ROOT / "output/mannsahara-results.html")
    paths = sorted(set(paths))
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest_path = ROOT / "evidence/package-sha256-personal-life.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    paths.append(manifest_path)
    archive = ROOT / "output/mannsahara-submission-personal-life.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in paths:
            bundle.write(path, Path("mannsahara") / path.relative_to(ROOT))
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for path, digest in manifest.items():
            assert hashlib.sha256(bundle.read("mannsahara/" + path)).hexdigest() == digest, path
    print(f"Verified {archive.name}: {len(paths)} files, {archive.stat().st_size} bytes")


if __name__ == "__main__":
    main()
