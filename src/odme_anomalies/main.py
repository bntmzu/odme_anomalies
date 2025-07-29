from fastapi import FastAPI

app = FastAPI(title="ODME - mythological anomalies")


@app.get("/")
async def root():
    return {"message": "ODME API is running"}

