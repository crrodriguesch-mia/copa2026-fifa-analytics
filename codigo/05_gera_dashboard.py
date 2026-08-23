"""
=====================================================================
ESTUDO DE CASO - COPA DO MUNDO FIFA 2026
Etapa 4b: Geracao do dashboard HTML auto-contido
=====================================================================
Injeta o payload JSON no template e grava duas versoes:
  saida/dashboard_copa2026.html  -> documento completo (abre no navegador)
  saida/dashboard_artifact.html  -> mesmo conteudo sem <!doctype>/<html>
                                    (formato exigido pela publicacao web)
=====================================================================
"""

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SAIDA, CODIGO = BASE / "saida", BASE / "codigo"

tpl = (CODIGO / "template_dashboard.html").read_text(encoding="utf-8")
dados = (SAIDA / "dashboard_dados.json").read_text(encoding="utf-8")

conteudo = tpl.replace("/*__DADOS__*/", dados)
assert "/*__DADOS__*/" not in conteudo, "placeholder de dados nao substituido"

(SAIDA / "dashboard_artifact.html").write_text(conteudo, encoding="utf-8")

completo = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + conteudo.split("<div id=\"tip\"", 1)[0]
            + '</head>\n<body>\n<div id="tip"'
            + conteudo.split("<div id=\"tip\"", 1)[1]
            + '\n</body>\n</html>\n')
(SAIDA / "dashboard_copa2026.html").write_text(completo, encoding="utf-8")

for f in ("dashboard_artifact.html", "dashboard_copa2026.html"):
    print(f"{f}: {(SAIDA / f).stat().st_size/1024:.0f} KB")
