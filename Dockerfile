FROM python:3.11-slim

# Sécurité : ne pas tourner en root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copier uniquement les dépendances en premier (cache Docker optimisé)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source (sans .env grâce au .dockerignore)
COPY src/ ./src/
COPY start.sh ./

RUN chmod +x start.sh

ENV PYTHONPATH=/app/src

# Passer à l'utilisateur non-root
USER appuser

EXPOSE 8000

CMD ["./start.sh"]
