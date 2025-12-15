from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from api.sellers import router as sellers_router
from api.products import router as products_router
from api.capture import router as capture_router
from api.supplier_scraper_v2 import router as supplier_router

app = FastAPI(title="Automação FBA", version="1.0.0")

# CORS - permitir requisições do React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(sellers_router, prefix="/api/sellers", tags=["Sellers"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])
app.include_router(capture_router, prefix="/api/capture", tags=["Capture"])
app.include_router(supplier_router, prefix="/api/supplier", tags=["Supplier"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Backend rodando"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)