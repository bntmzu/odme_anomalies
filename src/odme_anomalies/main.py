from fastapi import FastAPI
from odme_anomalies.api.v1.router import router

app = FastAPI(
    title="ODME – Mythological Anomalies",
    description="Systém pro hlášení a sledování mytologických projevů",
    version="1.0.0",
)


@app.get("/", tags=["Healthcheck"])
async def root():
    return {"message": "ODME API is running"}


app.include_router(router, prefix="/v1")
