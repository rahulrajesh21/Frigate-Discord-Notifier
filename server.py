#!/usr/bin/env python3
"""
Frigate -> Discord High-Resolution Video Notification Service (Rich Embed Edition)
Receives Frigate-Notify webhook triggers, fetches high-resolution event clips
from Frigate's recording API, automatically splits large clips (>9.5MB) into lossless
parts with zero re-encoding, and sends them to Discord using Discord Rich Embeds.
"""

import os
import sys
import time
import json
import re
import glob
import math
import shutil
import tempfile
import threading
import subprocess
from datetime import datetime
from collections import OrderedDict
from flask import Flask, request, jsonify
import requests

# Try to ensure static_ffmpeg is in PATH if installed
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

# Ensure ~/.local/bin is in PATH
local_bin = os.path.expanduser("~/.local/bin")
if local_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"

def load_env_file():
    """Loads environment variables from .env file if present."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception as e:
            print(f"Warning: could not read .env: {e}", flush=True)

load_env_file()

app = Flask(__name__)

# Configuration
FRIGATE_URL = os.environ.get("FRIGATE_URL", "http://172.18.0.2:5000")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") or os.environ.get("DISCORD_WEBHOOK", "")
PORT = int(os.environ.get("PORT", "5001"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "15"))
RETRY_INTERVAL = int(os.environ.get("RETRY_INTERVAL", "4"))
# Discord standard webhook upload limit is 10 MB. We threshold at 9.5 MB.
MAX_FILE_SIZE_MB = float(os.environ.get("MAX_FILE_SIZE_MB", "9.5"))

# In-memory deduplication cache
# Stores event_id -> timestamp (cleaned every 15 mins)
_seen_events = OrderedDict()
_seen_lock = threading.Lock()
DEDUP_CACHE_LIMIT = 500
DEDUP_TTL_SECONDS = 900  # 15 minutes


def get_discord_webhook_url() -> str:
    """Gets Discord webhook URL from environment or ~/.notify-discord.json."""
    global DISCORD_WEBHOOK_URL
    if DISCORD_WEBHOOK_URL:
        return DISCORD_WEBHOOK_URL

    for env_key in ["DISCORD_WEBHOOK_URL", "DISCORD_WEBHOOK", "WEBHOOK_URL"]:
        val = os.environ.get(env_key)
        if val:
            DISCORD_WEBHOOK_URL = val
            return val

    config_path = os.path.expanduser("~/.notify-discord.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                data = json.load(f)
                url = data.get("webhook-url") or data.get("webhook_url")
                if url:
                    DISCORD_WEBHOOK_URL = url
                    return url
        except Exception as e:
            print(f"Warning: Could not read ~/.notify-discord.json: {e}", flush=True)

    return ""


def is_duplicate(event_id: str) -> bool:
    """Checks if an event ID has already been processed recently."""
    now = time.time()
    with _seen_lock:
        # Evict expired items
        while _seen_events and (now - next(iter(_seen_events.values())) > DEDUP_TTL_SECONDS):
            _seen_events.popitem(last=False)
        return event_id in _seen_events


def record_event(event_id: str):
    """Records an event ID into the deduplication cache."""
    with _seen_lock:
        if len(_seen_events) >= DEDUP_CACHE_LIMIT:
            _seen_events.popitem(last=False)
        _seen_events[event_id] = time.time()


def resolve_frigate_url() -> str:
    """
    Validates FRIGATE_URL or discovers the active Frigate instance
    on localhost or docker bridge.
    """
    global FRIGATE_URL
    candidates = [
        FRIGATE_URL,
        "http://172.18.0.2:5000",
        "http://172.18.0.3:5000",
        "http://frigate:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5000"
    ]
    for url in candidates:
        if not url:
            continue
        try:
            r = requests.get(f"{url}/api/version", timeout=1.5)
            if r.status_code == 200:
                FRIGATE_URL = url
                return url
        except Exception:
            continue

    # Fallback scan on docker bridge subnets
    for subnet in ["172.18.0", "172.17.0"]:
        for i in range(2, 16):
            url = f"http://{subnet}.{i}:5000"
            try:
                r = requests.get(f"{url}/api/version", timeout=0.5)
                if r.status_code == 200:
                    FRIGATE_URL = url
                    return url
            except Exception:
                continue

    return FRIGATE_URL


def parse_webhook_payload(req):
    """
    Extracts event metadata from various Frigate & Frigate-Notify payload structures.
    Supports JSON, nested JSON, Frigate MQTT/webhooks (after/before), and plain text.
    """
    raw_text = req.get_data(as_text=True) or ""
    data = req.get_json(silent=True)

    event_data = {
        "id": None,
        "camera": "unknown",
        "label": "unknown",
        "start_time": None,
        "is_test": False
    }

    if isinstance(data, dict):
        # Handle Frigate direct webhook {"before": {...}, "after": {...}, "type": "..."}
        if "after" in data and isinstance(data.get("after"), dict):
            target = data["after"]
        # Handle Frigate-Notify nested event object if present
        elif "event" in data and isinstance(data.get("event"), dict):
            target = data["event"]
        else:
            target = data

        # Look for ID in various casing conventions
        for key in ["id", "ID", "event_id", "EventID", "eventId", "event_ID"]:
            if key in target and target[key]:
                event_data["id"] = str(target[key]).strip()
                break

        # Look for Camera
        for key in ["camera", "Camera", "camera_name", "CameraName"]:
            if key in target and target[key]:
                event_data["camera"] = str(target[key]).strip()
                break

        # Look for Label
        for key in ["label", "Label", "object", "detected_object", "Object"]:
            if key in target and target[key]:
                event_data["label"] = str(target[key]).strip()
                break

        # Look for Start Time
        for key in ["start_time", "StartTime", "time", "Time", "timestamp", "Timestamp"]:
            if key in target and target[key]:
                event_data["start_time"] = target[key]
                break

    # If ID was not found in parsed JSON, attempt regex parsing on raw body
    if not event_data["id"] and raw_text:
        # Look for Frigate event ID format: timestamp.fraction-hash
        match = re.search(r'(\d{9,11}\.\d+-[a-zA-Z0-9]+)', raw_text)
        if match:
            event_data["id"] = match.group(1)
        else:
            # Check for TEST pattern (e.g. TEST123)
            test_match = re.search(r'["\']?(TEST[a-zA-Z0-9_-]*)["\']?', raw_text)
            if test_match:
                event_data["id"] = test_match.group(1)

        # Look for camera name in raw text
        cam_match = re.search(r'["\']?camera["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)["\']?', raw_text, re.IGNORECASE)
        if cam_match:
            event_data["camera"] = cam_match.group(1)

        # Look for label in raw text
        lbl_match = re.search(r'["\']?label["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)["\']?', raw_text, re.IGNORECASE)
        if lbl_match:
            event_data["label"] = lbl_match.group(1)

    if event_data["id"]:
        if event_data["id"].upper().startswith("TEST") or (isinstance(data, dict) and data.get("test")):
            event_data["is_test"] = True

    return event_data, raw_text


def download_clip(event_id: str, frigate_url: str):
    """
    Downloads the high-resolution event clip MP4 from Frigate API with retry loop.
    Returns (temp_file_path, file_size_mb) or (None, 0) on failure.
    """
    url = f"{frigate_url}/api/events/{event_id}/clip.mp4"
    print(f"WAITING FOR CLIP: {event_id} via {url}", flush=True)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=30, stream=True)
            if response.status_code == 200:
                # Write stream to a temporary MP4 file
                tf = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                temp_path = tf.name
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        tf.write(chunk)
                tf.close()

                file_size = os.path.getsize(temp_path)
                # Ensure the file has valid MP4 data (> 50KB)
                if file_size > 50000:
                    size_mb = file_size / (1024 * 1024)
                    print(f"CLIP DOWNLOADED ({size_mb:.2f} MB, attempt {attempt}/{MAX_RETRIES})", flush=True)
                    return temp_path, size_mb
                else:
                    # Clip recording might still be finishing
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    print(f"Clip incomplete ({file_size} bytes, attempt {attempt}/{MAX_RETRIES})", flush=True)
            elif response.status_code == 404:
                print(f"Clip not ready yet (404 Not Found, attempt {attempt}/{MAX_RETRIES})", flush=True)
            else:
                print(f"Frigate returned HTTP {response.status_code} (attempt {attempt}/{MAX_RETRIES})", flush=True)
        except requests.RequestException as e:
            print(f"Frigate connection error (attempt {attempt}/{MAX_RETRIES}): {e}", flush=True)

        time.sleep(RETRY_INTERVAL)

    return None, 0


def split_video_lossless(input_path: str, target_part_mb: float = 8.0) -> tuple:
    """
    Splits an MP4 file into parts strictly under 9.5MB using ffmpeg stream copy (-c copy).
    Preserves 100% original video resolution and quality with zero re-encoding (instant).
    Returns (split_dir, list_of_part_filepaths).
    """
    size_mb = os.path.getsize(input_path) / (1024 * 1024)
    if size_mb <= MAX_FILE_SIZE_MB:
        return None, [input_path]

    # Probe duration using ffprobe
    duration = 30.0
    try:
        res = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0 and res.stdout.strip():
            duration = float(res.stdout.strip())
    except Exception as e:
        print(f"Warning: ffprobe duration probe error: {e}", flush=True)

    num_parts = max(2, math.ceil(size_mb / target_part_mb))
    seg_dur = max(2.0, duration / num_parts)

    temp_dir = tempfile.mkdtemp(prefix='frigate_split_')
    out_pattern = os.path.join(temp_dir, 'part_%03d.mp4')

    print(f"SPLITTING LARGE VIDEO ({size_mb:.2f} MB > {MAX_FILE_SIZE_MB} MB) INTO {num_parts} LOSSLESS PARTS (~{seg_dur:.1f}s each)...", flush=True)

    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-i', input_path,
        '-c', 'copy',
        '-map', '0',
        '-f', 'segment',
        '-segment_time', str(seg_dur),
        '-reset_timestamps', '1',
        out_pattern
    ]

    try:
        subprocess.run(cmd, check=True, timeout=60)
        parts = sorted(glob.glob(os.path.join(temp_dir, 'part_*.mp4')))
        if parts:
            print(f"SPLIT SUCCESSFUL: Generated {len(parts)} parts.", flush=True)
            return temp_dir, parts
    except Exception as e:
        print(f"ERROR during ffmpeg lossless splitting: {e}", flush=True)

    # Fallback if split fails
    return temp_dir, [input_path]


def upload_to_discord(event_data: dict, video_path: str, size_mb: float, part_num: int = 1, total_parts: int = 1) -> bool:
    """
    Sends the event video to Discord formatted with a beautiful Discord Rich Embed card.
    """
    webhook_url = get_discord_webhook_url()
    if not webhook_url:
        print("ERROR: No Discord webhook URL configured (checked environment and ~/.notify-discord.json)", flush=True)
        return False

    event_id = event_data.get("id", "unknown")
    camera = event_data.get("camera", "unknown")
    label = event_data.get("label", "unknown")
    start_time = event_data.get("start_time")

    # Time formatting for Discord Embed
    time_display = "Just now"
    if start_time:
        try:
            ts = int(float(start_time))
            time_display = f"<t:{ts}:F> (<t:{ts}:R>)"
        except Exception:
            time_display = str(start_time)

    # Dynamic Embed Colors based on detected label
    label_lower = label.lower()
    if "person" in label_lower:
        color = 15158332  # Red / Crimson
    elif "car" in label_lower or "vehicle" in label_lower:
        color = 3447003   # Blue
    elif "dog" in label_lower or "cat" in label_lower or "animal" in label_lower:
        color = 15844367  # Gold / Yellow
    elif "package" in label_lower or "delivery" in label_lower:
        color = 3066993   # Green
    else:
        color = 10181046  # Purple

    # Build Header Title
    if total_parts > 1:
        title = f"🚨 Frigate Detection Alert: {camera} [Part {part_num}/{total_parts}]"
        footer_text = f"Frigate NVR • High-Res Recording • Part {part_num} of {total_parts} ({size_mb:.2f} MB)"
    else:
        title = f"🚨 Frigate Detection Alert: {camera}"
        footer_text = f"Frigate NVR • High-Res Recording ({size_mb:.2f} MB)"

    # Build Discord Rich Embed Object
    embed = {
        "title": title,
        "color": color,
        "fields": [
            {"name": "📷 Camera", "value": f"`{camera}`", "inline": True},
            {"name": "🎯 Detected", "value": f"`{label.capitalize()}`", "inline": True},
            {"name": "🕒 Time", "value": time_display, "inline": False},
            {"name": "🆔 Event ID", "value": f"`{event_id}`", "inline": False}
        ],
        "footer": {
            "text": footer_text
        }
    }

    part_desc = f" (Part {part_num}/{total_parts}, {size_mb:.2f} MB)" if total_parts > 1 else f" ({size_mb:.2f} MB)"
    print(f"DISCORD UPLOAD STARTED{part_desc}", flush=True)

    filename = f"{camera}_{event_id}_part{part_num}.mp4" if total_parts > 1 else f"{camera}_{event_id}.mp4"

    try:
        with open(video_path, "rb") as vf:
            files = {
                "files[0]": (filename, vf, "video/mp4")
            }
            payload = {
                "embeds": [embed]
            }
            response = requests.post(
                webhook_url,
                data={"payload_json": json.dumps(payload)},
                files=files,
                timeout=120
            )

        if response.status_code not in (200, 204):
            print(f"ERROR: Discord API returned status {response.status_code}: {response.text}", flush=True)
            return False

        print(f"DISCORD UPLOAD SUCCESSFUL{part_desc}", flush=True)
        return True
    except requests.Timeout:
        print(f"ERROR: Discord upload timed out after 120 seconds{part_desc}", flush=True)
        return False
    except Exception as e:
        print(f"ERROR: Discord upload exception{part_desc}: {e}", flush=True)
        return False


def process_event_worker(event_data: dict):
    """
    Background worker thread:
    1. Downloads clip from Frigate.
    2. If clip > 9.5MB, splits into lossless parts (<9.5MB each).
    3. Uploads each part to Discord with Rich Embeds.
    4. Deletes all temporary files in finally block.
    """
    event_id = event_data.get("id")
    camera = event_data.get("camera", "unknown")
    label = event_data.get("label", "unknown")

    print(f"EVENT ID: {event_id}", flush=True)
    print(f"CAMERA: {camera}", flush=True)
    print(f"LABEL: {label}", flush=True)

    # Test event check: skip download/upload
    if event_data.get("is_test") or str(event_id).upper().startswith("TEST"):
        print("TEST EVENT DETECTED: Skipping clip download and Discord upload.", flush=True)
        return

    frigate_url = resolve_frigate_url()
    video_path, size_mb = download_clip(event_id, frigate_url)

    if not video_path:
        print(f"ERROR: Unable to obtain clip for event {event_id} from {frigate_url}", flush=True)
        return

    split_dir = None
    try:
        split_dir, parts = split_video_lossless(video_path, target_part_mb=8.0)
        total_parts = len(parts)

        for idx, part_file in enumerate(parts, 1):
            part_size_mb = os.path.getsize(part_file) / (1024 * 1024)
            upload_to_discord(event_data, part_file, part_size_mb, part_num=idx, total_parts=total_parts)
            # Brief pause between multi-part uploads
            if total_parts > 1 and idx < total_parts:
                time.sleep(1.0)
    finally:
        # Clean up original temp file
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception as err:
                print(f"Warning: Failed to delete temp file {video_path}: {err}", flush=True)

        # Clean up split directory and files
        if split_dir and os.path.exists(split_dir):
            try:
                shutil.rmtree(split_dir, ignore_errors=True)
            except Exception as err:
                print(f"Warning: Failed to delete split directory {split_dir}: {err}", flush=True)


@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    frigate_active = resolve_frigate_url()
    webhook_configured = bool(get_discord_webhook_url())
    return jsonify({
        "status": "healthy",
        "service": "frigate-discord-video",
        "frigate_url": frigate_active,
        "discord_webhook_configured": webhook_configured,
        "max_file_size_mb": MAX_FILE_SIZE_MB
    }), 200


@app.route("/", methods=["POST"])
@app.route("/webhook", methods=["POST"])
@app.route("/frigate", methods=["POST"])
@app.route("/notify", methods=["POST"])
def webhook_handler():
    """Webhook receiver endpoint."""
    print("\n" + "=" * 40, flush=True)
    print("WEBHOOK RECEIVED", flush=True)

    event_data, raw_body = parse_webhook_payload(request)

    if not event_data.get("id"):
        print("ERROR: Missing or unparseable event ID in webhook payload.", flush=True)
        print(f"Raw body received: {raw_body}", flush=True)
        print("=" * 40, flush=True)
        return jsonify({
            "error": "Missing event ID",
            "raw_received": raw_body
        }), 400

    event_id = event_data["id"]

    # Duplicate check
    if is_duplicate(event_id):
        print(f"EVENT ID: {event_id} (DUPLICATE - IGNORED)", flush=True)
        print("=" * 40, flush=True)
        return jsonify({
            "status": "ignored_duplicate",
            "event_id": event_id
        }), 200

    # Record event
    record_event(event_id)

    # Asynchronous worker thread
    worker = threading.Thread(target=process_event_worker, args=(event_data,), daemon=True)
    worker.start()

    print("=" * 40, flush=True)
    return jsonify({
        "status": "accepted",
        "event_id": event_id,
        "camera": event_data["camera"],
        "label": event_data["label"],
        "is_test": event_data["is_test"]
    }), 200


if __name__ == "__main__":
    print("==========================================", flush=True)
    print(" Frigate -> Discord Video Receiver Service", flush=True)
    print(" (Rich Embed Edition + Lossless Splitter) ", flush=True)
    print("==========================================", flush=True)
    active_url = resolve_frigate_url()
    print(f"Frigate API URL: {active_url}", flush=True)
    print(f"Discord Webhook: {bool(get_discord_webhook_url())}", flush=True)
    print(f"Listening on:    http://0.0.0.0:{PORT}", flush=True)
    print("==========================================", flush=True)

    app.run(host="0.0.0.0", port=PORT, threaded=True)
