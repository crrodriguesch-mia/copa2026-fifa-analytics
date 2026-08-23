"""
Etapa de verificacao: abre o dashboard num navegador headless, captura erros
de console, testa os filtros e gera capturas de tela nos dois temas.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
SAIDA = BASE / "saida"
URL = (SAIDA / "dashboard_copa2026.html").as_uri()
erros = []

with sync_playwright() as p:
    b = p.chromium.launch()
    for tema, w, h in [("light", 1440, 1000), ("dark", 1440, 1000), ("mobile", 420, 900)]:
        pg = b.new_page(viewport={"width": w, "height": h},
                        color_scheme="dark" if tema == "dark" else "light",
                        device_scale_factor=1.5 if tema == "mobile" else 1)
        pg.on("console", lambda m: erros.append(f"[{tema}] console.{m.type}: {m.text}")
              if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: erros.append(f"[{tema}] pageerror: {e}"))
        pg.goto(URL, wait_until="load")
        pg.wait_for_timeout(1800)

        # verificacoes estruturais
        checks = {
            "kpis": pg.locator(".kpi").count(),
            "cards": pg.locator(".card").count(),
            "svgs": pg.locator("svg").count(),
            "tabelas": pg.locator("table").count(),
            "linhas_partidas": pg.locator("#t-partidas tbody tr").count(),
            "partidas_chave": pg.locator(".match").count(),
        }
        print(tema, checks)
        if checks["svgs"] < 8:
            erros.append(f"[{tema}] poucos graficos renderizados: {checks['svgs']}")
        if checks["linhas_partidas"] != 104 and tema == "light":
            erros.append(f"[{tema}] tabela de partidas com {checks['linhas_partidas']} linhas")

        # overflow horizontal da pagina
        ow = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        if ow > 2:
            erros.append(f"[{tema}] overflow horizontal de {ow}px")

        if tema == "light":
            # interacoes: troca de metrica, filtro de perfil, busca, toggle de tabela
            pg.select_option("#f-metrica", "posse_media"); pg.wait_for_timeout(400)
            pg.select_option("#f-perfil", pg.locator("#f-perfil option").nth(1).get_attribute("value"))
            pg.wait_for_timeout(400)
            n = pg.locator("#c-rank svg g").count()
            if n == 0:
                erros.append("[light] ranking vazio apos filtro de perfil")
            pg.fill("#f-busca", "Marrocos"); pg.wait_for_timeout(500)
            print("busca Marrocos ->", pg.locator("#cnt-sel").inner_text())
            pg.click("#f-limpar"); pg.wait_for_timeout(500)
            pg.locator('.tbtn[data-table="t-mw"]').click(); pg.wait_for_timeout(300)
            if pg.locator("#t-mw table").count() == 0:
                erros.append("[light] tabela alternativa nao abriu")
            pg.locator('.tbtn[data-table="t-mw"]').click()
            pg.select_option("#f-fase", "Quartas de final"); pg.wait_for_timeout(400)
            print("quartas ->", pg.locator("#cnt-par").inner_text())
            pg.click("#f-limpar"); pg.wait_for_timeout(400)

        pg.screenshot(path=str(SAIDA / f"captura_{tema}.png"), full_page=(tema != "mobile"))
        pg.close()
    b.close()

print("\n--- ERROS/AVISOS ---")
print("\n".join(erros) if erros else "nenhum")
sys.exit(1 if any("pageerror" in e or "console.error" in e for e in erros) else 0)
