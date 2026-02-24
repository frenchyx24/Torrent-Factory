# Stage 1: Build frontend with Node.js
FROM node:18-slim AS frontend-builder

WORKDIR /app

# Install pnpm globally
RUN npm install -g pnpm@latest

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy all config files
COPY tsconfig*.json vite.config.ts postcss.config.js tailwind.config.ts ./
COPY eslint.config.js ./
COPY src/ ./src/
COPY public/ ./public/

# Build frontend
RUN pnpm build

# Stage 2: Runtime with Python backend + frontend files
FROM python:3.11-slim

# Installation de mktorrent (l'outil stable pour créer des torrents)
RUN apt-get update \
    && apt-get install -y --no-install-recommends mktorrent ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY main.py .
COPY scripts/ ./scripts/
COPY manifest.json .

# Copy prebuilt frontend from stage 1
COPY --from=frontend-builder /app/dist ./dist

# Création de la structure de dossiers utilisées en runtime
RUN mkdir -p config data/series data/movies data/torrents/series data/torrents/movies \
    && chmod -R 755 config data dist || true

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

# Créer un utilisateur non-root pour exécuter l'application
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app \
    && chown -R app:app /app /config /data || true

USER app

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]