# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package.json ./
# Install Node dependencies
RUN npm install
# Copy frontend source and build
COPY . .
RUN npm run build

# Stage 2: Final production image
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (mktorrent is required by the backend for torrent creation)
RUN apt-get update && apt-get install -y \
    mktorrent \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the built frontend from Stage 1 to where Flask expects it
COPY --from=frontend-builder /app/dist ./dist

# Copy backend source code and manifest
COPY main.py manifest.json ./

# Ensure necessary directories exist for data and configuration
RUN mkdir -p /config /data/series /data/movies /data/torrents

# Expose the backend port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=main.py
ENV CONFIG_PATH=/config/config.json

# Start the application
CMD ["python", "main.py"]