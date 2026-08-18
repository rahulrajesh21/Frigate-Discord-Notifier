# Frigate Discord Video Notification Service

A reliable, asynchronous bridge that sends **high-resolution recorded event video clips** from [Frigate NVR](https://github.com/blakeblackshear/frigate) to **Discord** channels via [Frigate-Notify](https://github.com/0x2142/frigate-notify) webhooks and the [`notify-discord`](https://github.com/jlandowner/notify-discord) CLI.

---

## 🎯 Features

- **High-Resolution Event Clips**: Automatically downloads the full-resolution recorded event clip (`/api/events/<EVENT_ID>/clip.mp4`) from Frigate's recording stream rather than the low-res detection substream.
- **Asynchronous Processing**: Immediately responds with `HTTP 200` to Frigate-Notify webhooks to prevent timeouts or retries while clip recording finalizes in the background.
- **Clip Readiness & Polling**: Retries fetching clips with configurable backoff while Frigate closes recording segments on disk.
- **Deduplication Engine**: Built-in in-memory deduplication cache prevents repeated video uploads for the same event ID.
- **Automatic Frigate Discovery**: Validates `FRIGATE_URL` and auto-discovers active Frigate instances on local Docker bridges (`172.18.0.x`).
- **Secure by Design**: Zero hardcoded Discord tokens or API credentials. Integrates with `.env`, systemd `EnvironmentFile`, or `~/.notify-discord.json`.
- **Automatic Temp File Cleanup**: Safely removes temporary MP4 files immediately after upload attempts in all execution branches.

---

## 🏗️ Architecture

```
 ┌─────────────────────────────────────────────────────────┐
 │ 🎥 Frigate NVR (0.18+)                                  │
 │   • Channel 101: High-Res Recording (2560x1440 / 1080p) │
 │   • Channel 102: Detection Stream (640x480)             │
 └────────────────────────────┬────────────────────────────┘
                              │ Detection Trigger
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 🔔 Frigate-Notify (v0.5.4+)                             │
 │   • Webhook: POST http://<receiver-ip>:5001             │
 └────────────────────────────┬────────────────────────────┘
                              │ Webhook Event (JSON / Text)
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 🐍 Frigate Discord Video Receiver (Port 5001)           │
 │   1. Immediate HTTP 200 acknowledgment                  │
 │   2. Deduplication check                                │
 │   3. Background worker: Polls /api/events/<ID>/clip.mp4 │
 │   4. Saves temporary MP4                                │
 │   5. Invokes `notify-discord` CLI with `--file`         │
 │   6. Automatically deletes temp MP4                     │
 └────────────────────────────┬────────────────────────────┘
                              │ notify-discord CLI
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 💬 Discord Channel (High-Resolution Video Clip)          │
 └─────────────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

- Python 3.10+
- `requests` and `flask`
- [`notify-discord`](https://github.com/jlandowner/notify-discord) installed at `/usr/local/bin/notify-discord`

To install `notify-discord`:
```bash
curl -sSL https://github.com/jlandowner/notify-discord/releases/latest/download/notify-discord-x86_64-unknown-linux-gnu.tgz \
  | sudo tar -xz -C /usr/local/bin/ notify-discord
sudo chmod +x /usr/local/bin/notify-discord
```

Configure your Discord webhook in `~/.notify-discord.json`:
```json
{
  "webhook-url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
}
```

---

## 🚀 Installation

### Option A: Systemd Service (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/frigate-discord-video.git
   cd frigate-discord-video
   ```

2. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env to set your FRIGATE_URL and PORT if different from defaults
   ```

4. **Install Systemd Unit:**
   ```bash
   sudo cp frigate-discord-video.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable frigate-discord-video
   sudo systemctl start frigate-discord-video
   ```

5. **Verify Service Status:**
   ```bash
   sudo systemctl status frigate-discord-video
   ```

---

### Option B: Docker Container

1. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```

2. **Start via Docker Compose:**
   ```bash
   docker compose up -d --build
   ```

---

## ⚙️ Frigate-Notify Configuration

Add or update the `webhook` provider under `alerts:` in your Frigate-Notify `config.yml`:

```yaml
alerts:
  webhook:
    enabled: true
    server: "http://<RECEIVER_HOST_IP>:5001"
    method: POST
    headers:
      - "Content-Type: application/json"
    template: |
      {
        "id": "{{ .ID }}",
        "camera": "{{ .Camera }}",
        "label": "{{ .Label }}",
        "start_time": {{ .StartTime }},
        "top_score": {{ .TopScore }}
      }
```

---

## 🧪 Testing

### 1. Health Check
```bash
curl -v http://localhost:5001/
```
**Expected Response:** `HTTP 200 OK` with `Frigate Discord Video service OK`.

### 2. Test Webhook (Dry-Run Mode)
```bash
curl -v -X POST http://localhost:5001/ \
  -H "Content-Type: application/json" \
  -d '{"id":"TEST123","camera":"east","label":"person"}'
```
**Expected Response:** `HTTP 200 OK` with `is_test: true`. (Dry-run mode skips video download and Discord upload).

---

## 📋 Logs & Monitoring

### Systemd Logs
```bash
journalctl -u frigate-discord-video -f
```

### Docker Logs
```bash
docker logs -f frigate-discord-video
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
