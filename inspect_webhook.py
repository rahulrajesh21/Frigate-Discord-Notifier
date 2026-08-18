#!/usr/bin/env python3
"""
Webhook Payload Inspector for Frigate-Notify
Runs on port 5001 to capture, pretty-print, and inspect the exact JSON payload
sent by Frigate-Notify during real events without performing downloads or uploads.
"""

from flask import Flask, request, jsonify
import json
import sys

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return "Frigate Discord Video service OK\n", 200

@app.route("/", methods=["POST"])
def inspect_payload():
    print("\n" + "=" * 60, flush=True)
    print(">>> RAW WEBHOOK RECEIVED <<<", flush=True)
    print(f"Headers:\n{request.headers}", flush=True)
    
    raw_body = request.get_data(as_text=True)
    print(f"Raw Body:\n{raw_body}", flush=True)
    
    json_data = request.get_json(silent=True)
    if json_data is not None:
        print("Parsed JSON Payload:", flush=True)
        print(json.dumps(json_data, indent=2), flush=True)
    else:
        print("Body could not be parsed as JSON (Content-Type may not be application/json)", flush=True)
    print("=" * 60 + "\n", flush=True)
    
    return jsonify({
        "status": "received",
        "message": "Payload logged successfully"
    }), 200

if __name__ == "__main__":
    port = 5001
    print("=" * 60, flush=True)
    print(f" Webhook Inspector listening on http://0.0.0.0:{port}")
    print(" Trigger a Frigate event or run a test curl to view payload")
    print("=" * 60, flush=True)
    app.run(host="0.0.0.0", port=port)
