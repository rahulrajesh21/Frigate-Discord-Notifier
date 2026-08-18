# Testing & Monitoring

## Endpoints

- `GET /` — Health check
- `POST /` — Webhook receiver

---

## Health Check

Verify the service is running:
```bash
curl -v http://localhost:5001/
```
Expected: `HTTP 200 OK` with body `Frigate Discord Video service OK`.

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
