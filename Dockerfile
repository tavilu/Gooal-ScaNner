FROM python:3.11-slim

# -----------------------------------
# 1) PREPARO DO AMBIENTE
# -----------------------------------
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# -----------------------------------
# 2) INSTALAÇÃO DAS DEPENDÊNCIAS
# -----------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------
# 3) COPIAR PROJETO
# -----------------------------------
COPY . .

EXPOSE 8000

# -----------------------------------
# 4) EXECUÇÃO DO SERVIDOR FASTAPI/GUNICORN
# -----------------------------------
CMD ["gunicorn", "app:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--threads", "2", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5"]
