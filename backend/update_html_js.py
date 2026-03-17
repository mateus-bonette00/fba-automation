import sys
import os

files_to_fix = [
    "exports/Produtos_Daniel_20_02_2026_195500_CORRIGIDO.html",
    "exports/Produtos_Daniel_20_02_2026_205843.html",
    "exports/Produtos_Daniel_20_02_2026_212722.html",
    "exports/Produtos_Daniel_20_02_2026_213201.html"
]

base_dir = "/home/mateus/Documentos/Qota Store/códigos/fba-automation"

js_script = """
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const links = document.querySelectorAll('td a');
                
                // Load clicked state from localStorage
                links.forEach(link => {
                    const url = link.getAttribute('href');
                    if(url && localStorage.getItem('clicked_' + url)) {
                        link.parentElement.classList.add('clicked-cell');
                    }
                    
                    // Add click listener
                    link.addEventListener('click', function() {
                        if(url) {
                            localStorage.setItem('clicked_' + url, 'true');
                            this.parentElement.classList.add('clicked-cell');
                        }
                    });
                });
            });
        </script>
"""

for filename in files_to_fix:
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
        
    print(f"Atualizando {filename}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Adicionar CSS
        if "td.clicked-cell" not in content:
            content = content.replace("tr:hover { background-color: #2a2a2a; }", 
                                      "tr:hover { background-color: #2a2a2a; }\n            td.clicked-cell { background-color: #4a1515 !important; }")
            content = content.replace("a { color: #4da6ff; text-decoration: none; }", 
                                      "a { color: #4da6ff; text-decoration: none; display: block; width: 100%; height: 100%; }\n            a:visited { color: #ff8080; }")
            content = content.replace("th, td { border: 1px solid #333; padding: 8px; text-align: left; }", 
                                      "th, td { border: 1px solid #333; padding: 8px; text-align: left; transition: background-color 0.3s; }")
            
        # Adicionar JS
        if "localStorage.getItem('clicked_'" not in content:
            content = content.replace("</body></html>", js_script + "\n</body></html>")
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Sucesso: CSS e JS injetados em {filename}.")
    except Exception as e:
        print(f"Erro processando {filename}: {e}")
