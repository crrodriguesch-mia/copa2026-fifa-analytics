"""
=====================================================================
ESTUDO DE CASO - COPA DO MUNDO FIFA 2026
Etapa 2: Estatistica Aplicada a Analise de Dados
=====================================================================
Tecnicas aplicadas:
  2.1 Estatistica descritiva (tendencia central e dispersao)
  2.2 Aderencia da distribuicao de gols ao modelo de Poisson (qui-quadrado)
  2.3 Correlacao de Spearman e Pearson entre indicadores e desempenho
  2.4 Comparacao entre grupos (Mann-Whitney U + tamanho de efeito)
  2.5 Analise de associacao (qui-quadrado / Fisher + V de Cramer)

Saida: saida/resultados_estatistica.json  (consumido pelo dashboard e pelo relatorio)
=====================================================================
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parent.parent
DADOS, SAIDA = BASE / "dados", BASE / "saida"
SAIDA.mkdir(exist_ok=True)

partidas = pd.read_csv(DADOS / "partidas.csv")
longa = pd.read_csv(DADOS / "partidas_selecao.csv")
sel = pd.read_csv(DADOS / "selecoes.csv")

res = {}
print("=" * 70)
print("2. ESTATISTICA APLICADA")
print("=" * 70)

# ---------------------------------------------------------------------
# 2.1 ESTATISTICA DESCRITIVA
# ---------------------------------------------------------------------
g = partidas["total_gols"]
desc = dict(
    n=int(g.size), media=float(g.mean()), mediana=float(g.median()),
    moda=int(g.mode().iloc[0]), desvio_padrao=float(g.std(ddof=1)),
    variancia=float(g.var(ddof=1)), cv_pct=float(100 * g.std(ddof=1) / g.mean()),
    minimo=int(g.min()), maximo=int(g.max()),
    q1=float(g.quantile(.25)), q3=float(g.quantile(.75)),
    amplitude_interquartil=float(g.quantile(.75) - g.quantile(.25)),
    assimetria=float(g.skew()), curtose=float(g.kurtosis()),
)
res["descritiva_gols_partida"] = desc
print("\n2.1 Gols por partida (n=104)")
for k, v in desc.items():
    print(f"    {k:<24} {v:.3f}" if isinstance(v, float) else f"    {k:<24} {v}")

# Por etapa da competicao
por_etapa = (partidas.groupby("etapa")["total_gols"]
             .agg(n="count", media="mean", mediana="median", desvio=lambda s: s.std(ddof=1)))
res["gols_por_etapa"] = por_etapa.round(3).to_dict("index")
por_fase = (partidas.groupby(["fase_ordem", "fase"])["total_gols"]
            .agg(n="count", media="mean").reset_index().sort_values("fase_ordem"))
res["gols_por_fase"] = por_fase.drop(columns="fase_ordem").round(3).to_dict("records")
print("\n    Gols por etapa:")
print(por_etapa.round(3).to_string())

# Indicadores das 48 selecoes (por jogo, comparaveis)
ind = ["gols_por_jogo", "gols_sofridos_por_jogo", "posse_media", "precisao_passes",
       "chutes_por_jogo", "chutes_a_gol_por_jogo", "xg_por_jogo", "aproveitamento_pct",
       "precisao_finalizacao", "cartoes_por_jogo"]
tab_ind = sel[ind].agg(["mean", "median", "std", "min", "max"]).T
tab_ind["cv_pct"] = 100 * tab_ind["std"] / tab_ind["mean"]
res["descritiva_indicadores"] = tab_ind.round(3).to_dict("index")
print("\n    Indicadores por selecao (48 selecoes):")
print(tab_ind.round(2).to_string())

# ---------------------------------------------------------------------
# 2.2 ADERENCIA AO MODELO DE POISSON
#     Hipotese: o numero de gols por partida segue Poisson(lambda = media).
# ---------------------------------------------------------------------
lam = g.mean()
obs = g.value_counts().sort_index()
categorias = list(range(0, 6))                 # 0,1,2,3,4,5+
o = [int((g == k).sum()) for k in range(5)] + [int((g >= 5).sum())]
e = [stats.poisson.pmf(k, lam) * len(g) for k in range(5)]
e.append((1 - stats.poisson.cdf(4, lam)) * len(g))
chi2 = float(sum((oi - ei) ** 2 / ei for oi, ei in zip(o, e)))
gl = len(o) - 1 - 1                            # -1 pelo parametro lambda estimado
p_poisson = float(1 - stats.chi2.cdf(chi2, gl))
res["poisson"] = dict(lambda_=float(lam), categorias=["0", "1", "2", "3", "4", "5+"],
                      observado=o, esperado=[round(x, 2) for x in e],
                      chi2=round(chi2, 3), gl=gl, p_valor=round(p_poisson, 4),
                      conclusao=("Nao se rejeita H0: a distribuicao de gols e compativel com "
                                 "Poisson" if p_poisson > .05 else
                                 "Rejeita-se H0: a distribuicao nao e compativel com Poisson"))
print(f"\n2.2 Aderencia a Poisson (lambda={lam:.3f}): chi2={chi2:.3f}, gl={gl}, p={p_poisson:.4f}")
print(f"    {res['poisson']['conclusao']}")

# ---------------------------------------------------------------------
# 2.3 CORRELACAO
#     Spearman (ordinal, robusta a outliers e a n pequeno) entre cada
#     indicador e a classificacao final (1 = campeao -> correlacao
#     negativa significa "quanto maior o indicador, melhor a posicao").
# ---------------------------------------------------------------------
alvo = "classificacao_final"
linhas = []
for c in ind + ["passes_por_jogo", "gols_menos_xg", "pct_clean_sheets", "saldo_gols"]:
    rho, p = stats.spearmanr(sel[c], sel[alvo])
    linhas.append(dict(indicador=c, rho_spearman=round(float(rho), 3), p_valor=round(float(p), 5),
                       significativo_5pct=bool(p < .05), n=int(sel[c].notna().sum())))
corr_class = pd.DataFrame(linhas).sort_values("rho_spearman")
res["correlacao_classificacao"] = corr_class.to_dict("records")
print("\n2.3 Correlacao de Spearman com a classificacao final (1 = campeao)")
print(corr_class.to_string(index=False))

# Matriz de correlacao entre indicadores (Pearson) para o heatmap
matriz = sel[["gols_por_jogo", "gols_sofridos_por_jogo", "xg_por_jogo", "posse_media",
              "precisao_passes", "chutes_por_jogo", "chutes_a_gol_por_jogo",
              "aproveitamento_pct", "cartoes_por_jogo"]].corr(method="pearson").round(3)
res["matriz_correlacao"] = dict(variaveis=list(matriz.columns), valores=matriz.values.tolist())

# Relacao xG x gols marcados (validacao do indicador de qualidade de chance)
r_xg, p_xg = stats.pearsonr(sel["xg"], sel["gols_pro"])
res["correlacao_xg_gols"] = dict(r_pearson=round(float(r_xg), 3), p_valor=float(p_xg),
                                 r2=round(float(r_xg ** 2), 3))
print(f"\n    xG total x gols marcados: r={r_xg:.3f} (R²={r_xg**2:.3f}), p={p_xg:.2e}")

# Posse de bola x resultado - a pergunta classica da disciplina
rho_posse, p_posse = stats.spearmanr(sel["posse_media"], sel["aproveitamento_pct"])
res["correlacao_posse_aproveitamento"] = dict(rho=round(float(rho_posse), 3), p_valor=round(float(p_posse), 5))
print(f"    posse media x aproveitamento: rho={rho_posse:.3f}, p={p_posse:.4f}")

# ---------------------------------------------------------------------
# 2.4 COMPARACAO ENTRE GRUPOS
#     G1 = 32 selecoes que avancaram ao mata-mata
#     G2 = 16 selecoes eliminadas na fase de grupos
#     n pequeno e distribuicoes assimetricas -> teste nao parametrico
#     de Mann-Whitney U, com tamanho de efeito r = Z / sqrt(N).
# ---------------------------------------------------------------------
g1 = sel[sel.avancou_mata_mata == 1]
g2 = sel[sel.avancou_mata_mata == 0]
comp = []
for c in ["posse_media", "precisao_passes", "chutes_a_gol_por_jogo", "xg_por_jogo",
          "gols_por_jogo", "gols_sofridos_por_jogo", "precisao_finalizacao",
          "passes_por_jogo", "cartoes_por_jogo"]:
    a, b = g1[c].dropna(), g2[c].dropna()
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    n1, n2 = len(a), len(b)
    mu, sigma = n1 * n2 / 2, np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u - mu) / sigma
    comp.append(dict(indicador=c,
                     mediana_avancou=round(float(a.median()), 2),
                     mediana_eliminado=round(float(b.median()), 2),
                     media_avancou=round(float(a.mean()), 2),
                     media_eliminado=round(float(b.mean()), 2),
                     U=float(u), p_valor=round(float(p), 5),
                     efeito_r=round(abs(float(z)) / np.sqrt(n1 + n2), 3),
                     significativo_5pct=bool(p < .05)))
comp = pd.DataFrame(comp).sort_values("p_valor")
res["comparacao_grupos"] = comp.to_dict("records")
print("\n2.4 Mann-Whitney U: avancaram (n=32) x eliminados na fase de grupos (n=16)")
print(comp.to_string(index=False))

# Gols por partida: fase de grupos x mata-mata
a = partidas.loc[partidas.etapa == "Grupos", "total_gols"]
b = partidas.loc[partidas.etapa == "Mata-mata", "total_gols"]
u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
res["comparacao_gols_etapa"] = dict(media_grupos=round(float(a.mean()), 3),
                                    media_mata_mata=round(float(b.mean()), 3),
                                    U=float(u), p_valor=round(float(p), 4),
                                    significativo_5pct=bool(p < .05))
print(f"\n    Gols/partida Grupos ({a.mean():.2f}) x Mata-mata ({b.mean():.2f}): "
      f"U={u:.0f}, p={p:.4f}")

# ---------------------------------------------------------------------
# 2.5 ANALISE DE ASSOCIACAO (variaveis categoricas)
# ---------------------------------------------------------------------
assoc = {}

# (a) Terco de posse de bola x avancar ao mata-mata
sel["faixa_posse"] = pd.qcut(sel["posse_media"], 3, labels=["Baixa", "Media", "Alta"])
tab = pd.crosstab(sel["faixa_posse"], sel["avancou_mata_mata"])
chi2_a, p_a, gl_a, _ = stats.chi2_contingency(tab)
v_cramer = np.sqrt(chi2_a / (tab.values.sum() * (min(tab.shape) - 1)))
assoc["posse_x_avanco"] = dict(tabela=tab.to_dict(), chi2=round(float(chi2_a), 3),
                               gl=int(gl_a), p_valor=round(float(p_a), 4),
                               v_cramer=round(float(v_cramer), 3),
                               significativo_5pct=bool(p_a < .05))
print("\n2.5 Associacao - faixa de posse x avanco ao mata-mata")
print(tab.to_string())
print(f"    chi2={chi2_a:.3f}, gl={gl_a}, p={p_a:.4f}, V de Cramer={v_cramer:.3f}")

# (b) Manter a meta invicta x vencer a partida (nivel partida-selecao, n=208)
longa["venceu"] = (longa["resultado"] == "V").astype(int)
tab_b = pd.crosstab(longa["clean_sheet"], longa["venceu"])
chi2_b, p_b, gl_b, _ = stats.chi2_contingency(tab_b)
v_b = np.sqrt(chi2_b / (tab_b.values.sum() * (min(tab_b.shape) - 1)))
p_cs = longa.loc[longa.clean_sheet, "venceu"].mean()
p_ncs = longa.loc[~longa.clean_sheet, "venceu"].mean()
assoc["clean_sheet_x_vitoria"] = dict(
    tabela=tab_b.to_dict(), chi2=round(float(chi2_b), 3), gl=int(gl_b),
    p_valor=float(p_b), v_cramer=round(float(v_b), 3),
    prob_vitoria_com_clean_sheet=round(float(p_cs), 3),
    prob_vitoria_sem_clean_sheet=round(float(p_ncs), 3),
    risco_relativo=round(float(p_cs / p_ncs), 2))
print("\n    Meta invicta x vitoria (208 participacoes de equipes)")
print(f"    P(vitoria | nao sofreu gol) = {p_cs:.1%} | P(vitoria | sofreu gol) = {p_ncs:.1%}")
print(f"    chi2={chi2_b:.3f}, p={p_b:.2e}, V de Cramer={v_b:.3f}, RR={p_cs/p_ncs:.2f}")

# (c) Confederacao x avanco ao mata-mata (Fisher-Freeman-Halton via Monte Carlo qui-quadrado)
tab_c = pd.crosstab(sel["confederacao"], sel["avancou_mata_mata"])
chi2_c, p_c, gl_c, _ = stats.chi2_contingency(tab_c)
assoc["confederacao_x_avanco"] = dict(tabela=tab_c.to_dict(), chi2=round(float(chi2_c), 3),
                                      gl=int(gl_c), p_valor=round(float(p_c), 4),
                                      nota="Celulas com frequencia esperada < 5; resultado exploratorio.")
res["associacao"] = assoc

# ---------------------------------------------------------------------
# Gravacao
# ---------------------------------------------------------------------
(SAIDA / "resultados_estatistica.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
sel.to_csv(DADOS / "selecoes.csv", index=False, encoding="utf-8-sig")
print(f"\n>> saida/resultados_estatistica.json gravado")
