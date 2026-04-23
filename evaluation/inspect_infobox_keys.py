import json
from collections import Counter

INPUT_FILE = "data/british_museum_collections.json"


def main() -> None:
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    counter = Counter()

    for artifact in dataset:
        raw = artifact.get("infobox_raw")
        if not raw:
            continue

        try:
            infobox = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            continue

        if isinstance(infobox, dict):
            for key in infobox.keys():
                counter[key.strip().lower()] += 1
        

    for key, count in counter.most_common(100):
        print(f"{key}: {count}")


if __name__ == "__main__":
    main()