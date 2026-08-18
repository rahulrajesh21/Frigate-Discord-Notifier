# Configuration Reference

This document outlines environment variables and Frigate-Notify webhook settings.

---

## Environment Variables (`.env`)

Configure service parameters in `.env`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `FRIGATE_URL` | `http://172.18.0.3:5000` | URL of the Frigate NVR instance API. |
| `PORT` | `5001` | Local port for receiving webhooks. |
| `DISCORD_WEBHOOK_URL` | *(empty)* | Optional Discord Webhook URL override. |
| `MAX_RETRIES` | `15` | Maximum retry attempts while waiting for clip finalization. |
| `RETRY_INTERVAL` | `4` | Seconds between clip download retries. |
| `MAX_FILE_SIZE_MB` | `24.5` | Max upload size limit (MB) to prevent Discord rejection. |

---

## Frigate-Notify Integration

Add the webhook provider under `alerts:` in your Frigate-Notify `config.yml`:

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
