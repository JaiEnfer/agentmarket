FROM node:22-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY payer/package.json payer/package-lock.json ./payer/
RUN cd payer && npm ci

COPY payer ./payer
COPY agent ./agent

RUN python3 -m venv /app/.venv \
    && /app/.venv/bin/pip install --no-cache-dir -r agent/requirements.txt

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8501

CMD ["streamlit", "run", "agent/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]