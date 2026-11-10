#!/usr/bin/env python3
"""Apply the Longman card templates to the open Anki collection."""

import argparse
import json
from pathlib import Path
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen


def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    request = Request(
        "http://127.0.0.1:8765", payload, {"Content-Type": "application/json"}
    )
    with urlopen(request, timeout=15) as response:
        result = json.load(response)
    if result.get("error") is not None:
        raise RuntimeError(f"{action}: {result['error']}")
    return result["result"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--initialize",
        action="store_true",
        help="Create the Longman note type/deck for a fresh collection; sync existing data first.",
    )
    args = parser.parse_args()
    name = "Longman"
    assets = Path(__file__).resolve().parents[1] / "assets/anki"
    front = (assets / "longman-front.html").read_text(encoding="utf-8")
    back = (assets / "longman-back.html").read_text(encoding="utf-8")
    css = (assets / "longman.css").read_text(encoding="utf-8")
    models = anki("modelNames")
    decks = anki("deckNames")
    if not args.initialize and (name not in models or "LongMan" not in decks):
        raise RuntimeError(
            "Sync your existing AnkiWeb collection first (Longman note type / LongMan deck missing). "
            "Only for a fresh collection, rerun with --initialize."
        )
    if name not in models:
        anki(
            "createModel",
            modelName=name,
            inOrderFields=["Word", "selected_text", "marked_sentence"],
            css=css,
            isCloze=False,
            cardTemplates=[{"Name": "Card 1", "Front": front, "Back": back}],
        )
    if "LongMan" not in decks:
        anki("createDeck", deck="LongMan")
    fields = set(anki("modelFieldNames", modelName=name))
    required = {"Word", "selected_text", "marked_sentence"}
    if not required <= fields:
        raise RuntimeError(f"Longman is missing fields: {sorted(required - fields)}")

    previous = anki("modelTemplates", modelName=name)
    if len(previous) != 1:
        raise RuntimeError("Expected one Longman card template; no changes applied.")
    previous_css = anki("modelStyling", modelName=name)["css"]
    templates = {
        next(iter(previous)): {
            "Front": front,
            "Back": back,
        }
    }
    if previous == templates and previous_css == css:
        print("Longman templates and styling are already up to date.")
        return

    # Keep the previous values only in memory to recover a partial API failure.
    try:
        anki("updateModelTemplates", model={"name": name, "templates": templates})
        anki("updateModelStyling", model={"name": name, "css": css})
        if (
            anki("modelTemplates", modelName=name) != templates
            or anki("modelStyling", modelName=name)["css"] != css
        ):
            raise RuntimeError("Anki returned different templates or styling after applying.")
    except Exception:
        anki("updateModelTemplates", model={"name": name, "templates": previous})
        anki("updateModelStyling", model={"name": name, "css": previous_css})
        raise

    print("Applied and verified the Longman front, back, and styling.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, URLError, ValueError, RuntimeError) as error:
        sys.exit(f"Could not apply Longman templates: {error}")
