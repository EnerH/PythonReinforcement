import os
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from dotenv import load_dotenv

# --- .env loading (works whether you run from repo root or subfolder) ---
# It will search upward for ".env" starting from the current working directory.
# If you want to lock it to the script's folder, pass: Path(__file__).resolve().parent / ".env"
env_path = find_dotenv(filename=".env", usecwd=True)  # searches from CWD upward
if not env_path:
    # fallback: try the script's folder explicitly
    env_path = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=env_path, override=True)

# --- CONFIG from env (.env should live in P5_API_DataExplorer/.env) ---
API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
# default save dir = script folder if NASA_SAVE_DIR is not set
SAVE_DIR = Path(os.getenv("NASA_SAVE_DIR", Path(__file__).resolve().parent))
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# (Optional) quick debug so you can see what got loaded:
# print(f"[debug] .env path: {env_path}")
# print(f"[debug] SAVE_DIR: {SAVE_DIR}")

# Live endpoints
APOD_URL = "https://api.nasa.gov/planetary/apod"
IMAGES_SEARCH_URL = "https://images-api.nasa.gov/search"
MSL_RSS_URL = "https://mars.nasa.gov/rss/api/"

# =============================
# CORE HELPERS
# =============================

def safe_request(url, params=None, retries=3, delay=2):
    """GET with retries and clear errors. Do not retry on 404."""
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 404:
                print(f"❌ 404 Not Found: {r.url}")
                return None
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"[Attempt {attempt}] Error: {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("❌ Failed after multiple attempts.")
                return None

# =============================
# APOD
# =============================

def fetch_apod():
    """Astronomy Picture of the Day (requires API key)."""
    params = {"api_key": API_KEY}
    data = safe_request(APOD_URL, params)
    if not data:
        return

    print("\n🌠 Astronomy Picture of the Day")
    print(f"Title: {data.get('title','')}")
    print(f"Date: {data.get('date','')}")
    explanation = data.get("explanation", "")
    print(f"Explanation: {explanation[:300]}{'...' if len(explanation) > 300 else ''}")

    img_url = data.get("hdurl") or data.get("url")
    if img_url and img_url.lower().endswith((".jpg", ".png", ".jpeg")):
        print(f"Image URL: {img_url}")
        if input("Download image? (y/n): ").strip().lower() == "y":
            save_image(img_url, "APOD.jpg")

# =============================
# CURIOSITY VIA NASA IMAGES LIBRARY
# =============================

def fetch_curiosity_images_via_library(
    query="curiosity rover",
    camera=None,         # e.g., 'navcam', 'fhaz', 'mast'
    year_start=None,     # e.g., '2015'
    year_end=None,       # e.g., '2018'
    media_type="image",
    limit=20
):
    """
    Search Curiosity images using NASA Images & Video Library (no API key).
    This is reliable while the Mars Photos API is archived.
    """
    q = query
    if camera:
        q += f" {camera}"

    params = {
        "q": q,
        "media_type": media_type,
    }
    if year_start:
        params["year_start"] = year_start
    if year_end:
        params["year_end"] = year_end

    data = safe_request(IMAGES_SEARCH_URL, params=params)
    if not data:
        print("⚠️ NASA Images search returned no data.")
        return

    collection = data.get("collection", {})
    items = collection.get("items", [])
    if not items:
        print("⚠️ No items matched your search.")
        return

    # Extract a lightweight list (title, date, preview URL)
    rows = []
    for it in items[:limit]:
        meta = (it.get("data") or [{}])[0]
        links = it.get("links") or []
        thumb = None
        for l in links:
            if l.get("rel") in (None, "preview") and l.get("href", "").lower().endswith((".jpg", ".png", ".jpeg")):
                thumb = l.get("href")
                break
        rows.append({
            "title": meta.get("title"),
            "date_created": meta.get("date_created"),
            "nasa_id": meta.get("nasa_id"),
            "preview": thumb,
        })

    if not rows:
        print("⚠️ No previewable images found (try a different camera or date range).")
        return

    print(f"\n🪐 Showing {len(rows)} results for '{q}'"
          f"{' ('+year_start+'..'+year_end+')' if year_start or year_end else ''}")
    for r in rows:
        print(f"- {r['date_created'][:10] if r['date_created'] else 'N/A'} | {r['title']}")
        print(f"  Preview: {r['preview']}\n")

    # Optional quick viz: results per year
    try:
        df = pd.DataFrame(rows)
        if not df.empty and df["date_created"].notna().any():
            df["year"] = df["date_created"].dropna().apply(lambda s: s[:4])
            plt.figure(figsize=(6, 4))
            df["year"].value_counts().sort_index().plot(kind="bar", title="Images per Year (NASA Library)")
            plt.xlabel("Year"); plt.ylabel("Count"); plt.tight_layout(); plt.show()
    except Exception as e:
        print(f"⚠️ Could not plot summary: {e}")

# =============================
# OPTIONAL: CURIOSITY RSS (paged, but may be empty now)
# =============================

def _rss_call(page=0, num=100):
    """One page of the RSS JSON with paging/size controls."""
    params = {
        "feed": "raw_images",
        "category": "msl",
        "feedtype": "json",
        "num": num,
        "page": page,
        "order": "desc",
    }
    return safe_request(MSL_RSS_URL, params=params) or {}

def fetch_rss_recent_by_filters(camera=None, start_date=None, end_date=None,
                                limit=20, pages=6, page_size=150, fallback_to_library=True):
    """
    Try to fetch Curiosity RAW images from the RSS JSON feed with paging and filters.
    If the RSS feed is empty/unavailable, optionally fallback to the NASA Images Library.
    """
    print("\n🔁 Trying Curiosity RAW RSS feed (may be empty)…")
    all_images = []
    for p in range(pages):
        data = _rss_call(page=p, num=page_size)
        images = data.get("images", [])
        if not images:
            if p == 0:
                print("⚠️ RSS returned no images (page 0). The feed may be temporarily unavailable.")
            break
        all_images.extend(images)

    if not all_images:
        print("⚠️ No images returned by RSS after paging.")
        if fallback_to_library:
            print("↪️  Falling back to NASA Images Library with your filters…")
            year_start = start_date[:4] if start_date else None
            year_end   = end_date[:4]   if end_date   else None
            return fetch_curiosity_images_via_library(
                query="curiosity rover",
                camera=camera,
                year_start=year_start,
                year_end=year_end,
                limit=limit
            )
        return

    cam_filter = camera.lower() if camera else None

    def within_range(dt_str: str) -> bool:
        if not (start_date or end_date):
            return True
        try:
            d = datetime.strptime(dt_str[:10], "%Y-%m-%d").date()
        except Exception:
            return False
        if start_date and d < datetime.strptime(start_date, "%Y-%m-%d").date():
            return False
        if end_date and d > datetime.strptime(end_date, "%Y-%m-%d").date():
            return False
        return True

    filtered = []
    for img in all_images:
        dt = img.get("date_taken", "")
        cam = (img.get("camera") or "")
        if cam_filter and cam.lower() != cam_filter:
            continue
        if not within_range(dt):
            continue
        url = img.get("image_files", {}).get("medium") or img.get("image_files", {}).get("full_res")
        if url:
            filtered.append({"date_taken": dt, "camera": cam, "url": url})

    if not filtered:
        print(f"⚠️ No RSS images matched (camera={camera or 'ALL'}, date={start_date}..{end_date}).")
        if fallback_to_library:
            print("↪️  Falling back to NASA Images Library with your filters…")
            year_start = start_date[:4] if start_date else None
            year_end   = end_date[:4]   if end_date   else None
            return fetch_curiosity_images_via_library(
                query="curiosity rover",
                camera=camera,
                year_start=year_start,
                year_end=year_end,
                limit=limit
            )
        return

    print(f"🪐 Showing {min(len(filtered), limit)} images "
          f"(camera={camera or 'ALL'}, date={start_date}..{end_date}) "
          f"from {len(all_images)} polled RSS records.")
    for row in filtered[:limit]:
        print(f"{row['date_taken']} | {row['camera']} | {row['url']}")

    # Optional quick chart
    try:
        df = pd.DataFrame(filtered)
        if not df.empty:
            plt.figure(figsize=(6, 4))
            df["camera"].value_counts().plot(kind="bar", title="Curiosity RAW Images by Camera (RSS selection)")
            plt.xlabel("Camera"); plt.ylabel("Count"); plt.tight_layout(); plt.show()
    except Exception as e:
        print(f"⚠️ Could not plot summary: {e}")


# =============================
# UTIL
# =============================

def save_image(url, filename):
    """Download and save image to SAVE_DIR (from .env NASA_SAVE_DIR)."""
    try:
        # Normalize filename a bit (avoid weird chars)
        safe = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in filename)
        file_path = SAVE_DIR / safe

        r = requests.get(url, timeout=20)
        r.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(r.content)

        print(f"✅ Saved {safe} → {file_path}")
    except Exception as e:
        print(f"⚠️ Failed to download image: {e}")


# =============================
# MENU / CLI
# =============================

def main():
    print("""
🚀 NASA API Data Explorer 🚀
[1] Astronomy Picture of the Day (APOD)
[2] Curiosity Images via NASA Images Library (keyword/camera/year filter)
[3] (Optional) Curiosity RAW RSS feed (may be empty)
[Q] Quit
""")
    while True:
        choice = input("Choose an option: ").strip().lower()
        if choice == "1":
            fetch_apod()
        elif choice == "2":
            cam = input("Camera keyword (navcam, fhaz, mast, blank=none): ").strip() or None
            year_start = input("Year start (e.g., 2015, blank=none): ").strip() or None
            year_end   = input("Year end   (e.g., 2018, blank=none): ").strip() or None
            fetch_curiosity_images_via_library(
                query="curiosity rover",
                camera=cam,
                year_start=year_start,
                year_end=year_end,
                limit=20
            )
        elif choice == "3":
            cam = input("Camera (FHAZ, RHAZ, NAVCAM, MAST, etc., blank=all): ").strip() or None
            start_d = input("Start date YYYY-MM-DD (blank=none): ").strip() or None
            end_d   = input("End date   YYYY-MM-DD (blank=none): ").strip() or None
            fetch_rss_recent_by_filters(camera=cam, start_date=start_d, end_date=end_d,
                                        limit=20, pages=4, page_size=100)
        elif choice in {"q", "quit"}:
            print("Goodbye 🌙")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
