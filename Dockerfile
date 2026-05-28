FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

ENV SECRET_KEY=build-placeholder
RUN python manage.py collectstatic --noinput

USER appuser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV WORKERS=3

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn recipe_saver.wsgi:application --bind 0.0.0.0:$PORT --workers $WORKERS"]
