# --- Étape 1 : Build du Frontend ---
FROM node:20-slim AS build-frontend
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# --- Étape 2 : Image Finale ---
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# On s'assure que le dossier dist existe avant de copier
RUN mkdir -p /app/dist
COPY --from=build-frontend /app/dist /app/dist

ENV TF_CONFIG_DIR=/config
EXPOSE 5000

CMD ["python", "main.py"]