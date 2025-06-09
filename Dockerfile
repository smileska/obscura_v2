FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=docker_settings

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        gettext \
        gcc \
        libc6-dev \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos '' appuser

RUN mkdir -p /app/static /app/staticfiles /app/media \
    && mkdir -p /app/media/chat_images /app/media/chatroom_images /app/media/profile_pics \
    && mkdir -p /app/templates \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app \
    && chmod -R 775 /app/media

USER appuser

RUN python manage.py collectstatic --noinput --settings=docker_settings || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "obscura.asgi:application"]