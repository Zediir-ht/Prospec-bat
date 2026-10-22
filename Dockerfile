FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY prospec ./prospec
ENV PORT=8000
VOLUME /app/data
# 1 seul worker : le suivi du job en cours est gardé en mémoire
CMD ["sh", "-c", "gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT prospec.web:app"]
