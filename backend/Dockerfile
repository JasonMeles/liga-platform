# 1. Image de base : Python 3.12 léger (pas de gros outils inutiles)
FROM python:3.12-slim

# 2. Dossier de travail à l'intérieur du container
WORKDIR /app

# 3. Installer uv (le gestionnaire de paquets que tu utilises déjà)
RUN pip install uv

# 4. Copier UNIQUEMENT les fichiers de dépendances d'abord (cache layer)
COPY pyproject.toml uv.lock ./

# 5. Installer les dépendances (cette étape reste en cache tant que
#    pyproject.toml/uv.lock ne changent pas)
RUN uv sync --frozen --no-dev

# 6. Copier le reste du code (change souvent, donc placé APRÈS)
COPY app/ ./app/

# 7. Copier les fichiers de configuration d'Alembic
COPY alembic.ini ./
COPY alembic/ ./alembic/

# 8. Exposer le port sur lequel uvicorn va écouter
EXPOSE 8000

# 9. Commande de démarrage du container
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]