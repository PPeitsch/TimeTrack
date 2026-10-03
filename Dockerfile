FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_APP=run.py

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN useradd --create-home --uid 1000 timetrack \
    && mkdir -p /app/uploads /data \
    && chown timetrack:timetrack /app/uploads /data

COPY --chown=timetrack:timetrack app ./app
COPY --chown=timetrack:timetrack migrations ./migrations
COPY --chown=timetrack:timetrack run.py ./
COPY --chown=timetrack:timetrack docker/entrypoint.sh /usr/local/bin/entrypoint.sh

USER timetrack
EXPOSE 8000

ENTRYPOINT ["entrypoint.sh"]
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --access-logfile - run:app"]
