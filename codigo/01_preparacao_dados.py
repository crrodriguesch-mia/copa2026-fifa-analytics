"""
=====================================================================
ESTUDO DE CASO - COPA DO MUNDO FIFA 2026
Etapa 1: Coleta, limpeza, integracao e criacao de indicadores
=====================================================================
MBA - Disciplina: Visualizacao de Dados e Elaboracao de Dashboards
Autor: Carlos Rodrigues

Entradas  (dados/):
    raw_grupos.json        -> 12 grupos: tabelas finais + 72 partidas
    raw_mata_mata.json     -> 32 partidas de mata-mata (16 avos -> final)
    raw_stats_premios.json -> estatisticas por selecao, artilharia, premios

Saidas    (dados/):
    partidas.csv           -> 104 partidas (base de fatos)
    selecoes.csv           -> 48 selecoes x 30+ indicadores (base analitica)
    artilharia.csv         -> 28 jogadores com 3+ gols
    validacao.txt          -> relatorio de consistencia da base
=====================================================================
"""

import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DADOS = BASE / "dados"

# ---------------------------------------------------------------------
# 1. LEITURA DAS BASES BRUTAS
# ---------------------------------------------------------------------
grupos_raw = json.loads((DADOS / "raw_grupos.json").read_text(encoding="utf-8"))
mata_raw = json.loads((DADOS / "raw_mata_mata.json").read_text(encoding="utf-8"))
stats_raw = json.loads((DADOS / "raw_stats_premios.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------
# 2. LIMPEZA / PADRONIZACAO DE NOMES
#    As tres fontes usam grafias diferentes para a mesma selecao
#    (ex.: "RD Congo" / "Congo (RDC)" / "Republica Democratica do Congo").
#    A funcao abaixo cria uma chave canonica sem acento/pontuacao.
# ---------------------------------------------------------------------
SINONIMOS = {
    "rd congo": "Congo (RDC)",
    "republica democratica do congo": "Congo (RDC)",
    "congo rdc": "Congo (RDC)",
    "tchequia": "Chéquia",
    "chequia": "Chéquia",
    "republica tcheca": "Chéquia",
    "paises baixos": "Países Baixos",
    "holanda": "Países Baixos",
    "estados unidos": "Estados Unidos",
    "eua": "Estados Unidos",
}


def chave(nome: str) -> str:
    """Normaliza um nome de selecao para comparacao (sem acento, minusculo)."""
    s = unicodedata.normalize("NFKD", str(nome)).encode("ASCII", "ignore").decode()
    s = s.lower().replace("(", " ").replace(")", " ").replace("-", " ").replace(".", " ")
    return " ".join(s.split())


def padroniza(nome: str) -> str:
    """Devolve o nome canonico da selecao."""
    k = chave(nome)
    return SINONIMOS.get(k, str(nome).strip())


# ---------------------------------------------------------------------
# 3. TABELA DE FATOS: 104 PARTIDAS
# ---------------------------------------------------------------------
ORDEM_FASE = {
    "Fase de grupos": 1,
    "16 avos de final": 2,
    "Oitavas de final": 3,
    "Quartas de final": 4,
    "Semifinal": 5,
    "Disputa de 3º lugar": 6,
    "Final": 7,
}
MAPA_FASE_RAW = {
    "16 avos": "16 avos de final",
    "Oitavas": "Oitavas de final",
    "Quartas": "Quartas de final",
    "Semifinais": "Semifinal",
    "Disputa de 3º lugar": "Disputa de 3º lugar",
    "Final": "Final",
}

registros = []

# 3.1 Fase de grupos --------------------------------------------------
for g in grupos_raw["grupos"]:
    for i, p in enumerate(g["partidas"]):
        registros.append(
            dict(
                fase="Fase de grupos",
                grupo=g["grupo"],
                rodada=i // 2 + 1,  # 2 partidas por rodada em cada grupo
                data=None,
                estadio=None,
                selecao_casa=padroniza(p["casa"]),
                selecao_fora=padroniza(p["fora"]),
                gols_casa=p["gols_casa"],
                gols_fora=p["gols_fora"],
                prorrogacao=False,
                penaltis=None,
            )
        )

# 3.2 Mata-mata -------------------------------------------------------
for f in mata_raw["fases"]:
    fase = MAPA_FASE_RAW[f["fase"]]
    for p in f["partidas"]:
        registros.append(
            dict(
                fase=fase,
                grupo=None,
                rodada=None,
                data=p.get("data"),
                estadio=p.get("estadio"),
                selecao_casa=padroniza(p["casa"]),
                selecao_fora=padroniza(p["fora"]),
                gols_casa=p["gols_casa"],
                gols_fora=p["gols_fora"],
                prorrogacao=bool(p.get("prorrogacao")),
                penaltis=p.get("penaltis"),
            )
        )

partidas = pd.DataFrame(registros)

# 3.3 Criacao de variaveis derivadas ---------------------------------
partidas["fase_ordem"] = partidas["fase"].map(ORDEM_FASE)
partidas["etapa"] = np.where(partidas["fase"] == "Fase de grupos", "Grupos", "Mata-mata")
partidas["total_gols"] = partidas["gols_casa"] + partidas["gols_fora"]
partidas["saldo_partida"] = (partidas["gols_casa"] - partidas["gols_fora"]).abs()
partidas["empate_tempo_normal"] = partidas["gols_casa"] == partidas["gols_fora"]
partidas["ambas_marcaram"] = (partidas["gols_casa"] > 0) & (partidas["gols_fora"] > 0)
partidas["over_2_5"] = partidas["total_gols"] > 2.5
partidas["clean_sheet_casa"] = partidas["gols_fora"] == 0
partidas["clean_sheet_fora"] = partidas["gols_casa"] == 0


def tem_penaltis(v) -> bool:
    return isinstance(v, str) and "-" in v


def decide_vencedor(r):
    if tem_penaltis(r.penaltis):  # ex.: "3-4" (casa-fora)
        a, b = (int(x) for x in str(r.penaltis).split("-"))
        return r.selecao_casa if a > b else r.selecao_fora
    if r.gols_casa > r.gols_fora:
        return r.selecao_casa
    if r.gols_fora > r.gols_casa:
        return r.selecao_fora
    return None  # empate valido apenas na fase de grupos


def decidida_por(r):
    if tem_penaltis(r.penaltis):
        return "Penaltis"
    if r.prorrogacao:
        return "Prorrogacao"
    return "Tempo normal"


partidas["vencedor"] = partidas.apply(decide_vencedor, axis=1)
partidas["decidida_por"] = partidas.apply(decidida_por, axis=1)
partidas.insert(0, "id_partida", range(1, len(partidas) + 1))

partidas = partidas.sort_values(["fase_ordem", "grupo", "rodada", "id_partida"]).reset_index(drop=True)

# ---------------------------------------------------------------------
# 4. TABELA LONGA (uma linha por selecao por partida)
#    Facilita agregacoes por selecao sem repetir logica casa/fora.
# ---------------------------------------------------------------------
casa = partidas.rename(
    columns={"selecao_casa": "selecao", "selecao_fora": "adversario",
             "gols_casa": "gols_pro", "gols_fora": "gols_contra"}
).assign(mando="Casa")
fora = partidas.rename(
    columns={"selecao_fora": "selecao", "selecao_casa": "adversario",
             "gols_fora": "gols_pro", "gols_casa": "gols_contra"}
).assign(mando="Fora")
cols = ["id_partida", "fase", "fase_ordem", "etapa", "grupo", "selecao", "adversario",
        "gols_pro", "gols_contra", "vencedor", "decidida_por", "mando"]
longa = pd.concat([casa[cols], fora[cols]], ignore_index=True)

longa["resultado"] = np.select(
    [longa["vencedor"] == longa["selecao"],
     longa["vencedor"].isna()],
    ["V", "E"], default="D",
)
longa["pontos"] = longa["resultado"].map({"V": 3, "E": 1, "D": 0})
longa["clean_sheet"] = longa["gols_contra"] == 0

# ---------------------------------------------------------------------
# 5. BASE ANALITICA POR SELECAO (integracao das tres fontes)
# ---------------------------------------------------------------------
agg = (
    longa.groupby("selecao")
    .agg(
        jogos=("id_partida", "count"),
        vitorias=("resultado", lambda s: (s == "V").sum()),
        empates=("resultado", lambda s: (s == "E").sum()),
        derrotas=("resultado", lambda s: (s == "D").sum()),
        gols_pro=("gols_pro", "sum"),
        gols_contra=("gols_contra", "sum"),
        clean_sheets=("clean_sheet", "sum"),
        pontos_totais=("pontos", "sum"),
    )
    .reset_index()
)
agg["saldo_gols"] = agg["gols_pro"] - agg["gols_contra"]

# 5.1 Grupo, posicao e pontos da fase de grupos -----------------------
linhas_grupo = []
for g in grupos_raw["grupos"]:
    for t in g["tabela"]:
        linhas_grupo.append(
            dict(selecao=padroniza(t["selecao"]), grupo=g["grupo"], pos_grupo=t["pos"],
                 pts_grupo=t["Pts"], gp_grupo=t["GP"], gc_grupo=t["GC"], sg_grupo=t["SG"])
        )
tab_grupos = pd.DataFrame(linhas_grupo)

# 5.2 Estatisticas tecnicas por selecao (posse, passes, chutes, xG) ---
tec = pd.DataFrame(stats_raw["stats_selecoes"])
tec["selecao"] = tec["selecao"].map(padroniza)
tec = tec.rename(columns={
    "posse_media_pct": "posse_media", "precisao_passes_pct": "precisao_passes",
    "chutes_a_gol": "chutes_a_gol", "assistencias": "assistencias",
    "penaltis": "penaltis_convertidos", "amarelos": "cartoes_amarelos",
    "vermelhos": "cartoes_vermelhos",
})
tec = tec[["selecao", "xg", "posse_media", "passes", "precisao_passes", "chutes",
           "chutes_a_gol", "assistencias", "penaltis_convertidos",
           "cartoes_amarelos", "cartoes_vermelhos"]]

# 5.3 Classificacao geral final (1 a 48) ------------------------------
clf = pd.DataFrame(stats_raw["classificacao_geral"])
clf["selecao"] = clf["selecao"].map(padroniza)
clf = clf.rename(columns={"pos": "classificacao_final", "fase": "fase_final"})[
    ["selecao", "classificacao_final", "fase_final"]]

selecoes = (
    agg.merge(tab_grupos, on="selecao", how="left")
    .merge(tec, on="selecao", how="left")
    .merge(clf, on="selecao", how="left")
)

# 5.4 INDICADORES CRIADOS (normalizados por jogo / taxas) -------------
selecoes["gols_por_jogo"] = selecoes["gols_pro"] / selecoes["jogos"]
selecoes["gols_sofridos_por_jogo"] = selecoes["gols_contra"] / selecoes["jogos"]
selecoes["chutes_por_jogo"] = selecoes["chutes"] / selecoes["jogos"]
selecoes["chutes_a_gol_por_jogo"] = selecoes["chutes_a_gol"] / selecoes["jogos"]
selecoes["passes_por_jogo"] = selecoes["passes"] / selecoes["jogos"]
selecoes["xg_por_jogo"] = selecoes["xg"] / selecoes["jogos"]
selecoes["aproveitamento_pct"] = 100 * selecoes["pontos_totais"] / (3 * selecoes["jogos"])
selecoes["precisao_finalizacao"] = 100 * selecoes["chutes_a_gol"] / selecoes["chutes"]
selecoes["eficiencia_finalizacao"] = 100 * selecoes["gols_pro"] / selecoes["chutes"]
# Desempenho vs. gols esperados: >0 = converteu acima do esperado
selecoes["gols_menos_xg"] = selecoes["gols_pro"] - selecoes["xg"]
selecoes["xg_por_chute"] = selecoes["xg"] / selecoes["chutes"]
selecoes["pct_clean_sheets"] = 100 * selecoes["clean_sheets"] / selecoes["jogos"]
selecoes["cartoes_por_jogo"] = (selecoes["cartoes_amarelos"] + selecoes["cartoes_vermelhos"]) / selecoes["jogos"]
selecoes["indice_disciplina"] = selecoes["cartoes_amarelos"] + 3 * selecoes["cartoes_vermelhos"]

# 5.5 Variaveis-alvo (para estatistica e mineracao) -------------------
selecoes["avancou_mata_mata"] = (selecoes["classificacao_final"] <= 32).astype(int)
selecoes["top16"] = (selecoes["classificacao_final"] <= 16).astype(int)
selecoes["top8"] = (selecoes["classificacao_final"] <= 8).astype(int)
selecoes["confederacao"] = selecoes["selecao"].map({
    # UEFA
    "Espanha": "UEFA", "França": "UEFA", "Inglaterra": "UEFA", "Alemanha": "UEFA",
    "Países Baixos": "UEFA", "Portugal": "UEFA", "Bélgica": "UEFA", "Suíça": "UEFA",
    "Croácia": "UEFA", "Noruega": "UEFA", "Áustria": "UEFA", "Suécia": "UEFA",
    "Escócia": "UEFA", "Chéquia": "UEFA", "Bósnia e Herzegovina": "UEFA", "Turquia": "UEFA",
    # CONMEBOL
    "Argentina": "CONMEBOL", "Brasil": "CONMEBOL", "Colômbia": "CONMEBOL",
    "Uruguai": "CONMEBOL", "Equador": "CONMEBOL", "Paraguai": "CONMEBOL",
    # CAF
    "Marrocos": "CAF", "Senegal": "CAF", "Egito": "CAF", "Costa do Marfim": "CAF",
    "Argélia": "CAF", "Tunísia": "CAF", "Gana": "CAF", "África do Sul": "CAF",
    "Cabo Verde": "CAF", "Congo (RDC)": "CAF",
    # CONCACAF
    "México": "CONCACAF", "Estados Unidos": "CONCACAF", "Canadá": "CONCACAF",
    "Panamá": "CONCACAF", "Haiti": "CONCACAF", "Curaçao": "CONCACAF",
    # AFC
    "Japão": "AFC", "Coreia do Sul": "AFC", "Irã": "AFC", "Arábia Saudita": "AFC",
    "Catar": "AFC", "Jordânia": "AFC", "Uzbequistão": "AFC", "Iraque": "AFC",
    "Austrália": "AFC",
    # OFC
    "Nova Zelândia": "OFC",
})

selecoes = selecoes.sort_values("classificacao_final").reset_index(drop=True)

# ---------------------------------------------------------------------
# 6. ARTILHARIA
# ---------------------------------------------------------------------
art = pd.DataFrame(stats_raw["artilharia"])
art["selecao"] = art["selecao"].map(padroniza)
art["assistencias"] = pd.to_numeric(art["assistencias"], errors="coerce")
art["gols_por_jogo"] = art["gols"] / art["partidas"]
art["minutos_por_gol"] = (art["minutos"] / art["gols"]).round(1)
art["participacoes_gol"] = art["gols"] + art["assistencias"].fillna(0)

# ---------------------------------------------------------------------
# 7. VALIDACAO DA BASE (auditoria de consistencia)
# ---------------------------------------------------------------------
log = []
add = log.append

add("RELATORIO DE VALIDACAO DA BASE - COPA DO MUNDO FIFA 2026")
add("=" * 62)
add(f"Partidas na base .................. {len(partidas)} (esperado: 104)")
add(f"  fase de grupos .................. {(partidas.etapa == 'Grupos').sum()} (esperado: 72)")
add(f"  mata-mata ....................... {(partidas.etapa == 'Mata-mata').sum()} (esperado: 32)")
add(f"Selecoes na base .................. {selecoes.selecao.nunique()} (esperado: 48)")
add(f"Total de gols ..................... {int(partidas.total_gols.sum())} (fontes: 308)")
add(f"Media de gols por partida ......... {partidas.total_gols.mean():.3f} (fontes: 2,96)")
add("")

add("A) Reconstrucao das tabelas de grupo a partir dos placares")
erros_grupo = 0
gs = longa[longa.etapa == "Grupos"].groupby("selecao").agg(
    Pts=("pontos", "sum"), GP=("gols_pro", "sum"), GC=("gols_contra", "sum"))
for _, r in tab_grupos.iterrows():
    calc = gs.loc[r.selecao]
    if not (calc.Pts == r.pts_grupo and calc.GP == r.gp_grupo and calc.GC == r.gc_grupo):
        erros_grupo += 1
        add(f"   [DIVERGENCIA] {r.selecao}: calculado {int(calc.Pts)}pts "
            f"{int(calc.GP)}:{int(calc.GC)} x fonte {r.pts_grupo}pts {r.gp_grupo}:{r.gc_grupo}")
add(f"   Linhas conferidas: 48 | divergencias: {erros_grupo}")
add("")

add("B) Gols pro/contra por selecao: soma das partidas x tabela agregada da fonte")
erros_gols = 0
for _, r in selecoes.iterrows():
    fonte = tec.loc[tec.selecao == r.selecao]
    if fonte.empty:
        continue
    gp_fonte = int(stats_raw["stats_selecoes"][
        [padroniza(s["selecao"]) for s in stats_raw["stats_selecoes"]].index(r.selecao)]["gols_pro"])
    gc_fonte = int(stats_raw["stats_selecoes"][
        [padroniza(s["selecao"]) for s in stats_raw["stats_selecoes"]].index(r.selecao)]["gols_contra"])
    if r.gols_pro != gp_fonte or r.gols_contra != gc_fonte:
        erros_gols += 1
        add(f"   [DIVERGENCIA] {r.selecao}: base {int(r.gols_pro)}:{int(r.gols_contra)} "
            f"x fonte {gp_fonte}:{gc_fonte}")
add(f"   Selecoes conferidas: {len(tec)} | divergencias: {erros_gols}")
add("")

add("C) Numero de jogos x fase alcancada (coerencia estrutural)")
esperado = {"Campeão": 8, "Vice-campeão": 8, "3º lugar": 8, "4º lugar": 8,
            "Quartas de final": 6, "Oitavas de final": 5, "16 avos de final": 4,
            "Fase de grupos": 3}
erros_jogos = 0
for _, r in selecoes.iterrows():
    esp = esperado.get(str(r.fase_final))
    if esp and r.jogos != esp:
        erros_jogos += 1
        add(f"   [DIVERGENCIA] {r.selecao}: {int(r.jogos)} jogos, esperado {esp} ({r.fase_final})")
add(f"   Divergencias: {erros_jogos}")
add("")

add("D) Integridade referencial e valores ausentes")
add(f"   Selecoes sem estatisticas tecnicas: {selecoes.xg.isna().sum()}")
add(f"   Selecoes sem confederacao ........: {selecoes.confederacao.isna().sum()}")
add(f"   Selecoes sem classificacao final .: {selecoes.classificacao_final.isna().sum()}")
add(f"   Empates no mata-mata sem penaltis : "
    f"{((partidas.etapa=='Mata-mata') & partidas.empate_tempo_normal & ~partidas.penaltis.apply(tem_penaltis)).sum()}")
add(f"   Artilheiros com assistencia ausente: {art.assistencias.isna().sum()} de {len(art)}")
add("")
add("LIMITACOES CONHECIDAS (documentadas nas fontes):")
add("   - Mando de campo (casa/fora) divergente entre fontes em ~10 partidas de grupo;")
add("     os placares nao sao afetados. Nenhuma analise deste estudo usa mando de campo")
add("     como variavel explicativa na fase de grupos.")
add("   - Faltas cometidas por selecao: nao publicadas por nenhuma fonte acessivel.")
add("   - Assistencias individuais publicadas apenas para os 7 primeiros artilheiros.")
add("   - Pontos exatos da classificacao geral FIFA nao publicados (apenas a ordem).")

(DADOS / "validacao.txt").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))

# ---------------------------------------------------------------------
# 8. GRAVACAO DAS BASES TRATADAS
# ---------------------------------------------------------------------
partidas.to_csv(DADOS / "partidas.csv", index=False, encoding="utf-8-sig")
longa.to_csv(DADOS / "partidas_selecao.csv", index=False, encoding="utf-8-sig")
selecoes.to_csv(DADOS / "selecoes.csv", index=False, encoding="utf-8-sig")
art.to_csv(DADOS / "artilharia.csv", index=False, encoding="utf-8-sig")
print(f"\nArquivos gravados em {DADOS}")
print(f"  partidas.csv          {partidas.shape}")
print(f"  partidas_selecao.csv  {longa.shape}")
print(f"  selecoes.csv          {selecoes.shape}")
print(f"  artilharia.csv        {art.shape}")
