FROM python:3.11-slim

# Install system dependencies
# We need snapraid to run snapraid commands.
# Since snapraid might not be in the default repos or might be old, we might need to build it or get it from a PPA.
# However, for simplicity and robustness, let's try to install it from apt if available, or assume the user wants us to use the host's binary mapped in?
# The spec says: "SnapRAID command runner that shells out to `snapraid`".
# It's safer to have the binary inside. Let's check if it's in debian bookworm.
# It is usually available.
RUN apt-get update && apt-get install -y \
    snapraid \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot_main.py"]
