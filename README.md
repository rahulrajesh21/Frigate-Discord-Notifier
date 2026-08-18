# Frigate Discord Video Receiver

An asynchronous bridge that sends high-resolution recorded event video clips from [Frigate](https://github.com/blakeblackshear/frigate) NVR directly to [Discord](https://discord.com) channels (Home Assistant not required). Powered by [Frigate-Notify](https://github.com/0x2142/frigate-notify) webhooks, [Flask](https://flask.palletsprojects.com/), and the [notify-discord](https://github.com/jlandowner/notify-discord) CLI.

[**View Documentation**](https://rahulrajesh21.github.io/Frigate-Discord-Notifier/)

---

## Features

- **High-Resolution Clips**: Downloads full-resolution recorded event clips (`/api/events/<ID>/clip.mp4`) from Frigate's recording stream rather than low-resolution detection substreams.
- **Asynchronous Processing**: Responds immediately with `HTTP 200` to webhooks while clip recording finalizes in the background.
- **Retry & Polling**: Retries fetching clips with configurable backoff while Frigate completes recording segments.
- **Deduplication Engine**: In-memory cache prevents repeated video uploads for duplicate event triggers.
- **Auto-Discovery**: Validates and discovers active Frigate instances on local Docker bridges.

---

## Quick Start

### Docker Compose

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Set `DISCORD_WEBHOOK_URL` in `.env`:
   ```ini
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   ```

3. Start the container:
   ```bash
   docker compose up -d --build
   ```

### Native Execution

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

---

## Resources & Dependencies

- [Frigate NVR](https://github.com/blakeblackshear/frigate) — Real-time NVR with local AI object detection
- [Frigate-Notify](https://github.com/0x2142/frigate-notify) — Lightweight alert notification service for Frigate
- [notify-discord CLI](https://github.com/jlandowner/notify-discord) — CLI tool for sending messages and files to Discord via webhooks
- [Flask Web Framework](https://flask.palletsprojects.com/) — Lightweight Python WSGI web application framework
- [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) — Standard Discord webhook API

---

## Documentation

Full installation guides, Systemd unit configuration, Frigate-Notify templates, and troubleshooting details are available on GitHub Pages:

👉 **[https://rahulrajesh21.github.io/Frigate-Discord-Notifier/](https://rahulrajesh21.github.io/Frigate-Discord-Notifier/)**

- [Installation & Prerequisites](docs/setup.md)
- [Configuration Reference](docs/configuration.md)
- [Testing & Troubleshooting](docs/testing.md)

---

## License

[MIT](LICENSE)
