# Testing & Monitoring

## Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check (JSON) |
| `GET` | `/health` | Health check (JSON, alias) |
| `POST` | `/` | Webhook receiver |
| `POST` | `/webhook` | Webhook receiver (alias) |
| `POST` | `/frigate` | Webhook receiver (alias) |
| `POST` | `/notify` | Webhook receiver (alias) |

---

## Health Check

Verify the service is running:
```bash
curl http://localhost:5001/health
```
Expected response:
```json
{
  "status": "healthy",
  "service": "frigate-discord-video",
  "frigate_url": "http://172.18.0.2:5000",
  "discord_webhook_configured": true,
  "max_file_size_mb": 9.5
}
```

---

## Dry-Run Webhook Test

Simulate a test event without triggering clip downloads or Discord uploads:
```bash
curl -v -X POST http://localhost:5001/ \
  -H "Content-Type: application/json" \
  -d '{"id":"TEST123","camera":"front","label":"person"}'
```
Expected: `HTTP 200 OK` with `{"is_test": true, "status": "accepted"}`.

---

## Logs

### Docker
```bash
docker logs -f frigate-discord-video
```

### Systemd
```bash
journalctl -u frigate-discord-video -f
```
