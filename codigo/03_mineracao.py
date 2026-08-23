"""
=====================================================================
ESTUDO DE CASO - COPA DO MUNDO FIFA 2026
Etapa 3: Mineracao de Dados aplicada a Negocios
=====================================================================
Tecnicas aplicadas:
  3.1 Clusterizacao (K-Means) das 48 selecoes por perfil de jogo
      - padronizacao z-score, metodo do cotovelo, indice de silhueta
      - reducao de dimensionalidade por PCA para visualizacao
  3.2 Regras de associacao (Apriori) sobre atributos discretizados
  3.3 Classificacao (arvore de decisao) com validacao cruzada
      leave-one-out - usada como leitura de importancia de variaveis

Saida: saida/resultados_mineracao.json
=====================================================================
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.metrics import confusion_matrix, precision_score, recall_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

BASE = Path(__file__).resolve().parent.parent
DADOS, SAIDA = BASE / "dados", BASE / "saida"
sel = pd.read_csv(DADOS / "selecoes.csv")
res = {}

print("=" * 70)
print("3. MINERACAO DE DADOS")
print("=" * 70)

# ---------------------------------------------------------------------
# 3.1 CLUSTERIZACAO K-MEANS
#     Justificativa: o objetivo e descobrir GRUPOS de selecoes com
#     estilos de jogo semelhantes sem rotulo previo -> tarefa nao
#     supervisionada. K-Means e adequado para variaveis continuas,
#     e interpretavel (centroides = perfil medio) e escala bem com
#     n=48. Todas as variaveis sao "por jogo" para nao penalizar
#     selecoes eliminadas cedo, e padronizadas em z-score porque as
#     unidades sao heterogeneas (%, contagens).
# ---------------------------------------------------------------------
VARS = ["posse_media", "precisao_passes", "passes_por_jogo", "chutes_por_jogo",
        "chutes_a_gol_por_jogo", "xg_por_jogo", "gols_por_jogo", "gols_sofridos_por_jogo"]
X = sel[VARS].to_numpy(float)
Z = StandardScaler().fit_transform(X)

diag = []
for k in range(2, 8):
    km = KMeans(n_clusters=k, n_init=50, random_state=42).fit(Z)
    diag.append(dict(k=k, inercia=round(float(km.inertia_), 2),
                     silhueta=round(float(silhouette_score(Z, km.labels_)), 3)))
res["diagnostico_k"] = diag
print("\n3.1 Escolha do numero de clusters")
print(pd.DataFrame(diag).to_string(index=False))

# A silhueta e maxima em k=2 (0,424), mas a solucao de 2 grupos apenas separa
# "fortes" de "fracos" e nao gera leitura de negocio. O cotovelo da inercia e a
# interpretabilidade dos centroides sustentam k=4, que preserva silhueta positiva
# (0,249) e produz quatro perfis taticos distintos. A escolha e discutida no relatorio.
K = 4
km = KMeans(n_clusters=K, n_init=100, random_state=42).fit(Z)
sel["cluster"] = km.labels_
sil_final = float(silhouette_score(Z, km.labels_))

perfil = sel.groupby("cluster").agg(
    n=("selecao", "count"),
    posse=("posse_media", "mean"), precisao_passes=("precisao_passes", "mean"),
    passes_jogo=("passes_por_jogo", "mean"), chutes_jogo=("chutes_por_jogo", "mean"),
    chutes_gol_jogo=("chutes_a_gol_por_jogo", "mean"), xg_jogo=("xg_por_jogo", "mean"),
    gols_jogo=("gols_por_jogo", "mean"), gols_sofridos_jogo=("gols_sofridos_por_jogo", "mean"),
    aproveitamento=("aproveitamento_pct", "mean"),
    classificacao_media=("classificacao_final", "mean"),
    taxa_avanco_pct=("avancou_mata_mata", lambda s: 100 * s.mean()),
).round(2)
print("\n    Perfil dos clusters (medias)")
print(perfil.to_string())

# Rotulos interpretativos, atribuidos pela leitura dos centroides
ordem = perfil.sort_values("classificacao_media").index.tolist()
NOMES = ["Elite técnica", "Equilibradas competitivas", "Reativas de baixa posse", "Frágeis defensivamente"]
rotulos = {c: NOMES[i] for i, c in enumerate(ordem)}
sel["perfil_cluster"] = sel["cluster"].map(rotulos)
perfil["rotulo"] = [rotulos[c] for c in perfil.index]

res["kmeans"] = dict(
    k=K, variaveis=VARS, silhueta=round(sil_final, 3),
    perfis=perfil.reset_index().to_dict("records"),
    membros={rotulos[c]: sel.loc[sel.cluster == c, "selecao"].tolist() for c in sorted(rotulos)},
)
print("\n    Composicao dos clusters")
for c in sorted(rotulos):
    print(f"    [{rotulos[c]}] ({(sel.cluster == c).sum()}): "
          f"{', '.join(sel.loc[sel.cluster == c, 'selecao'])}")

# PCA para visualizacao 2D no dashboard
pca = PCA(n_components=2, random_state=42).fit(Z)
comp = pca.transform(Z)
sel["pca_x"], sel["pca_y"] = comp[:, 0], comp[:, 1]
res["pca"] = dict(
    variancia_explicada=[round(float(v), 3) for v in pca.explained_variance_ratio_],
    variancia_acumulada=round(float(pca.explained_variance_ratio_.sum()), 3),
    cargas={v: [round(float(pca.components_[0][i]), 3), round(float(pca.components_[1][i]), 3)]
            for i, v in enumerate(VARS)},
)
print(f"\n    PCA: PC1={pca.explained_variance_ratio_[0]:.1%}, "
      f"PC2={pca.explained_variance_ratio_[1]:.1%} "
      f"(acumulado {pca.explained_variance_ratio_.sum():.1%})")

# ---------------------------------------------------------------------
# 3.2 REGRAS DE ASSOCIACAO (APRIORI)
#     Justificativa: responde "quais combinacoes de caracteristicas
#     aparecem junto com o avanco na competicao?" em formato de regra
#     legivel para o negocio (SE ... ENTAO ...), com suporte,
#     confianca e lift. Variaveis continuas foram discretizadas em
#     ALTO/BAIXO pela mediana do torneio (corte objetivo e balanceado).
# ---------------------------------------------------------------------
def binariza(coluna, nome_alto, nome_baixo):
    m = sel[coluna].median()
    return pd.DataFrame({nome_alto: sel[coluna] > m, nome_baixo: sel[coluna] <= m})


trans = pd.concat([
    binariza("posse_media", "posse_ALTA", "posse_BAIXA"),
    binariza("precisao_passes", "passe_PRECISO", "passe_IMPRECISO"),
    binariza("chutes_a_gol_por_jogo", "volume_ofensivo_ALTO", "volume_ofensivo_BAIXO"),
    binariza("xg_por_jogo", "xg_ALTO", "xg_BAIXO"),
    binariza("gols_sofridos_por_jogo", "defesa_VAZADA", "defesa_SOLIDA"),
    binariza("cartoes_por_jogo", "indisciplina_ALTA", "indisciplina_BAIXA"),
], axis=1)
trans["AVANCOU_MATA_MATA"] = sel["avancou_mata_mata"] == 1
trans["CHEGOU_AS_QUARTAS"] = sel["top8"] == 1
trans["ELIMINADO_NOS_GRUPOS"] = sel["avancou_mata_mata"] == 0

itens = apriori(trans, min_support=0.15, use_colnames=True)
regras = association_rules(itens, metric="confidence", min_threshold=0.70)
regras["antecedentes"] = regras["antecedents"].apply(lambda s: " + ".join(sorted(s)))
regras["consequentes"] = regras["consequents"].apply(lambda s: " + ".join(sorted(s)))
regras["n_ant"] = regras["antecedents"].apply(len)

ALVOS = {"AVANCOU_MATA_MATA", "CHEGOU_AS_QUARTAS", "ELIMINADO_NOS_GRUPOS"}
uteis = regras[
    regras["consequents"].apply(lambda s: set(s).issubset(ALVOS)) &
    ~regras["antecedents"].apply(lambda s: bool(set(s) & ALVOS)) &
    (regras["lift"] > 1.1) & (regras["n_ant"] <= 3)
].sort_values(["lift", "confidence", "support"], ascending=False)

# Poda de redundancia: descarta a regra cujo antecedente e superconjunto de
# outra regra com o mesmo consequente e confianca igual ou maior (a regra mais
# simples explica o mesmo fenomeno).
def nao_redundante(df):
    manter = []
    for i, r in df.iterrows():
        redundante = any(
            (o.consequents == r.consequents) and (o.antecedents < r.antecedents)
            and (o.confidence >= r.confidence - 1e-9)
            for _, o in df.iterrows() if o.name != i)
        if not redundante:
            manter.append(i)
    return df.loc[manter]


uteis = nao_redundante(uteis)

# Selecao equilibrada: as melhores regras de cada desfecho, nao apenas as de
# maior lift (que seriam todas do mesmo consequente).
cols = ["antecedentes", "consequentes", "support", "confidence", "lift"]
escolhidas = pd.concat([
    g.sort_values(["lift", "confidence"], ascending=False).head(4)
    for _, g in uteis.groupby("consequentes")
]).sort_values(["lift", "confidence"], ascending=False)
res["regras_associacao"] = (escolhidas[cols].round(3)
                            .rename(columns={"support": "suporte", "confidence": "confianca"})
                            .to_dict("records"))
res["regras_associacao_todas"] = (uteis[cols].round(3)
                                  .rename(columns={"support": "suporte", "confidence": "confianca"})
                                  .sort_values("lift", ascending=False).to_dict("records"))
res["apriori_parametros"] = dict(suporte_minimo=0.15, confianca_minima=0.70,
                                lift_minimo=1.1, itemsets_frequentes=int(len(itens)),
                                regras_geradas=int(len(regras)), regras_uteis=int(len(uteis)),
                                poda="antecedentes redundantes descartados")
print(f"\n3.2 Apriori: {len(itens)} itemsets frequentes, {len(regras)} regras, "
      f"{len(uteis)} relevantes apos poda de redundancia")
print(escolhidas[cols].round(3).to_string(index=False))

# ---------------------------------------------------------------------
# 3.3 CLASSIFICACAO - ARVORE DE DECISAO
#     Usada de forma complementar: com n=48 o objetivo nao e previsao,
#     e identificar quais indicadores separam melhor as classes e em
#     que ponto de corte. Profundidade limitada a 3 para evitar
#     sobreajuste; validacao leave-one-out.
# ---------------------------------------------------------------------
Xc = sel[VARS]
y = sel["avancou_mata_mata"]
arv = DecisionTreeClassifier(max_depth=2, min_samples_leaf=6, ccp_alpha=0.01, random_state=42)
acc = cross_val_score(arv, Xc, y, cv=LeaveOneOut(), scoring="accuracy").mean()
pred_loo = cross_val_predict(arv, Xc, y, cv=LeaveOneOut())
mc = confusion_matrix(y, pred_loo)          # linhas: real, colunas: previsto
prec = precision_score(y, pred_loo)
rec = recall_score(y, pred_loo)
arv.fit(Xc, y)
imp = (pd.Series(arv.feature_importances_, index=VARS)
       .sort_values(ascending=False).round(3))
baseline = float(max(y.mean(), 1 - y.mean()))
res["arvore_decisao"] = dict(
    acuracia_loocv=round(float(acc), 3), baseline_maioria=round(baseline, 3),
    precisao=round(float(prec), 3), recall=round(float(rec), 3),
    matriz_confusao=mc.tolist(), profundidade_maxima=2,
    importancias=imp[imp > 0].to_dict(),
    regras_texto=export_text(arv, feature_names=VARS, decimals=2),
)
print(f"\n3.3 Arvore de decisao - acuracia LOOCV: {acc:.1%} "
      f"(baseline da classe majoritaria: {baseline:.1%})")
print(f"    precisao={prec:.1%}  recall={rec:.1%}  matriz de confusao (LOOCV)={mc.tolist()}")
print("    Importancia das variaveis:")
print(imp[imp > 0].to_string())
print("\n" + export_text(arv, feature_names=VARS, decimals=2))

# ---------------------------------------------------------------------
sel.to_csv(DADOS / "selecoes.csv", index=False, encoding="utf-8-sig")
(SAIDA / "resultados_mineracao.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(">> saida/resultados_mineracao.json gravado")
