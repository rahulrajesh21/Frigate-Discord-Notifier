# Frigate Discord Video Receiver

A complete and local notification bridge that sends high-resolution recorded event video clips from [Frigate](https://github.com/blakeblackshear/frigate) NVR to [Discord](https://discord.com) channels. Home Assistant not required.

Uses [Frigate-Notify](https://github.com/0x2142/frigate-notify) webhooks to receive event triggers and the [notify-discord](https://github.com/jlandowner/notify-discord) CLI to upload video clips. Built on [Flask](https://flask.palletsprojects.com/) for a lightweight, asynchronous webhook receiver.

- Downloads the full-resolution recorded event clip from Frigate's recording stream rather than the low-res detection substream
- Immediately responds with `HTTP 200` to prevent webhook timeouts while clip recording finalizes in the background
- Retries fetching clips with configurable backoff while Frigate closes recording segments on disk
- Built-in in-memory deduplication cache prevents repeated video uploads for the same event ID
- Validates and auto-discovers active Frigate instances on local Docker bridge networks
- Reads credentials from environment variables or config files — zero hardcoded secrets
- Automatically removes temporary MP4 files after upload attempts

## Getting Started

- [Installation & Setup](setup.md)
- [Configuration](configuration.md)
- [Testing & Troubleshooting](testing.md)

## Resources

- [Frigate NVR](https://github.com/blakeblackshear/frigate) — Realtime object detection NVR for IP cameras
- [Frigate-Notify](https://github.com/0x2142/frigate-notify) — Lightweight alert notification service for Frigate
- [notify-discord](https://github.com/jlandowner/notify-discord) — CLI tool for posting messages and files to Discord via webhooks
- [Flask](https://flask.palletsprojects.com/) — Python WSGI web application framework
- [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) — Discord webhook integration

## Project Repository

Source code is available on GitHub: [rahulrajesh21/Frigate-Discord-Notifier](https://github.com/rahulrajesh21/Frigate-Discord-Notifier)
