from fastapi import FastAPI

app = FastAPI(title="API Certificaciones Médicas - Panamá")


@app.get("/health")
def health():
    return {"status": "ok"}