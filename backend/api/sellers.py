from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import io
import re
import numpy as np
from typing import Optional, List

router = APIRouter()

CATEGORIAS_CANONICAS = [
    "Arts, Crafts & Sewing",
    "Office Products",
    "Toys & Games",
    "Sports & Outdoors",
    "Automotive (Acessórios)",
    "Pet Supplies",
    "Tools & Home Improvement",
    "Home & Kitchen",
]

CAT_KEYWORDS = {
    "Arts, Crafts & Sewing": [
        r"\barts?\b", r"\bcrafts?\b", r"\bsewing\b",
    ],
    "Office Products": [r"\boffice(\s+products?)?\b", r"\bstationery\b"],
    "Toys & Games": [r"\btoys?\b", r"\bgames?\b"],
    "Sports & Outdoors": [r"\bsports?\b", r"\boutdoors?\b"],
    "Automotive (Acessórios)": [r"\bautomotive\b", r"\bauto\s*parts\b"],
    "Pet Supplies": [r"\bpet\s+supplies\b", r"\bpet\b"],
    "Tools & Home Improvement": [r"\btools?\b", r"\bhome\s+improv"],
    "Home & Kitchen": [r"\bhome\b", r"\bkitchen\b"],
}

def match_categoria(valor: str, alvo: str) -> bool:
    if not isinstance(valor, str):
        return False
    val = valor.strip().casefold()
    if ">" in val:
        val = val.split(">", 1)[0].strip()
    for pat in CAT_KEYWORDS.get(alvo, []):
        if re.search(pat, val, flags=re.I):
            return True
    return False

@router.get("/categorias")
async def get_categorias():
    return {"categorias": CATEGORIAS_CANONICAS}

# Armazenar DataFrames em memória (cache simples)
uploaded_data_cache = {}

@router.post("/upload-csv")
async def upload_sellers_csv(
    files: List[UploadFile] = File(...)
):
    try:
        all_dfs = []

        # Ler todos os arquivos CSV
        for file in files:
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content), low_memory=False)
            all_dfs.append(df)

        # Concatenar todos os DataFrames
        df = pd.concat(all_dfs, ignore_index=True)

        # Filtrar apenas FBA
        if "Uses FBA" in df.columns:
            df = df[df["Uses FBA"] == True]

        if df.empty:
            raise HTTPException(status_code=400, detail="Nenhum seller com FBA encontrado")

        # Embaralhar os dados
        df = df.sample(frac=1).reset_index(drop=True)

        # Substituir NaN, inf e -inf por None (null no JSON)
        df = df.replace([np.nan, np.inf, -np.inf], None)

        # Identificar colunas importantes
        image_col = None
        title_col = None
        upc_col = None
        asin_col = None

        for col in df.columns:
            col_lower = col.lower()
            if 'image' in col_lower and not image_col:
                image_col = col
            elif any(x in col_lower for x in ['title', 'product name']) and 'parent' not in col_lower and not title_col:
                title_col = col
            elif 'upc' in col_lower and not upc_col:
                upc_col = col
            elif 'asin' in col_lower and 'parent' not in col_lower and not asin_col:
                asin_col = col

        # Armazenar no cache com ID simples
        cache_id = "current_data"
        uploaded_data_cache[cache_id] = {
            "df": df,
            "columns": {
                "image": image_col,
                "title": title_col,
                "upc": upc_col,
                "asin": asin_col
            }
        }

        return {
            "total": len(df),
            "cache_id": cache_id,
            "columns": {
                "image": image_col,
                "title": title_col,
                "upc": upc_col,
                "asin": asin_col
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get-products/{cache_id}")
async def get_products(
    cache_id: str,
    page: int = 1,
    per_page: int = 200,
    seller: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_bsr: Optional[int] = None,
    max_bsr: Optional[int] = None,
    max_fba_sellers: Optional[int] = None,
    exclude_amazon: bool = False
):
    try:
        if cache_id not in uploaded_data_cache:
            raise HTTPException(status_code=404, detail="Dados não encontrados. Faça upload novamente.")

        cached = uploaded_data_cache[cache_id]
        df = cached["df"].copy()
        columns = cached["columns"]

        # Log dos filtros recebidos
        print(f"Filtros recebidos - seller: {seller}, min_price: {min_price}, max_price: {max_price}, min_bsr: {min_bsr}, max_bsr: {max_bsr}, max_fba_sellers: {max_fba_sellers}, exclude_amazon: {exclude_amazon}")
        print(f"Total de produtos antes dos filtros: {len(df)}")

        # Aplicar filtros
        if seller and seller.strip():
            # Procurar coluna de seller
            seller_col = None
            for col in df.columns:
                if 'seller' in col.lower():
                    seller_col = col
                    break

            if seller_col:
                print(f"Coluna de seller encontrada: {seller_col}")
                before_count = len(df)
                df = df[df[seller_col].astype(str).str.contains(seller, case=False, na=False)]
                print(f"Produtos após filtro de seller: {len(df)} (eram {before_count})")
            else:
                print("Coluna de seller não encontrada!")

        # Filtro de preço
        if min_price is not None or max_price is not None:
            # Procurar coluna de preço (evitando colunas de mudança de preço)
            price_col = None
            for col in df.columns:
                col_lower = col.lower()
                # Procurar por "price" mas excluir colunas de mudança, buy box, etc
                if 'price' in col_lower and not any(x in col_lower for x in ['change', 'last', 'buy', 'variation', 'drop']):
                    price_col = col
                    break

            if price_col:
                print(f"Coluna de preço encontrada: {price_col}")
                # Converter para numérico
                df[price_col] = pd.to_numeric(df[price_col], errors='coerce')

                # Mostrar alguns valores de exemplo
                sample_prices = df[price_col].dropna().head(10).tolist()
                print(f"Exemplos de preços na coluna: {sample_prices}")
                print(f"Min: {df[price_col].min()}, Max: {df[price_col].max()}")

                before_count = len(df)

                if min_price is not None:
                    df = df[df[price_col] >= min_price]
                    print(f"Produtos após filtro min_price ({min_price}): {len(df)}")

                if max_price is not None:
                    df = df[df[price_col] <= max_price]
                    print(f"Produtos após filtro max_price ({max_price}): {len(df)}")
            else:
                print("Coluna de preço não encontrada!")
                # Listar todas as colunas que contêm "price"
                price_cols = [col for col in df.columns if 'price' in col.lower()]
                print(f"Colunas disponíveis com 'price': {price_cols}")

        # Filtro de BSR (Best Seller Rank) - quanto menor, melhor vende
        if min_bsr is not None or max_bsr is not None:
            # Procurar coluna de BSR/Sales Rank
            bsr_col = None
            for col in df.columns:
                col_lower = col.lower()
                if any(x in col_lower for x in ['bsr', 'sales rank', 'salesrank', 'best seller', 'bestseller', 'rank']):
                    # Excluir colunas de mudança de rank
                    if not any(x in col_lower for x in ['change', 'drop', 'growth', 'last']):
                        bsr_col = col
                        break

            if bsr_col:
                print(f"Coluna de BSR encontrada: {bsr_col}")
                # Converter para numérico
                df[bsr_col] = pd.to_numeric(df[bsr_col], errors='coerce')

                # Mostrar alguns valores de exemplo
                sample_bsr = df[bsr_col].dropna().head(10).tolist()
                print(f"Exemplos de BSR na coluna: {sample_bsr}")
                print(f"Min BSR no dataset: {df[bsr_col].min()}, Max BSR no dataset: {df[bsr_col].max()}")

                before_count = len(df)

                # Aplicar filtro de BSR mínimo e máximo (remover NaN também)
                if min_bsr is not None and max_bsr is not None:
                    df = df[df[bsr_col].notna() & (df[bsr_col] >= min_bsr) & (df[bsr_col] <= max_bsr)]
                    print(f"Produtos após filtro BSR ({min_bsr} - {max_bsr}): {len(df)} (eram {before_count})")
                elif min_bsr is not None:
                    df = df[df[bsr_col].notna() & (df[bsr_col] >= min_bsr)]
                    print(f"Produtos após filtro min_bsr ({min_bsr}): {len(df)} (eram {before_count})")
                elif max_bsr is not None:
                    df = df[df[bsr_col].notna() & (df[bsr_col] <= max_bsr)]
                    print(f"Produtos após filtro max_bsr ({max_bsr}): {len(df)} (eram {before_count})")
            else:
                print("Coluna de BSR não encontrada!")
                # Listar todas as colunas que contêm "rank" ou "bsr"
                bsr_cols = [col for col in df.columns if any(x in col.lower() for x in ['rank', 'bsr', 'sales'])]
                print(f"Colunas disponíveis com 'rank/bsr/sales': {bsr_cols}")

        # Filtro de número de FBA sellers (pouca concorrência)
        if max_fba_sellers is not None:
            # Procurar coluna de número de FBA sellers
            fba_count_col = None
            for col in df.columns:
                col_lower = col.lower()
                # Buscar por várias variações possíveis
                if 'fba' in col_lower and any(x in col_lower for x in ['seller', 'count', 'number', '#']):
                    # Excluir colunas que são percentuais ou outras métricas
                    if not any(x in col_lower for x in ['%', 'percent', 'ratio', 'share']):
                        fba_count_col = col
                        break

            if fba_count_col:
                print(f"Coluna de contagem FBA encontrada: {fba_count_col}")
                # Converter para numérico
                df[fba_count_col] = pd.to_numeric(df[fba_count_col], errors='coerce')

                # Mostrar alguns valores de exemplo
                sample_fba = df[fba_count_col].dropna().head(10).tolist()
                print(f"Exemplos de contagem FBA: {sample_fba}")
                print(f"Min FBA: {df[fba_count_col].min()}, Max FBA: {df[fba_count_col].max()}")

                before_count = len(df)
                # Filtrar apenas produtos com poucos FBA sellers (remover NaN também)
                df = df[df[fba_count_col].notna() & (df[fba_count_col] <= max_fba_sellers)]
                print(f"Produtos após filtro FBA count (max {max_fba_sellers}): {len(df)} (eram {before_count})")
            else:
                print("Coluna de contagem FBA não encontrada!")
                # Listar TODAS as colunas disponíveis para debug
                print(f"TODAS AS COLUNAS: {list(df.columns)}")
                # Listar colunas que contêm "fba"
                fba_cols = [col for col in df.columns if 'fba' in col.lower()]
                print(f"Colunas disponíveis com 'fba': {fba_cols}")

        # Filtro para excluir produtos vendidos pela Amazon
        if exclude_amazon:
            before_count = len(df)

            # Procurar coluna de seller (principal)
            seller_col = None
            for col in df.columns:
                if 'seller' in col.lower():
                    seller_col = col
                    break

            # Procurar colunas relacionadas ao vendedor principal ou Buy Box
            buybox_col = None
            for col in df.columns:
                col_lower = col.lower()
                if any(x in col_lower for x in ['buy box', 'buybox', 'featured merchant', 'primary seller']):
                    buybox_col = col
                    break

            # Criar máscara para filtrar Amazon
            mask = pd.Series([True] * len(df), index=df.index)

            # Filtrar pela coluna Seller
            if seller_col:
                print(f"Coluna de Seller encontrada: {seller_col}")
                seller_mask = ~df[seller_col].astype(str).str.contains('amazon', case=False, na=False)
                mask = mask & seller_mask
            else:
                print("Coluna de Seller não encontrada!")

            # Filtrar pela coluna Buy Box (se existir)
            if buybox_col:
                print(f"Coluna de Buy Box encontrada: {buybox_col}")
                buybox_mask = ~df[buybox_col].astype(str).str.contains('amazon', case=False, na=False)
                mask = mask & buybox_mask
            else:
                print("Coluna de Buy Box não encontrada!")
                # Listar colunas relacionadas
                buybox_cols = [col for col in df.columns if any(x in col.lower() for x in ['buy', 'box', 'merchant', 'featured'])]
                print(f"Colunas disponíveis relacionadas a Buy Box: {buybox_cols}")

            # Aplicar o filtro
            df = df[mask]
            print(f"Produtos após excluir Amazon: {len(df)} (eram {before_count})")

        # Calcular paginação após filtros
        total = len(df)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        print(f"Total de produtos após todos os filtros: {total}")
        print(f"Página {page}, retornando produtos {start_idx} a {end_idx}")

        # Pegar slice do DataFrame
        df_page = df.iloc[start_idx:end_idx]

        # Identificar coluna de preço e seller para retornar nos dados
        price_col = None
        seller_col = None
        for col in df.columns:
            col_lower = col.lower()
            # Mesma lógica de busca de preço
            if 'price' in col_lower and not any(x in col_lower for x in ['change', 'last', 'buy', 'variation', 'drop']) and not price_col:
                price_col = col
            if 'seller' in col_lower and not seller_col:
                seller_col = col

        # Criar dados formatados
        products = []
        for _, row in df_page.iterrows():
            # Obter valores das colunas de forma segura
            image_val = row[columns["image"]] if columns["image"] else None
            title_val = row[columns["title"]] if columns["title"] else None
            upc_val = row[columns["upc"]] if columns["upc"] else None
            asin_val = row[columns["asin"]] if columns["asin"] else None

            # Obter preço
            price_val = None
            if price_col:
                try:
                    price_raw = row[price_col]
                    if pd.notna(price_raw):
                        price_val = float(price_raw)
                except (ValueError, KeyError):
                    pass

            # Obter seller
            seller_val = None
            if seller_col:
                try:
                    seller_val = row[seller_col]
                except KeyError:
                    pass

            product = {
                "image": image_val,
                "title": title_val,
                "upc": upc_val,
                "asin": asin_val,
                "price": price_val,
                "seller": seller_val,
            }
            products.append(product)

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "data": products
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get-sellers-list/{cache_id}")
async def get_sellers_list(cache_id: str):
    try:
        if cache_id not in uploaded_data_cache:
            raise HTTPException(status_code=404, detail="Dados não encontrados.")

        cached = uploaded_data_cache[cache_id]
        df = cached["df"]

        # Procurar coluna de seller
        seller_col = None
        for col in df.columns:
            if 'seller' in col.lower():
                seller_col = col
                break

        if not seller_col:
            return {"sellers": []}

        # Obter sellers únicos
        sellers = df[seller_col].dropna().unique().tolist()
        sellers = sorted([str(s) for s in sellers if s])

        return {"sellers": sellers}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/download-filtered-csv/{cache_id}")
async def download_filtered_csv(
    cache_id: str,
    seller: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_bsr: Optional[int] = None,
    max_bsr: Optional[int] = None,
    max_fba_sellers: Optional[int] = None,
    exclude_amazon: bool = False
):
    """
    Baixa CSV dos produtos filtrados com links da Amazon, Google UPC e Google Título
    """
    try:
        if cache_id not in uploaded_data_cache:
            raise HTTPException(status_code=404, detail="Dados não encontrados. Faça upload novamente.")

        cached = uploaded_data_cache[cache_id]
        df = cached["df"].copy()
        columns = cached["columns"]

        print(f"Download CSV - Filtros recebidos - seller: {seller}, min_price: {min_price}, max_price: {max_price}, min_bsr: {min_bsr}, max_bsr: {max_bsr}, max_fba_sellers: {max_fba_sellers}, exclude_amazon: {exclude_amazon}")
        print(f"Total de produtos antes dos filtros: {len(df)}")

        # Aplicar os mesmos filtros do endpoint get-products
        if seller and seller.strip():
            seller_col = None
            for col in df.columns:
                if 'seller' in col.lower():
                    seller_col = col
                    break
            if seller_col:
                df = df[df[seller_col].astype(str).str.contains(seller, case=False, na=False)]

        if min_price is not None or max_price is not None:
            price_col = None
            for col in df.columns:
                col_lower = col.lower()
                if 'price' in col_lower and not any(x in col_lower for x in ['change', 'last', 'buy', 'variation', 'drop']):
                    price_col = col
                    break
            if price_col:
                df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
                if min_price is not None:
                    df = df[df[price_col] >= min_price]
                if max_price is not None:
                    df = df[df[price_col] <= max_price]

        if min_bsr is not None or max_bsr is not None:
            bsr_col = None
            for col in df.columns:
                col_lower = col.lower()
                if any(x in col_lower for x in ['bsr', 'sales rank', 'salesrank', 'best seller', 'bestseller', 'rank']):
                    if not any(x in col_lower for x in ['change', 'drop', 'growth', 'last']):
                        bsr_col = col
                        break
            if bsr_col:
                df[bsr_col] = pd.to_numeric(df[bsr_col], errors='coerce')
                if min_bsr is not None and max_bsr is not None:
                    df = df[df[bsr_col].notna() & (df[bsr_col] >= min_bsr) & (df[bsr_col] <= max_bsr)]
                elif min_bsr is not None:
                    df = df[df[bsr_col].notna() & (df[bsr_col] >= min_bsr)]
                elif max_bsr is not None:
                    df = df[df[bsr_col].notna() & (df[bsr_col] <= max_bsr)]

        if max_fba_sellers is not None:
            fba_count_col = None
            for col in df.columns:
                col_lower = col.lower()
                if 'fba' in col_lower and any(x in col_lower for x in ['seller', 'count', 'number', '#']):
                    if not any(x in col_lower for x in ['%', 'percent', 'ratio', 'share']):
                        fba_count_col = col
                        break
            if fba_count_col:
                df[fba_count_col] = pd.to_numeric(df[fba_count_col], errors='coerce')
                df = df[df[fba_count_col].notna() & (df[fba_count_col] <= max_fba_sellers)]

        if exclude_amazon:
            before_count = len(df)
            seller_col = None
            for col in df.columns:
                if 'seller' in col.lower():
                    seller_col = col
                    break
            buybox_col = None
            for col in df.columns:
                col_lower = col.lower()
                if any(x in col_lower for x in ['buy box', 'buybox', 'featured merchant', 'primary seller']):
                    buybox_col = col
                    break
            mask = pd.Series([True] * len(df), index=df.index)
            if seller_col:
                seller_mask = ~df[seller_col].astype(str).str.contains('amazon', case=False, na=False)
                mask = mask & seller_mask
            if buybox_col:
                buybox_mask = ~df[buybox_col].astype(str).str.contains('amazon', case=False, na=False)
                mask = mask & buybox_mask
            df = df[mask]
            print(f"Produtos após excluir Amazon: {len(df)} (eram {before_count})")

        print(f"Total de produtos após todos os filtros para CSV: {len(df)}")

        # Identificar colunas importantes
        price_col = None
        seller_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'price' in col_lower and not any(x in col_lower for x in ['change', 'last', 'buy', 'variation', 'drop']) and not price_col:
                price_col = col
            if 'seller' in col_lower and not seller_col:
                seller_col = col

        # Criar DataFrame com os dados exportados
        export_data = []
        for _, row in df.iterrows():
            # Obter valores das colunas de forma segura
            title_val = row[columns["title"]] if columns["title"] else ""
            upc_val = row[columns["upc"]] if columns["upc"] else ""
            asin_val = row[columns["asin"]] if columns["asin"] else ""

            # Obter preço
            price_val = ""
            if price_col:
                try:
                    price_raw = row[price_col]
                    if pd.notna(price_raw):
                        price_val = float(price_raw)
                except (ValueError, KeyError):
                    pass

            # Obter seller
            seller_val = ""
            if seller_col:
                try:
                    seller_val = row[seller_col]
                except KeyError:
                    pass

            # Criar links
            amazon_link = f"https://www.amazon.com/dp/{asin_val}" if asin_val else ""
            google_titulo_link = f"https://www.google.com/search?q={title_val}&gl=us&hl=es" if title_val else ""
            google_upc_link = f"https://www.google.com/search?q={upc_val}&gl=us&hl=es" if upc_val else ""

            export_data.append({
                "Título": title_val,
                "ASIN": asin_val,
                "UPC": upc_val,
                "Preço": price_val,
                "Seller": seller_val,
                "Link Amazon": amazon_link,
                "Link Google (Título)": google_titulo_link,
                "Link Google (UPC)": google_upc_link
            })

        # Criar DataFrame de exportação
        df_export = pd.DataFrame(export_data)

        # Substituir NaN, inf e -inf por None antes de exportar
        df_export = df_export.replace([np.nan, np.inf, -np.inf], "")

        # Exportar
        output = io.BytesIO()
        df_export.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)

        from starlette.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=produtos_filtrados.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/download-filtered")
async def download_filtered(
    files: List[UploadFile] = File(...)
):
    try:
        all_dfs = []

        # Ler todos os arquivos CSV
        for file in files:
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content), low_memory=False)
            all_dfs.append(df)

        # Concatenar todos os DataFrames
        df = pd.concat(all_dfs, ignore_index=True)

        # Filtrar apenas FBA
        if "Uses FBA" in df.columns:
            df = df[df["Uses FBA"] == True]

        # Embaralhar os dados
        df = df.sample(frac=1).reset_index(drop=True)

        # Substituir NaN, inf e -inf por None antes de exportar
        df = df.replace([np.nan, np.inf, -np.inf], None)

        # Exportar
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        from starlette.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sellers_filtrado.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))