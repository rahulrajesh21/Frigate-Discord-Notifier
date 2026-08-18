# Installation & Setup

## Prerequisites

### Python

Python 3.10+ is required when running natively (outside Docker).

### notify-discord CLI

Download the appropriate binary for your platform:

**Linux (x86_64):**
```bash
curl -sSL https://github.com/jlandowner/notify-discord/releases/latest/download/notify-discord-x86_64-unknown-linux-gnu.tgz \
  | sudo tar -xz -C /usr/local/bin/ notify-discord
sudo chmod +x /usr/local/bin/notify-discord
```

**macOS (Apple Silicon):**
```bash
curl -sSL https://github.com/jlandowner/notify-discord/releases/latest/download/notify-discord-aarch64-apple-darwin.tgz \
  | sudo tar -xz -C /usr/local/bin/ notify-discord
sudo chmod +x /usr/local/bin/notify-discord
```

**macOS (Intel):**
```bash
curl -sSL https://github.com/jlandowner/notify-discord/releases/latest/download/notify-discord-x86_64-apple-darwin.tgz \
  | sudo tar -xz -C /usr/local/bin/ notify-discord
sudo chmod +x /usr/local/bin/notify-discord
```

### Discord Webhook

Create `~/.notify-discord.json` or set `DISCORD_WEBHOOK_URL` in your `.env` file:
```json
{
  "webhook-url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
}
```

---

## Docker Compose (Recommended)

1. Copy and edit the environment file:
   ```bash
   cp .env.example .env
   ```

   **Note:** In Docker mode, `DISCORD_WEBHOOK_URL` must be set in `.env` because host config files (`~/.notify-discord.json`) are not mounted inside the container.

2. Verify the Docker network exists. `docker-compose.yml` connects to an external network named `frigate_default`. Ensure it exists or create it:
   ```bash
   docker network create frigate_default
   ```
   If your Frigate container uses a different network name, edit `networks` in `docker-compose.yml` accordingly.

3. Start the container:
   ```bash
   docker compose up -d --build
   ```

---

## Systemd Service (Linux)

1. Clone and set up:
   ```bash
   git clone https://github.com/rahulrajesh21/Frigate-Discord-Notifier.git
   cd Frigate-Discord-Notifier
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your FRIGATE_URL, DISCORD_WEBHOOK_URL, and PORT
   ```

3. Edit `frigate-discord-video.service` to match your system:
   ```ini
   User=your_username
   WorkingDirectory=/path/to/Frigate-Discord-Notifier
   EnvironmentFile=-/path/to/Frigate-Discord-Notifier/.env
   ExecStart=/path/to/Frigate-Discord-Notifier/venv/bin/python3 /path/to/Frigate-Discord-Notifier/server.py
   ```

4. Enable and start:
   ```bash
   sudo cp frigate-discord-video.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable frigate-discord-video
   sudo systemctl start frigate-discord-video
   ```
