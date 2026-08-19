# Frigate Discord Video Receiver

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A complete and local notification bridge that sends high-resolution recorded event video clips from [Frigate](https://github.com/blakeblackshear/frigate) NVR to [Discord](https://discord.com) channels via **Discord Rich Embeds**. Home Assistant not required.

Uses [Frigate-Notify](https://github.com/0x2142/frigate-notify) webhooks (or Frigate's native webhooks) to receive event triggers, fetches the full-resolution clip from Frigate's recording API, and uploads it directly to Discord. Built on [Flask](https://flask.palletsprojects.com/) for a lightweight, asynchronous webhook receiver.

- Downloads the full-resolution recorded event clip from Frigate's recording stream rather than the low-res detection substream
- Immediately responds with `HTTP 200` to prevent webhook timeouts while clip recording finalizes in the background
- Retries fetching clips with configurable backoff while Frigate closes recording segments on disk
- **Automatically splits clips larger than 9.5 MB** into lossless parts using `ffmpeg -c copy` (zero re-encoding, instant)
- Sends each part with a **Discord Rich Embed** card — color-coded by detected label, with camera, timestamp, and event ID fields
- Built-in in-memory deduplication cache prevents repeated video uploads for the same event ID
- Validates and auto-discovers active Frigate instances on local Docker bridge networks
- Reads credentials from environment variables, `.env` file, or `~/.notify-discord.json` — zero hardcoded secrets
- Automatically removes all temporary MP4 files after upload attempts

## Why This Service Is Needed

Standard [Frigate-Notify](https://github.com/0x2142/frigate-notify) natively supports sending static image snapshots (`snapshot.jpg`) and text notifications, but cannot send full-resolution video clips (`clip.mp4`) directly for several technical reasons:

- **Clip Availability Delay**: When Frigate detects an object and triggers a notification webhook, the recorded video clip is still actively being written to disk. The finalized `clip.mp4` is not available until after the event recording segment closes.
- **Webhook Timeouts**: Synchronous notification handlers time out if forced to wait for video segment finalization before responding.
- **Video Attachment Handling**: Uploading high-resolution MP4 video files to Discord webhooks requires asynchronous multipart file dispatching rather than simple JSON payloads.

This bridge service resolves these constraints by accepting webhooks instantly with `HTTP 200`, polling Frigate's clip API with configurable backoff until recording finalizes, splitting oversized clips losslessly if needed, and delivering the high-resolution MP4 file to Discord with a Rich Embed.

## Documentation

View the documentation at https://rahulrajesh21.github.io/Frigate-Discord-Notifier/

## Quick Start

### Docker Compose

```bash
cp .env.example .env
# Edit .env to set DISCORD_WEBHOOK_URL
docker compose up -d --build
```

### Native

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

> **Note:** `ffmpeg` must be available in your PATH (or install `static-ffmpeg` via pip — it is included in `requirements.txt` and loaded automatically).

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
