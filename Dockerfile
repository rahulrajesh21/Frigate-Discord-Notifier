FROM python:3.11-slim

WORKDIR /app

# Install curl and ca-certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install notify-discord binary
RUN curl -sSL https://github.com/jlandowner/notify-discord/releases/latest/download/notify-discord-x86_64-unknown-linux-gnu.tgz \
    | tar -xz -C /usr/local/bin/ notify-discord && \
    chmod +x /usr/local/bin/notify-discord

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

ENV PYTHONUNBUFFERED=1
EXPOSE 5001

CMD ["python", "server.py"]
