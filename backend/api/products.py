from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
import re
import numpy as np

router = APIRouter()

def para_numero(series):
    s = series.astype(str)
    return (s.str.replace(r"\(.*?\)", "", regex=True)
             .str.replace(r"[^0-9.\-eE]", "", regex=True)
             .replace({"": np.nan, "-": np.nan})
             .astype(float))

@router.post("/upload-csv")
async def upload_products_csv(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Contar registros
        total = len(df)
        
        return {
            "total": total,
            "colunas": list(df.columns),
            "preview": df.head(20).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/process-csv")
async def process_products(
    file: UploadFile = File(...),
    min_price: float = 10.0,
    max_price: float = 50.0,
    max_reviews: int = 130
):
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Filtros básicos
        if "isFBA" in df.columns:
            df = df[df["isFBA"] == True]
        
        if "amazon_sold" in df.columns:
            df = df[df["amazon_sold"] != True]
        
        if "avaliacoes" in df.columns:
            df = df[para_numero(df["avaliacoes"]) < max_reviews]
        
        return {
            "total_processados": len(df),
            "data": df.head(100).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))