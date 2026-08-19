# Configuration

## Environment Variables

Configure service parameters in `.env` (auto-loaded on startup) or set them as real environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `FRIGATE_URL` | `http://172.18.0.2:5000` | URL of the Frigate NVR instance API |
| `PORT` | `5001` | Local port for receiving webhooks |
| `DISCORD_WEBHOOK_URL` | *(empty)* | Discord Webhook URL — also checked in `~/.notify-discord.json` |
| `MAX_RETRIES` | `15` | Maximum retry attempts while waiting for clip finalization |
| `RETRY_INTERVAL` | `4` | Seconds between clip download retries |
| `MAX_FILE_SIZE_MB` | `9.5` | Clips above this size (MB) are split into lossless parts before upload |

> **Note:** Discord's standard webhook upload limit is **10 MB**. The default threshold of `9.5 MB` provides a safe buffer. Clips exceeding this are automatically split using `ffmpeg -c copy` (zero re-encoding).

---

## Frigate-Notify Webhook

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

---

## Frigate Native Webhook (Alternative)

The service also accepts Frigate's native `{"before": {...}, "after": {...}}` webhook format directly. No Frigate-Notify is required in this case — point Frigate's webhook at `http://<RECEIVER_HOST_IP>:5001/webhook`.

---

## Webhook URL

The Discord webhook URL is resolved in this order:

1. `DISCORD_WEBHOOK_URL` environment variable
2. `DISCORD_WEBHOOK` environment variable
3. `~/.notify-discord.json` → `webhook-url` or `webhook_url` key
