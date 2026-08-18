# Testing & Monitoring Guide

## Endpoints

- **`GET /`**: Health Check Endpoint
- **`POST /`**: Webhook Receiver Endpoint

---

## Verification Commands

### 1. Service Health Check
Verify that the service is running and listening:
```bash
curl -v http://localhost:5001/
```
**Expected Response**: `HTTP 200 OK` with body `Frigate Discord Video service OK`.

### 2. Dry-Run Webhook Test
Simulate a Frigate-Notify test payload without triggering clip downloads or Discord uploads:
```bash
curl -v -X POST http://localhost:5001/ \
  -H "Content-Type: application/json" \
  -d '{"id":"TEST123","camera":"front","label":"person"}'
```
**Expected Response**: `HTTP 200 OK` with JSON `{"is_test": true, "status": "accepted"}`.

---

## Logs & Monitoring

### Docker Logs
```bash
docker logs -f frigate-discord-video
```

### Systemd Logs
```bash
journalctl -u frigate-discord-video -f
```
