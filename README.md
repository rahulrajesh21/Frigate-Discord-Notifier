# Frigate Discord Video Receiver

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A complete and local notification bridge that sends high-resolution recorded event video clips from [Frigate](https://github.com/blakeblackshear/frigate) NVR to [Discord](https://discord.com) channels. Home Assistant not required.

Uses [Frigate-Notify](https://github.com/0x2142/frigate-notify) webhooks to receive event triggers and the [notify-discord](https://github.com/jlandowner/notify-discord) CLI to upload video clips. Built on [Flask](https://flask.palletsprojects.com/) for a lightweight, asynchronous webhook receiver.

- Downloads the full-resolution recorded event clip from Frigate's recording stream rather than the low-res detection substream
- Immediately responds with `HTTP 200` to prevent webhook timeouts while clip recording finalizes in the background
- Retries fetching clips with configurable backoff while Frigate closes recording segments on disk
- Built-in in-memory deduplication cache prevents repeated video uploads for the same event ID
- Validates and auto-discovers active Frigate instances on local Docker bridge networks
- Reads credentials from environment variables or config files — zero hardcoded secrets
- Automatically removes temporary MP4 files after upload attempts

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

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
