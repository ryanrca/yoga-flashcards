FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    default-mysql-client \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Bake the static files into the image so no runtime collectstatic is needed.
# This only reads app directories, never the database.
RUN DEBUG=0 DJANGO_SECRET_KEY=build-time-only python manage.py collectstatic --noinput

# Media is a mounted volume in production; keep the mount point present.
RUN mkdir -p /app/media

EXPOSE 8000

# Overridden by docker-compose (./start.sh) for local development.
CMD ["gunicorn", "yoga_flashcards.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
