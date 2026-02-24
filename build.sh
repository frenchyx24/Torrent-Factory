#!/usr/bin/env bash
# Build script: install deps and build frontend + backend
set -euo pipefail

echo "🔧 Installing Node dependencies..."
pnpm install

echo "🏗️  Building frontend with Vite..."
pnpm build

echo "✅ Frontend build complete! Files in dist/"
ls -lah dist/ | head -20

echo "🐍 Python environment ready (Docker or venv)."
echo "   To run locally: source .venv/bin/activate && gunicorn -w 4 -b 0.0.0.0:5000 main:app"
echo "   To run Docker: docker compose up --build"
