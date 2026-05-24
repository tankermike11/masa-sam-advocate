# Stage 1: build React
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY config/ ./config/

COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p /data

# TEMPORARY — remove after seed deploy
COPY data/pilot.db /app/backend/data/pilot.db

ENV PYTHONPATH=/app
ENV DATA_DIR=/data

EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
