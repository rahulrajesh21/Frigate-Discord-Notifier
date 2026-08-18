#!/usr/bin/env python3
"""
Frigate -> Discord High-Resolution Video Notification Service
Receives Frigate-Notify webhook triggers, fetches high-resolution event clips
from Frigate's recording API, and uploads them to Discord using notify-discord CLI.
"""

import os
import sys
import time
import json
import re
import tempfile
import threading
import subprocess
from datetime import datetime
from collections import OrderedDict
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configuration
FRIGATE_URL = os.environ.get("FRIGATE_URL", "http://172.18.0.3:5000")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", "5001"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "15"))
RETRY_INTERVAL = int(os.environ.get("RETRY_INTERVAL", "4"))
MAX_FILE_SIZE_MB = float(os.environ.get("MAX_FILE_SIZE_MB", "24.5"))

# In-memory deduplication cache
# Stores event_id -> timestamp (cleaned every 15 mins)
_seen_events = OrderedDict()
_seen_lock = threading.Lock()
DEDUP_CACHE_LIMIT = 500
DEDUP_TTL_SECONDS = 900  # 15 minutes


def is_duplicate(event_id: str) -> bool:
    """Checks if an event ID has already been processed recently."""
    now = time.time()
    with _seen_lock:
        # Evict old items
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
        "http://frigate:5000",
        "http://172.18.0.3:5000",
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

    # Fallback scan on docker bridge if container IP changed
    for i in range(2, 10):
        url = f"http://172.18.0.{i}:5000"
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
    Supports JSON, nested JSON, Go templates, and plain text.
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
        # Handle nested event object if present
        target = data.get("event") if isinstance(data.get("event"), dict) else data

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
                content_type = response.headers.get("Content-Type", "")
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


def upload_to_discord(event_data: dict, video_path: str, size_mb: float) -> bool:
    """
    Invokes notify-discord CLI to upload the event video to Discord.
    """
    event_id = event_data.get("id", "unknown")
    camera = event_data.get("camera", "unknown")
    label = event_data.get("label", "unknown")
    start_time = event_data.get("start_time")

    time_str = ""
    if start_time:
        try:
            ts = float(start_time)
            dt = datetime.fromtimestamp(ts)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            time_str = str(start_time)

    # Check maximum file size limit
    if size_mb > MAX_FILE_SIZE_MB:
        print(f"ERROR: Clip size ({size_mb:.2f} MB) exceeds max upload limit ({MAX_FILE_SIZE_MB} MB)", flush=True)
        return False

    message_lines = [
        "🚨 **Frigate Alert**",
        f"📷 **Camera:** `{camera}`",
        f"🎯 **Object:** `{label}`",
        f"🆔 **Event ID:** `{event_id}`"
    ]
    if time_str:
        message_lines.append(f"🕒 **Time:** `{time_str}`")

    message = "\n".join(message_lines)

    cmd = ["notify-discord", "--file", video_path]
    if DISCORD_WEBHOOK_URL:
        cmd.extend(["--webhook-url", DISCORD_WEBHOOK_URL])

    print("DISCORD UPLOAD STARTED", flush=True)
    try:
        result = subprocess.run(
            cmd,
            input=message,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"ERROR: notify-discord failed (exit {result.returncode})", flush=True)
            if result.stdout:
                print(f"Output: {result.stdout.strip()}", flush=True)
            if result.stderr:
                print(f"Error: {result.stderr.strip()}", flush=True)
            return False

        print("DISCORD UPLOAD SUCCESSFUL", flush=True)
        return True
    except subprocess.TimeoutExpired:
        print("ERROR: notify-discord timed out after 120 seconds", flush=True)
        return False
    except FileNotFoundError:
        print("ERROR: /usr/local/bin/notify-discord executable not found in PATH", flush=True)
        return False
    except Exception as e:
        print(f"ERROR: Discord upload exception: {e}", flush=True)
        return False


def process_event_worker(event_data: dict):
    """
    Background worker thread: downloads clip from Frigate and uploads to Discord.
    Deletes temporary file in finally block.
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

    try:
        upload_to_discord(event_data, video_path, size_mb)
    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception as err:
                print(f"Warning: Failed to delete temp file {video_path}: {err}", flush=True)


@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return "Frigate Discord Video service OK\n", 200


@app.route("/", methods=["POST"])
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
    print("==========================================", flush=True)
    active_url = resolve_frigate_url()
    print(f"Frigate API URL: {active_url}", flush=True)
    print(f"Listening on:    http://0.0.0.0:{PORT}", flush=True)
    print("==========================================", flush=True)

    app.run(host="0.0.0.0", port=PORT, threaded=True)
