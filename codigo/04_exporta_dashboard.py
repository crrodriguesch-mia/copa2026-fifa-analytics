"""
=====================================================================
ESTUDO DE CASO - COPA DO MUNDO FIFA 2026
Etapa 4a: Exportacao do payload do dashboard
=====================================================================
Consolida as bases tratadas e os resultados analiticos num unico JSON
que e embutido no arquivo HTML do dashboard (auto-contido, sem
dependencia de servidor ou de biblioteca externa).

Saida: saida/dashboard_dados.json
=====================================================================
"""

import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DADOS, SAIDA = BASE / "dados", BASE / "saida"

sel = pd.read_csv(DADOS / "selecoes.csv")
par = pd.read_csv(DADOS / "partidas.csv")
art = pd.read_csv(DADOS / "artilharia.csv")
estat = json.loads((SAIDA / "resultados_estatistica.json").read_text(encoding="utf-8"))
mine = json.loads((SAIDA / "resultados_mineracao.json").read_text(encoding="utf-8"))
raw = json.loads((DADOS / "raw_stats_premios.json").read_text(encoding="utf-8"))
grupos_raw = json.loads((DADOS / "raw_grupos.json").read_text(encoding="utf-8"))

# Codigos de tres letras (padrao FIFA) para rotulos compactos nos graficos
COD = {
    "Espanha": "ESP", "Argentina": "ARG", "Inglaterra": "ING", "França": "FRA",
    "Noruega": "NOR", "Bélgica": "BEL", "Marrocos": "MAR", "Suíça": "SUI",
    "México": "MEX", "Colômbia": "COL", "Brasil": "BRA", "Portugal": "POR",
    "Canadá": "CAN", "Egito": "EGI", "Estados Unidos": "EUA", "Paraguai": "PAR",
    "Alemanha": "ALE", "Países Baixos": "HOL", "Japão": "JAP", "Suécia": "SUE",
    "Croácia": "CRO", "Áustria": "AUT", "Cabo Verde": "CPV", "Senegal": "SEN",
    "Costa do Marfim": "CIV", "Equador": "EQU", "Congo (RDC)": "COD",
    "Argélia": "ALG", "Gana": "GAN", "Austrália": "AUS", "África do Sul": "RSA",
    "Bósnia e Herzegovina": "BIH", "Coreia do Sul": "COR", "Irã": "IRA",
    "Uruguai": "URU", "Turquia": "TUR", "Escócia": "ESC", "Chéquia": "TCH",
    "Nova Zelândia": "NZL", "Panamá": "PAN", "Haiti": "HAI", "Catar": "CAT",
    "Arábia Saudita": "ARA", "Jordânia": "JOR", "Uzbequistão": "UZB",
    "Curaçao": "CUR", "Iraque": "IRQ", "Tunísia": "TUN",
}
sel["cod"] = sel["selecao"].map(COD)
assert sel["cod"].isna().sum() == 0, "Selecao sem codigo de tres letras"

COLS_SEL = ["selecao", "cod", "confederacao", "grupo", "pos_grupo", "classificacao_final",
            "fase_final", "jogos", "vitorias", "empates", "derrotas", "gols_pro",
            "gols_contra", "saldo_gols", "pontos_totais", "aproveitamento_pct",
            "posse_media", "precisao_passes", "passes_por_jogo", "chutes_por_jogo",
            "chutes_a_gol_por_jogo", "xg", "xg_por_jogo", "gols_por_jogo",
            "gols_sofridos_por_jogo", "precisao_finalizacao", "gols_menos_xg",
            "clean_sheets", "pct_clean_sheets", "cartoes_amarelos", "cartoes_vermelhos",
            "cartoes_por_jogo", "assistencias", "cluster", "perfil_cluster",
            "pca_x", "pca_y", "avancou_mata_mata", "top8"]

payload = {
    "meta": {
        "titulo": "Copa do Mundo FIFA 2026",
        "subtitulo": "Canadá · México · Estados Unidos — 11 de junho a 19 de julho de 2026",
        "campeao": "Espanha", "vice": "Argentina", "terceiro": "Inglaterra", "quarto": "França",
        "final": "Espanha 1 x 0 Argentina — gol de Ferran Torres aos 106' (prorrogação), MetLife Stadium",
        "partidas": int(len(par)), "selecoes": int(sel.selecao.nunique()),
        "gols": int(par.total_gols.sum()),
        "media_gols": round(float(par.total_gols.mean()), 2),
        "publico_total": raw["estatisticas_gerais"]["publico_total"],
        "publico_medio": raw["estatisticas_gerais"]["media_publico"],
        "cartoes_amarelos": raw["estatisticas_gerais"]["cartoes_amarelos"],
        "cartoes_vermelhos": raw["estatisticas_gerais"]["cartoes_vermelhos"],
        "premios": raw["premios"],
        "atualizado": "21/08/2026",
    },
    "selecoes": sel[COLS_SEL].round(3).astype(object)
                .where(pd.notna(sel[COLS_SEL]), None).to_dict("records"),
    # astype(object) antes do where: sem isso o pandas devolve NaN em colunas
    # numericas, e NaN nao e JSON valido.
    "partidas": (par[["id_partida", "fase", "fase_ordem", "etapa", "grupo", "rodada", "data",
                      "estadio", "selecao_casa", "selecao_fora", "gols_casa", "gols_fora",
                      "total_gols", "prorrogacao", "penaltis", "vencedor", "decidida_por"]]
                 .astype(object).where(pd.notna(par), None).to_dict("records")),
    "artilharia": art.astype(object).where(pd.notna(art), None).to_dict("records"),
    "grupos": [{"grupo": g["grupo"], "tabela": g["tabela"]} for g in grupos_raw["grupos"]],
    "estatistica": estat,
    "mineracao": mine,
    "fontes": sorted({(f["url"] if isinstance(f, dict) else f)
                      for f in (raw["fontes"] + grupos_raw["fontes"] +
                                json.loads((DADOS / "raw_mata_mata.json")
                                           .read_text(encoding="utf-8"))["fontes"])}),
}

txt = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
(SAIDA / "dashboard_dados.json").write_text(txt, encoding="utf-8")
print(f"dashboard_dados.json gravado: {len(txt)/1024:.1f} KB")
print(f"  selecoes: {len(payload['selecoes'])} | partidas: {len(payload['partidas'])} "
      f"| artilheiros: {len(payload['artilharia'])} | fontes: {len(payload['fontes'])}")
