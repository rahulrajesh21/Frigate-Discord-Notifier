# Installation & Setup Guide

This guide details how to install `notify-discord` and deploy the service using either Docker Compose or Systemd.

---

## Prerequisites

### 1. Python Environment
Python 3.10+ is required when running natively (outside of Docker).

### 2. Install `notify-discord` CLI
Download the appropriate binary for your system architecture:

#### Linux (x86_64)
```bash
curl -sSL https://github.com/jlandowner/notify-discord/releases/latest/download/notify-discord-x86_64-unknown-linux-gnu.tgz \
  | sudo tar -xz -C /usr/local/bin/ notify-discord
sudo chmod +x /usr/local/bin/notify-discord
```

#### macOS (Apple Silicon - M1/M2/M3/M4 / ARM64)
```bash
curl -sSL https://github.com/jlandowner/notify-discord/releases/latest/download/notify-discord-aarch64-apple-darwin.tgz \
  | sudo tar -xz -C /usr/local/bin/ notify-discord
sudo chmod +x /usr/local/bin/notify-discord
```

#### macOS (Intel - x86_64)
```bash
curl -sSL https://github.com/jlandowner/notify-discord/releases/latest/download/notify-discord-x86_64-apple-darwin.tgz \
  | sudo tar -xz -C /usr/local/bin/ notify-discord
sudo chmod +x /usr/local/bin/notify-discord
```

### 3. Configure Webhook Secret
Create `~/.notify-discord.json` or set `DISCORD_WEBHOOK_URL` in your `.env` file:
```json
{
  "webhook-url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
}
```

---

## Deployment Options

### Option A: Docker Compose (Recommended)

1. **Copy Environment Configuration:**
   ```bash
   cp .env.example .env
   ```
   > **Note:** In Docker mode, specify `DISCORD_WEBHOOK_URL` in `.env` as host configuration files (`~/.notify-discord.json`) are not mounted inside the container by default.

2. **Verify Docker Network:**
   `docker-compose.yml` connects to an external network named `frigate_default`. Ensure this network exists or create it:
   ```bash
   docker network create frigate_default
   ```

3. **Start Container:**
   ```bash
   docker compose up -d --build
   ```

---

### Option B: Systemd Service (Linux)

1. **Clone Repository & Setup Virtual Environment:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/frigate-discord-video.git
   cd frigate-discord-video
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your FRIGATE_URL, DISCORD_WEBHOOK_URL, and PORT
   ```

3. **Configure & Enable Systemd Unit:**
   Edit `frigate-discord-video.service` to match your user and installation directory:
   ```ini
   [Unit]
   Description=Frigate Discord Video Notification Service
   After=network.target docker.service

   [Service]
   Type=simple
   User=YOUR_USERNAME
   WorkingDirectory=/path/to/frigate-discord-video
   EnvironmentFile=-/path/to/frigate-discord-video/.env
   ExecStart=/path/to/frigate-discord-video/venv/bin/python3 /path/to/frigate-discord-video/server.py
   Restart=always
   ```
   Then enable and start the unit:
   ```bash
   sudo cp frigate-discord-video.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable frigate-discord-video
   sudo systemctl start frigate-discord-video
   ```
