import csv
import io
import requests
import time

SHEET_EXPORT_URL = "https://docs.google.com/spreadsheets/d/1bjPtkfDmagCFDx9xTwcBh_LUzThH_cEqtbCa1dQ-PnQ/export?format=csv&gid=0"


class SupplierSheetError(RuntimeError):
    """Erro ao acessar ou interpretar a planilha de fornecedores."""
    pass


def get_next_supplier(start_index="", skip_indices=None, max_retries=3, timeout_seconds=20):
    """
    Baixa o CSV público e retorna o próximo fornecedor válido.

    Retorna:
      - dict {"indice": ..., "url": ...} quando encontra o próximo fornecedor
      - None quando realmente não há mais fornecedores válidos

    Lança SupplierSheetError quando há falha de rede/leitura após retries.
    """
    if skip_indices is None:
        skip_indices = []

    start_index_clean = (start_index or "").strip()
    skip_set = {str(x).strip() for x in skip_indices if str(x).strip()}
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(SHEET_EXPORT_URL, timeout=timeout_seconds)
            r.raise_for_status()
            r.encoding = "utf-8"

            csv_reader = csv.DictReader(io.StringIO(r.text))

            # If a start index is provided, we skip until we find it
            found_start = False if start_index_clean else True

            for row in csv_reader:
                indice = (row.get("INDICE") or "").strip()
                link = (row.get("LINKS DO FORNECEDORES") or "").strip()

                is_explicit_start = False
                if not found_start:
                    if indice == start_index_clean:
                        found_start = True
                        # Força o índice inicial uma vez (mesmo se estiver em skip),
                        # para garantir fluxo sequencial N -> N+1.
                        is_explicit_start = True
                    else:
                        continue  # Skip until we reach the starting index

                if not is_explicit_start and indice in skip_set:
                    continue

                if link and link.startswith("http"):
                    return {
                        "indice": indice,
                        "url": link,
                    }
            return None
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                print(f"Erro ao acessar Google Sheets (tentativa {attempt}/{max_retries}): {e}")
                time.sleep(min(10, attempt * 2))

    raise SupplierSheetError(f"Falha ao acessar Google Sheets após {max_retries} tentativas: {last_error}")
