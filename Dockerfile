# Amazon-Orders-WebScraper as its own container.
#
# Everything that must outlive a run sits under one mounted directory, /data:
#   /data/receipts/          one HTML receipt per order (the -o folder)
#   /data/profile/           the Chromium profile: cookies carry over, so Amazon sees a known, signed-in device
#
# The browser runs headed on a virtual display (Xvfb), not with --headless: Amazon answers headless sessions
# with its "Sorry! Something went wrong" page. Chromium and chromedriver come from the same package set, so
# their versions match and nothing is downloaded at run time.
#
#   docker build -t amazon-orders-webscraper .
#   docker run --rm --env-file .env --user "$(id -u):$(id -g)" -v "$PWD/data:/data" amazon-orders-webscraper
#
# Extra arguments go to main.py.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.9 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    # Chromium wants a writable HOME; the container is meant to run as the host user (any uid).
    HOME=/home/app \
    AP_PROFILE_DIR=/data/profile

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium chromium-driver fonts-liberation xvfb xauth tini \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /home/app /data && chmod 1777 /home/app /data

WORKDIR /app

# Dependencies from the lock file, cached separately from the source.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY main.py pages.py ./

VOLUME /data
# tini as PID 1: xvfb-run waits for the X server's SIGUSR1 "ready" signal, which a container's PID 1 never
# receives (the kernel only delivers signals to PID 1 that it explicitly handles), so as PID 1 it waits forever.
# tini also reaps the browser processes a crashed run leaves behind.
ENTRYPOINT ["tini", "--", "xvfb-run", "-a", "-s", "-screen 0 1920x1080x24", \
            "python", "main.py", "-c", "/usr/bin/chromedriver", "-head", "false", "-o", "/data/receipts"]
