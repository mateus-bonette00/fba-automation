import sys
import os
import re

files_to_fix = [
    "exports/Produtos_Daniel_20_02_2026_195500_CORRIGIDO.html",
    "exports/Produtos_Daniel_20_02_2026_205843.html",
    "exports/Produtos_Daniel_20_02_2026_212722.html",
    "exports/Produtos_Daniel_20_02_2026_213201.html"
]

base_dir = "/home/mateus/Documentos/Qota Store/códigos/fba-automation"

new_style = """<style>
            :root { --bg: #ffffff; --text: #333333; --table-bg: #f9f9f9; --border: #dddddd; --th-bg: #0563C1; --th-text: #ffffff; --link: #0066cc; --link-hover: #003399; --link-visited: #cc0000; --tr-hover: #f1f1f1; --clicked-bg: #ffe6e6; }
            @media (prefers-color-scheme: dark) {
              :root { --bg: #121212; --text: #e0e0e0; --table-bg: #1e1e1e; --border: #333333; --th-bg: #0563C1; --th-text: #ffffff; --link: #4da6ff; --link-hover: #80bfff; --link-visited: #ff8080; --tr-hover: #2a2a2a; --clicked-bg: #4a1515; }
            }
            body { font-family: monospace; font-size: 14px; margin: 20px; background: var(--bg); color: var(--text); }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; background: var(--table-bg); }
            th, td { border: 1px solid var(--border); padding: 8px; text-align: left; transition: background-color 0.3s; }
            th { background-color: var(--th-bg); color: var(--th-text); position: sticky; top: 0; }
            a { color: var(--link); text-decoration: none; display: block; width: 100%; height: 100%; }
            a:hover { text-decoration: underline; color: var(--link-hover); }
            a:visited { color: var(--link-visited); }
            tr:hover { background-color: var(--tr-hover); }
            td.clicked-cell { background-color: var(--clicked-bg) !important; }
</style>"""

for filename in files_to_fix:
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        continue
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Replace completely the style block via Regex
        content = re.sub(r"<style>.*?</style>", new_style, content, flags=re.DOTALL)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Sucesso: CSS Dinamico (Light/Dark) injetado em {filename}.")
    except Exception as e:
        print(f"Erro processando {filename}: {e}")
