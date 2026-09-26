FROM python:3.12-bookworm

# Install Node.js 22
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node dependencies first for better Docker caching
COPY payer/package.json payer/package-lock.json ./payer/
RUN cd payer && npm ci

# Install Python dependencies
COPY agent/requirements.txt ./agent/requirements.txt

RUN python -m venv /app/.venv \
    && /app/.venv/bin/pip install --no-cache-dir -r agent/requirements.txt

# Copy application code
COPY payer ./payer
COPY agent ./agent

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8501

CMD sh -c 'streamlit run agent/app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true'