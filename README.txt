Projeto gerado contendo backend (FastAPI) e frontend PWA.
- backend/.env já configurado com as chaves que você forneceu.
- Para rodar local:
  - python3 -m venv venv
  - source venv/bin/activate
  - pip install -r backend/requirements.txt
  - cd backend && uvicorn app:app --host 0.0.0.0 --port 8000
  - servir frontend (python -m http.server 8080) ou configurar backend para servir estático.
- Não compartilhe suas chaves. Este pacote contém sua REST API Key do OneSignal.
