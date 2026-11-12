"""List and validate the files the game actually serves, without calling an LLM."""
import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.story import ASSETS, SCENES

QUOTED = re.compile(r'''(["'])([^"'\r\n]+)\1''')
EXTENSION = re.compile(r"\.(?:png|jpe?g|mp4|mp3|ttf|woff2?|css|js|json)(?:\?[^\s]*)?$", re.I)


def runtime_assets():
    paths = {"public/assets/images/" + filename for filename in ASSETS.values()}
    paths.update("public" + unquote(scene["video"]) for scene in SCENES.values() if scene.get("video"))
    sources = list((ROOT / "templates").glob("*.html")) + list((ROOT / "public/assets/js").glob("*.js"))
    for source in sources:
        for _, value in QUOTED.findall(source.read_text(encoding="utf-8")):
            if not EXTENSION.search(value):
                continue
            value = unquote(urlsplit(value).path)
            if value.startswith("/assets/"):
                paths.add("public" + value)
            elif value.lower().endswith(".png") and "/" not in value:
                # Menu cards and encodeURIComponent-based artwork filenames.
                paths.add("public/assets/images/" + value)
    config = json.loads((ROOT / "public/assets/audio/audio-config.json").read_text(encoding="utf-8"))
    for track in list(config["music"].values()) + list(config["effects"].values()):
        paths.add("public/assets/sounds/" + track["file"])
    # Follow only stylesheets actually loaded by the two application pages.
    for relative in list(paths):
        if relative.endswith(".css"):
            stylesheet = ROOT / relative
            for value in re.findall(r"url\(\s*['\"]?([^)'\"]+)", stylesheet.read_text(encoding="utf-8")):
                if not value.startswith("data:"):
                    target = (stylesheet.parent / unquote(urlsplit(value).path)).resolve()
                    paths.add(target.relative_to(ROOT).as_posix())
    paths.add("public/assets/fonts/OFL.md")
    return sorted(paths)


def validate(paths):
    problems = []
    for relative in paths:
        path = ROOT / relative
        if not path.is_file() or not path.stat().st_size:
            problems.append("Missing/empty: " + relative)
            continue
        if path.stat().st_size >= 100 * 1024 * 1024:
            problems.append("GitHub file limit: " + relative)
        # Windows is case-insensitive; Render's Linux filesystem is not.
        parent = ROOT
        for part in Path(relative).parts:
            if part not in {entry.name for entry in parent.iterdir()}:
                problems.append("Case mismatch: " + relative)
                break
            parent /= part
    if problems:
        raise ValueError("\n".join(problems))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the asset allowlist as JSON")
    args = parser.parse_args()
    assets = runtime_assets()
    validate(assets)
    if args.json:
        print(json.dumps(assets, ensure_ascii=False, indent=2))
    else:
        total = sum((ROOT / path).stat().st_size for path in assets)
        print(f"PASS: {len(assets)} runtime assets; {total / 1024**2:.1f} MiB; no missing, empty, oversized or case-mismatched files")
