# Frigate Discord Video Receiver Documentation

An asynchronous notification bridge that sends high-resolution recorded event video clips from [Frigate](https://github.com/blakeblackshear/frigate) NVR directly to [Discord](https://discord.com) channels (Home Assistant not required). Built with [Frigate-Notify](https://github.com/0x2142/frigate-notify) webhooks, [Flask](https://flask.palletsprojects.com/), and the [notify-discord](https://github.com/jlandowner/notify-discord) CLI.

---

## Key Features

- **High-Resolution Clips**: Downloads the full-resolution event clip (`/api/events/<EVENT_ID>/clip.mp4`) from Frigate's recording stream rather than low-resolution detection substreams.
- **Asynchronous Architecture**: Responds instantly with `HTTP 200` to incoming webhooks to avoid timeouts while clip recording completes in the background.
- **Deduplication Engine**: In-memory cache prevents duplicate video uploads for repeated event triggers within a 15-minute window.
- **Frigate Auto-Discovery**: Automatically validates and discovers active Frigate instances on local Docker bridges.
- **Secure Credentials**: Reads credentials from environment variables or standard config files (`.env` / `~/.notify-discord.json`).
- **Automatic Cleanup**: Removes temporary MP4 video files immediately after upload.

---

## Resources & Integrations

- [Frigate NVR](https://github.com/blakeblackshear/frigate) — Real-time NVR with local AI object detection
- [Frigate-Notify](https://github.com/0x2142/frigate-notify) — Lightweight alert notification service for Frigate
- [notify-discord CLI](https://github.com/jlandowner/notify-discord) — CLI tool for sending messages and files to Discord via webhooks
- [Flask](https://flask.palletsprojects.com/) — Python web framework powering the webhook receiver
- [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) — Discord integration protocol

---

## Documentation Index

- [Installation & Setup](setup.md) - Deploy via Docker Compose or Systemd service.
- [Configuration](configuration.md) - Configure Frigate-Notify webhooks and environment settings.
- [Testing & Troubleshooting](testing.md) - Perform health checks, dry-run tests, and monitor logs.

---

## Project Repository

Source code and release issues are managed on GitHub:  
👉 [https://github.com/rahulrajesh21/Frigate-Discord-Notifier](https://github.com/rahulrajesh21/Frigate-Discord-Notifier)
