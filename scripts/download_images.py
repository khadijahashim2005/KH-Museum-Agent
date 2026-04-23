# ============================================================
# download_images.py
# Downloads agent images from Mistral signed URLs and saves
# them locally, then updates cached_agents.json with local paths.
#
# Run ONCE after generate_agents.py:
#   python scripts/download_images.py
#
# Images saved to:
#   KH-Museum-Agent/data/images/<slug>.png
# Cache updated:
#   image_url → local path usable by Flask at /images/<slug>.png
# ============================================================

import os
import sys
import json
import re
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "data", "cached_agents.json")
IMAGES_DIR = os.path.join(BASE_DIR, "data", "images")


def slugify(text: str) -> str:
    """Turn an artefact title into a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


def download_images():
    if not os.path.exists(CACHE_FILE):
        print(f"❌ Cache not found at: {CACHE_FILE}")
        print("   Run generate_agents.py first.")
        sys.exit(1)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)

    print(f"Found {len(cache)} agents in cache\n")

    updated = 0
    skipped = 0
    failed  = 0

    for key, entry in cache.items():
        title     = entry.get("artefact", {}).get("title", key)
        image_url = entry.get("image_url")

        if not image_url:
            print(f"  ⚠️  {title} — no image URL, skipping")
            skipped += 1
            continue

        # Check if already a local path (already downloaded)
        if image_url.startswith("/") or image_url.startswith("data/"):
            print(f"  ✅ {title} — already local, skipping")
            skipped += 1
            continue

        slug     = slugify(title)
        filename = f"{slug}.png"
        filepath = os.path.join(IMAGES_DIR, filename)

        print(f"  Downloading: {title}...")
        try:
            urllib.request.urlretrieve(image_url, filepath)
            # Store as a relative URL the Flask static route can serve
            local_path = f"/agent-images/{filename}"
            cache[key]["image_url"] = local_path
            print(f"  ✅ Saved → data/images/{filename}")
            updated += 1
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed += 1

    # Save updated cache
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"✅ Downloaded: {updated}")
    print(f"⚠️  Skipped:    {skipped}")
    print(f"❌ Failed:     {failed}")
    print(f"Cache updated: {CACHE_FILE}")
    print(f"Images saved:  {IMAGES_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    download_images()