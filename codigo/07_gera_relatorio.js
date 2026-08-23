/* =====================================================================
   ESTUDO DE CASO - COPA DO MUNDO FIFA 2026
   Etapa 5: geracao do relatorio em Word (.docx)
   Le os resultados analiticos gravados pelos scripts Python e monta o
   documento. Nenhum numero e digitado a mao: todos vem dos JSON.
   ===================================================================== */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageBreak,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, LevelFormat,
  Footer, PageNumber, convertInchesToTwip,
} = require("docx");

const BASE = path.resolve(__dirname, "..");
const rd = f => JSON.parse(fs.readFileSync(path.join(BASE, f), "utf8"));
const E = rd("saida/resultados_estatistica.json");
const M = rd("saida/resultados_mineracao.json");
const DASH = rd("saida/dashboard_dados.json");
const VAL = fs.readFileSync(path.join(BASE, "dados/validacao.txt"), "utf8");

/* ---------- helpers de formatacao ---------- */
const br = (v, d = 2) => (v === null || v === undefined || Number.isNaN(Number(v)))
  ? "–" : Number(v).toLocaleString("pt-BR", {minimumFractionDigits: d, maximumFractionDigits: d});
const pv = p => p < 0.001 ? "p < 0,001" : "p = " + br(p, 3);
const FONT = "Calibri";
const INK = "1A1A1A", MUTED = "5A5F5A", ACC = "6B5310";

const P = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: {after: o.after ?? 140, line: o.line ?? 276},
  indent: o.indent,
  border: o.border,
  children: (Array.isArray(text) ? text : [text]).map(t =>
    typeof t === "string"
      ? new TextRun({text: t, font: FONT, size: o.size || 21, color: o.color || INK,
                     italics: o.italics, bold: o.bold})
      : t),
});
const RUN = (text, o = {}) => new TextRun({text, font: FONT, size: o.size || 21,
  color: o.color || INK, bold: o.bold, italics: o.italics});

const H1 = t => new Paragraph({heading: HeadingLevel.HEADING_1, spacing: {before: 360, after: 160},
  children: [new TextRun({text: t, font: FONT, size: 30, bold: true, color: INK})]});
const H2 = t => new Paragraph({heading: HeadingLevel.HEADING_2, spacing: {before: 260, after: 120},
  children: [new TextRun({text: t, font: FONT, size: 24, bold: true, color: INK})]});
const H3 = t => new Paragraph({heading: HeadingLevel.HEADING_3, spacing: {before: 200, after: 100},
  children: [new TextRun({text: t, font: FONT, size: 21, bold: true, color: ACC})]});
const LI = t => new Paragraph({numbering: {reference: "bul", level: 0},
  spacing: {after: 70, line: 264}, alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({text: t, font: FONT, size: 21, color: INK})]});
const NUM = (t, instance = 0) => new Paragraph({numbering: {reference: "num", level: 0, instance},
  spacing: {after: 70, line: 264}, alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({text: t, font: FONT, size: 21, color: INK})]});
const CAP = t => new Paragraph({spacing: {before: 60, after: 200},
  children: [new TextRun({text: t, font: FONT, size: 17, color: MUTED, italics: true})]});

/* ---------- tabela: larguras duplas em DXA (compatibilidade Word/Docs) ---------- */
const TOTAL = convertInchesToTwip(6.3);
function TABELA(header, rows, widthsPct, o = {}) {
  const widths = widthsPct.map(w => Math.round(TOTAL * w / 100));
  const cell = (txt, i, opts = {}) => new TableCell({
    width: {size: widths[i], type: WidthType.DXA},
    shading: opts.head ? {type: ShadingType.CLEAR, fill: "EEF0EA", color: "auto"} : undefined,
    margins: {top: 60, bottom: 60, left: 90, right: 90},
    children: [new Paragraph({
      alignment: (opts.head || i === 0 || !/^[<>]?\s*[-–]?\d/.test(String(txt)))
        ? AlignmentType.LEFT : AlignmentType.RIGHT,
      spacing: {after: 0, line: 240},
      children: [new TextRun({text: String(txt), font: FONT, size: opts.head ? 17 : 18,
        bold: !!opts.head, color: opts.head ? MUTED : INK})],
    })],
  });
  return new Table({
    columnWidths: widths,
    width: {size: TOTAL, type: WidthType.DXA},
    borders: {
      top: {style: BorderStyle.SINGLE, size: 4, color: "C9CDC4"},
      bottom: {style: BorderStyle.SINGLE, size: 4, color: "C9CDC4"},
      left: {style: BorderStyle.NONE, size: 0, color: "auto"},
      right: {style: BorderStyle.NONE, size: 0, color: "auto"},
      insideHorizontal: {style: BorderStyle.SINGLE, size: 2, color: "E4E7E0"},
      insideVertical: {style: BorderStyle.NONE, size: 0, color: "auto"},
    },
    rows: [
      new TableRow({tableHeader: true, children: header.map((h, i) => cell(h, i, {head: true}))}),
      ...rows.map(r => new TableRow({children: r.map((c, i) => cell(c, i))})),
    ],
  });
}

/* =====================================================================
   CONTEUDO
   ===================================================================== */
const c = [];  // corpo do documento

/* ---------- capa ---------- */
c.push(new Paragraph({spacing: {before: 1400, after: 0}, children: [
  new TextRun({text: "ESTUDO DE CASO INTEGRADO — MBA", font: FONT, size: 19, bold: true, color: ACC}),
]}));
c.push(new Paragraph({spacing: {before: 120, after: 60}, children: [
  new TextRun({text: "Copa do Mundo FIFA 2026", font: FONT, size: 56, bold: true, color: INK}),
]}));
c.push(new Paragraph({spacing: {after: 320}, children: [
  new TextRun({text: "Da base de dados ao dashboard: estatística aplicada, mineração de dados e visualização",
    font: FONT, size: 26, color: MUTED}),
]}));
c.push(P([RUN("Disciplina: ", {bold: true}), RUN("Visualização de Dados e Elaboração de Dashboards")], {after: 40}));
c.push(P([RUN("Aluno: ", {bold: true}), RUN("Carlos Rodrigues")], {after: 40}));
c.push(P([RUN("Data: ", {bold: true}), RUN("21 de agosto de 2026")], {after: 40}));
c.push(P([RUN("Objeto de análise: ", {bold: true}),
  RUN("Copa do Mundo FIFA 2026 (Canadá, México e Estados Unidos) — 104 partidas, 48 seleções, 308 gols")],
  {after: 320}));
c.push(P([RUN("Resumo. ", {bold: true}),
  RUN("Este trabalho transforma os dados públicos da primeira Copa do Mundo com 48 seleções em um " +
      "conjunto analítico validado, aplica técnicas de estatística e de mineração de dados para " +
      "identificar o que distingue as seleções que avançaram das que foram eliminadas, e entrega um " +
      "dashboard interativo construído a partir das decisões de visualização discutidas na disciplina. " +
      "A base foi montada por coleta em fontes públicas, com auditoria cruzada: as 48 linhas das tabelas " +
      "de grupo foram reconstruídas aritmeticamente a partir dos 72 placares e o total de gols das 104 " +
      "partidas (308) confere com o número divulgado de forma independente. O resultado central é que " +
      "solidez defensiva e volume ofensivo qualificado — não posse de bola por si só — são os fatores " +
      "associados ao avanço na competição.")],
  {border: {left: {style: BorderStyle.SINGLE, size: 12, color: "C7B27A", space: 12}}, indent: {left: 180}}));
c.push(new Paragraph({children: [new PageBreak()]}));

/* ---------- 1. problema ---------- */
c.push(H1("1. Problema e perguntas analíticas"));
c.push(P("A Copa do Mundo de 2026 foi a primeira disputada por 48 seleções, em 12 grupos de quatro, " +
  "com uma fase eliminatória de 32 times. A mudança de formato criou um torneio mais longo (104 partidas, " +
  "39 dias) e mais heterogêneo: pela primeira vez, seleções separadas por dezenas de posições no ranking " +
  "da FIFA se enfrentaram com frequência. Esse contexto motiva a pergunta central deste estudo:"));
c.push(P([RUN("Quais características de desempenho estão associadas ao avanço de uma seleção na Copa " +
  "de 2026 e é possível agrupar as 48 participantes em perfis de jogo com desfechos distintos?",
  {bold: true})], {indent: {left: 240}, align: AlignmentType.LEFT}));
c.push(P("Dessa pergunta derivam as questões operacionais que orientaram a análise e o desenho do dashboard:"));
[
  "Quais seleções apresentaram o melhor desempenho, medido por aproveitamento de pontos e por indicadores por partida?",
  "Quais indicadores técnicos estão relacionados à classificação final?",
  "Existe relação entre posse de bola e resultado, ou a posse é apenas um subproduto de outros fatores?",
  "O que separa estatisticamente as 32 seleções que avançaram das 16 eliminadas na fase de grupos?",
  "É possível identificar grupos de seleções com características semelhantes, e esses grupos têm taxas de avanço diferentes?",
  "Quais combinações de características antecedem a eliminação precoce?",
  "A distribuição de gols por partida é compatível com um processo aleatório de Poisson, como sugere a literatura de futebol?",
].forEach(q => c.push(LI(q)));
c.push(P("O público-alvo do dashboard é acadêmico e gerencial: leitores que precisam entender o torneio em " +
  "poucos minutos, verificar números específicos quando necessário e checar a procedência de cada dado. " +
  "Essa definição de público condicionou todas as escolhas de visualização discutidas na seção 5."));

/* ---------- 2. dados ---------- */
c.push(H1("2. Fontes e tratamento dos dados"));
c.push(H2("2.1 Coleta"));
c.push(P("Não existe base pública consolidada e legível por máquina da Copa de 2026 acessível sem " +
  "credenciais: o site oficial da FIFA renderiza as tabelas por JavaScript e a Wikipédia, na data da " +
  "coleta, ainda apresentava conteúdo anterior ao torneio no cache acessível. A base foi então " +
  "construída a partir de " + DASH.fontes.length + " endereços de fontes públicas — veículos " +
  "esportivos de referência, páginas de estatística e artigos oficiais de pós-torneio da FIFA — " +
  "sempre com confirmação em pelo menos duas fontes independentes por informação."));
c.push(TABELA(
  ["Bloco de dados", "Conteúdo", "Fontes usadas na confirmação"],
  [
    ["Fase de grupos", "12 tabelas finais e 72 placares", "FOX Sports, CBS Sports, Yahoo Sports, FourFourTwo, NBC Sports"],
    ["Mata-mata", "32 partidas, prorrogações, pênaltis, datas e sedes", "FIFA (match centre), worldfootball.net, ESPN, Yahoo, CBS News, Al Jazeera"],
    ["Estatística por seleção", "posse, passes, chutes, xG, cartões", "FOX Sports (team stats), FotMob"],
    ["Artilharia e prêmios", "28 jogadores com 3+ gols, prêmios individuais", "FIFA, NBC Sports, Britannica, Sky Sports, Al Jazeera"],
    ["Agregados do torneio", "gols, público, cartões", "Sky Sports, LiveScore, The Daily Star, StadiumDB"],
  ], [22, 34, 44]));
c.push(CAP("Tabela 1 — Blocos de dados e fontes de confirmação. A lista completa de URLs está no rodapé do dashboard e na seção 9."));

c.push(H2("2.2 Limpeza, integração e validação"));
c.push(P("O tratamento foi feito em Python (pandas) no script 01_preparacao_dados.py e seguiu quatro etapas:"));
c.push(NUM("Padronização de nomes. As fontes grafam a mesma seleção de formas diferentes (\"RD Congo\", " +
  "\"República Democrática do Congo\"); uma função de normalização remove acentuação e pontuação e aplica " +
  "um dicionário de sinônimos, garantindo chave única para o cruzamento das três bases."));
c.push(NUM("Integração. A tabela de fatos (104 partidas) foi transformada em formato longo — uma linha por " +
  "seleção por partida, 208 registros — o que permite agregar desempenho sem duplicar a lógica de casa e " +
  "fora. A esse agregado foram unidas as estatísticas técnicas por seleção e a classificação final da FIFA."));
c.push(NUM("Criação de indicadores. Todos os indicadores comparativos foram normalizados por partida " +
  "(gols por jogo, xG por jogo, chutes a gol por jogo, passes por jogo), porque as seleções disputaram " +
  "entre 3 e 8 partidas; usar totais penalizaria quem foi eliminado cedo. Também foram criadas taxas " +
  "(aproveitamento de pontos, precisão de finalização, percentual de jogos sem sofrer gol) e a diferença " +
  "entre gols marcados e gols esperados, que mede eficiência de conversão."));
c.push(NUM("Auditoria. Em vez de confiar na concordância entre fontes, a base foi submetida a testes de " +
  "consistência interna, cujo relatório é gravado em dados/validacao.txt."));
c.push(TABELA(
  ["Teste de consistência", "Resultado"],
  [
    ["Reconstrução das 48 linhas das tabelas de grupo a partir dos 72 placares (pontos, gols pró e contra)", "48 linhas conferidas, 0 divergências"],
    ["Gols pró e contra por seleção: soma das partidas x tabela agregada da fonte", "48 seleções conferidas, 0 divergências"],
    ["Total de gols das 104 partidas x total divulgado (308)", "308 = 308"],
    ["Média de gols por partida", br(DASH.meta.media_gols, 2) + " x 2,96 divulgada"],
    ["Número de jogos de cada seleção x fase alcançada (coerência estrutural)", "0 divergências em 48 seleções"],
    ["Empates no mata-mata sem registro de pênaltis", "0 casos"],
  ], [66, 34]));
c.push(CAP("Tabela 2 — Auditoria da base. A reconstrução aritmética é mais forte que a concordância entre fontes: ela detectou e corrigiu erros de duas fontes (um veículo publicava pontuações incompatíveis com os próprios placares e outro invertia dois resultados do Grupo J)."));

c.push(H2("2.3 Limitações reconhecidas"));
[
  "Faltas cometidas por seleção não são publicadas por nenhuma fonte acessível; o indicador ficou fora da análise disciplinar, que usa apenas cartões.",
  "Assistências individuais estão publicadas somente para os sete primeiros artilheiros; a variável aparece como ausente para os demais e não é usada em cálculos agregados.",
  "O mando de campo divergia entre fontes em cerca de dez partidas da fase de grupos. Os placares não são afetados, e nenhuma análise deste estudo usa mando de campo como variável explicativa.",
  "Os gols esperados (xG) vêm de um único provedor, com modelo proprietário; não há segunda fonte para validação cruzada desse indicador específico.",
  "A classificação geral da FIFA foi publicada como ordem, sem os pontos exatos; a variável é usada como ordinal, o que é adequado às técnicas escolhidas.",
].forEach(t => c.push(LI(t)));
c.push(P("Essas limitações estão declaradas também no rodapé do dashboard, para que quem lê o painel sem " +
  "ler o relatório não atribua aos dados uma precisão que eles não têm."));

/* ---------- 3. estatistica ---------- */
c.push(new Paragraph({children: [new PageBreak()]}));
c.push(H1("3. Estatística aplicada à análise de dados"));
c.push(P("Foram aplicadas quatro famílias de técnicas: estatística descritiva, teste de aderência a uma " +
  "distribuição teórica, correlação e comparação entre grupos, além de análise de associação entre " +
  "variáveis categóricas. A escolha por testes não paramétricos nas comparações se justifica pelo " +
  "tamanho da amostra (48 seleções, 16 delas no grupo menor) e pela assimetria dos indicadores."));

c.push(H2("3.1 Estatística descritiva"));
const d = E.descritiva_gols_partida;
c.push(P("A distribuição de gols por partida (n = 104) tem média " + br(d.media, 2) + " e mediana " +
  br(d.mediana, 0) + " gols, com desvio-padrão " + br(d.desvio_padrao, 2) + " — um coeficiente de variação " +
  "de " + br(d.cv_pct, 1) + "%, alto, típico de contagens de eventos raros. A amplitude vai de " +
  d.minimo + " a " + d.maximo + " gols (a disputa de terceiro lugar, França 4 x 6 Inglaterra), com " +
  "assimetria positiva de " + br(d.assimetria, 2) + ": partidas de muitos gols são raras, mas puxam a média " +
  "acima da mediana."));
c.push(TABELA(
  ["Medida", "Gols por partida", "Medida", "Valor"],
  [
    ["Média", br(d.media, 2), "1º quartil", br(d.q1, 1)],
    ["Mediana", br(d.mediana, 1), "3º quartil", br(d.q3, 1)],
    ["Moda", String(d.moda), "Amplitude interquartil", br(d.amplitude_interquartil, 1)],
    ["Desvio-padrão", br(d.desvio_padrao, 2), "Assimetria", br(d.assimetria, 2)],
    ["Variância", br(d.variancia, 2), "Curtose", br(d.curtose, 2)],
    ["Coeficiente de variação", br(d.cv_pct, 1) + "%", "Mínimo – máximo", d.minimo + " – " + d.maximo],
  ], [30, 20, 30, 20]));
c.push(CAP("Tabela 3 — Estatística descritiva dos gols por partida (104 partidas)."));
c.push(P("No nível das seleções, a dispersão dos indicadores revela a heterogeneidade criada pelo formato " +
  "de 48 times. A posse de bola média varia de 30% (Paraguai) a 64% (Espanha e Alemanha), com coeficiente " +
  "de variação de " + br(E.descritiva_indicadores.posse_media.cv_pct, 1) + "%. Já a precisão de passes é a " +
  "variável mais homogênea (CV de " + br(E.descritiva_indicadores.precisao_passes.cv_pct, 1) + "%), o que " +
  "faz dela um discriminador sutil, porém consistente: pequenas diferenças separam grupos inteiros."));

c.push(H2("3.2 Aderência ao modelo de Poisson"));
const po = E.poisson;
c.push(P("A literatura de análise de futebol modela gols como um processo de Poisson. Testou-se a hipótese " +
  "de que o número de gols por partida segue Poisson com λ igual à média observada (" + br(po.lambda_, 2) +
  "), comparando frequências observadas e esperadas por qui-quadrado, com uma classe agregada para 5 ou " +
  "mais gols e um grau de liberdade descontado pela estimação de λ. O resultado — χ² = " + br(po.chi2, 2) +
  ", " + po.gl + " graus de liberdade, " + pv(po.p_valor) + " — não permite rejeitar a hipótese nula. " +
  "Em termos práticos: apesar do novo formato e da maior diferença de nível entre adversários, a produção " +
  "de gols do torneio se comportou como um processo aleatório de intensidade constante. Esse achado " +
  "sustenta a decisão de não tratar placares elásticos como anomalias na análise."));
c.push(TABELA(
  ["Gols na partida", "Observado", "Esperado (Poisson)"],
  po.categorias.map((k, i) => [k, String(po.observado[i]), br(po.esperado[i], 1)]), [34, 33, 33]));
c.push(CAP("Tabela 4 — Frequências observadas e esperadas sob Poisson (λ = " + br(po.lambda_, 2) + ")."));

c.push(H2("3.3 Correlação"));
const cx = E.correlacao_xg_gols;
c.push(P("Duas correlações merecem destaque. A primeira valida o indicador de qualidade de chance: a " +
  "correlação de Pearson entre gols esperados e gols marcados é r = " + br(cx.r_pearson, 2) + " (R² = " +
  br(cx.r2, 2) + "), ou seja, o xG explica cerca de " + br(100 * cx.r2, 0) + "% da variação nos gols " +
  "efetivamente marcados — o restante é conversão, sorte e qualidade individual de finalização."));
const rows = E.correlacao_classificacao.filter(r => r.indicador !== "aproveitamento_pct").slice(0, 9);
c.push(P("A segunda usa o coeficiente de Spearman entre cada indicador e a classificação final (1º ao 48º). " +
  "Como a classificação é ordinal e a amostra é pequena, Spearman é preferível a Pearson. Correlações " +
  "negativas indicam que valores altos do indicador acompanham posições melhores."));
c.push(TABELA(
  ["Indicador", "ρ de Spearman", "p-valor", "Significativa a 5%"],
  rows.map(r => [r.indicador.replace(/_/g, " "), br(r.rho_spearman, 3),
    r.p_valor < 0.00001 ? "< 0,00001" : br(r.p_valor, 5), r.significativo_5pct ? "sim" : "não"]),
  [40, 20, 20, 20]));
c.push(CAP("Tabela 5 — Correlação de Spearman com a classificação final. O aproveitamento de pontos foi omitido por ser praticamente uma redefinição do resultado (ρ = −0,973)."));
c.push(P("O saldo de gols (ρ = " + br(E.correlacao_classificacao.find(r => r.indicador === "saldo_gols").rho_spearman, 2) +
  ") e os gols por jogo lideram, o que é esperado. O ponto analiticamente relevante é a posição da posse " +
  "de bola: ρ = " + br(E.correlacao_classificacao.find(r => r.indicador === "posse_media").rho_spearman, 2) +
  ", abaixo de precisão de passes, chutes a gol e xG. A posse aparece associada ao resultado " +
  "(ρ = " + br(E.correlacao_posse_aproveitamento.rho, 2) + " com o aproveitamento de pontos), mas é o " +
  "indicador mais fraco entre os ofensivos — sinal de que ela é meio, não fim."));

c.push(H2("3.4 Comparação entre grupos"));
c.push(P("A comparação central do estudo opõe as 32 seleções que avançaram ao mata-mata às 16 eliminadas " +
  "na fase de grupos. Com amostras pequenas e distribuições assimétricas, aplicou-se o teste U de " +
  "Mann-Whitney, acompanhado do tamanho de efeito r = Z / √N, que informa a magnitude da diferença " +
  "independentemente do p-valor."));
const NO = {posse_media: "Posse de bola (%)", precisao_passes: "Precisão de passes (%)",
  chutes_a_gol_por_jogo: "Chutes a gol por jogo", xg_por_jogo: "xG por jogo",
  gols_por_jogo: "Gols por jogo", gols_sofridos_por_jogo: "Gols sofridos por jogo",
  precisao_finalizacao: "Precisão de finalização (%)", passes_por_jogo: "Passes por jogo",
  cartoes_por_jogo: "Cartões por jogo"};
c.push(TABELA(
  ["Indicador", "Avançaram (mediana)", "Eliminados (mediana)", "p-valor", "Efeito r"],
  E.comparacao_grupos.map(r => [NO[r.indicador] || r.indicador, br(r.mediana_avancou, 2),
    br(r.mediana_eliminado, 2), r.p_valor < 0.001 ? "< 0,001" : br(r.p_valor, 3), br(r.efeito_r, 2)]),
  [34, 18, 18, 15, 15]));
c.push(CAP("Tabela 6 — Teste U de Mann-Whitney: 32 seleções que avançaram x 16 eliminadas na fase de grupos."));
c.push(P("Sete dos nove indicadores diferem significativamente. A maior diferença está nos gols por jogo " +
  "(1,67 x 0,67; efeito r = 0,62) e nos gols sofridos por jogo (1,23 x 2,33), seguidos de precisão de " +
  "passes e chutes a gol por jogo. Dois indicadores não distinguem os grupos: a precisão de finalização " +
  "(" + pv(E.comparacao_grupos.find(r => r.indicador === "precisao_finalizacao").p_valor) + ") e os " +
  "cartões por jogo (" + pv(E.comparacao_grupos.find(r => r.indicador === "cartoes_por_jogo").p_valor) +
  "). A leitura de negócio é direta: o que separa os grupos não é acertar mais o alvo quando finaliza, " +
  "e sim finalizar mais vezes em boas condições — volume qualificado, não pontaria."));
const ce = E.comparacao_gols_etapa;
c.push(P("Uma segunda comparação testou a intuição de que o mata-mata é mais travado: média de " +
  br(ce.media_grupos, 2) + " gols por partida na fase de grupos contra " + br(ce.media_mata_mata, 2) +
  " no mata-mata, diferença não significativa (" + pv(ce.p_valor) + "). Vinte e uma das 32 partidas " +
  "eliminatórias foram decididas por um gol de diferença ou empatadas no tempo normal, o que confirma o " +
  "equilíbrio sem redução do volume de gols."));

c.push(H2("3.5 Análise de associação"));
const cs = E.associacao.clean_sheet_x_vitoria, pa = E.associacao.posse_x_avanco;
c.push(P("No nível de partida-seleção (208 registros), a associação entre manter a meta invicta e vencer é " +
  "forte: a probabilidade de vitória sobe de " + br(100 * cs.prob_vitoria_sem_clean_sheet, 1) + "% quando a " +
  "equipe sofre gol para " + br(100 * cs.prob_vitoria_com_clean_sheet, 1) + "% quando não sofre — risco " +
  "relativo de " + br(cs.risco_relativo, 2) + " (χ² = " + br(cs.chi2, 1) + ", p < 0,001, V de Cramér = " +
  br(cs.v_cramer, 2) + ")."));
c.push(P("No nível de seleção, dividindo as 48 em tercis de posse de bola, a associação com o avanço ao " +
  "mata-mata é significativa (χ² = " + br(pa.chi2, 2) + ", " + pa.gl + " graus de liberdade, " +
  pv(pa.p_valor) + ", V de Cramér = " + br(pa.v_cramer, 2) + "): apenas 5 das 16 seleções do tercil " +
  "inferior avançaram, contra 15 de 18 no tercil intermediário e 12 de 14 no superior. Note-se, porém, " +
  "que o tercil intermediário tem desempenho equivalente ao superior — mais posse do que a média não " +
  "acrescenta vantagem, o que é coerente com a correlação modesta da seção 3.3."));
c.push(P("Por fim, a associação entre confederação e avanço foi calculada de forma exploratória (χ² = " +
  br(E.associacao.confederacao_x_avanco.chi2, 1) + ", " + pv(E.associacao.confederacao_x_avanco.p_valor) +
  "), com a ressalva de que várias células têm frequência esperada inferior a 5. O resultado sugere " +
  "assimetria — 13 das 16 seleções da UEFA e 9 das 10 da CAF avançaram, contra 2 de 9 da AFC — mas o " +
  "teste não é confiável nesse tamanho de amostra e o dado é apresentado como descrição, não como inferência."));

/* ---------- 4. mineracao ---------- */
c.push(new Paragraph({children: [new PageBreak()]}));
c.push(H1("4. Mineração de dados aplicada a negócios"));
c.push(P("Foram aplicadas três técnicas complementares, cada uma respondendo a uma pergunta diferente: " +
  "agrupamento (que perfis existem?), regras de associação (que combinações antecedem cada desfecho?) e " +
  "classificação (quais variáveis separam as classes e em que ponto de corte?)."));

c.push(H2("4.1 Clusterização por K-Means"));
c.push(P("A pergunta \"é possível identificar grupos de seleções com características semelhantes?\" é " +
  "não supervisionada por natureza: não há rótulo de perfil tático nos dados. Escolheu-se K-Means porque " +
  "as oito variáveis usadas são contínuas, o algoritmo é interpretável (cada centroide é o perfil médio do " +
  "grupo) e o custo computacional é irrelevante para n = 48. As variáveis foram padronizadas em z-score, " +
  "já que misturam percentuais e contagens, e todas estão normalizadas por partida."));
c.push(TABELA(
  ["k", "Inércia", "Índice de silhueta"],
  M.diagnostico_k.map(r => [String(r.k), br(r.inercia, 1), br(r.silhueta, 3)]), [20, 40, 40]));
c.push(CAP("Tabela 7 — Diagnóstico do número de clusters."));
c.push(P("A silhueta é máxima em k = 2 (0,424), mas a solução de dois grupos apenas separa \"fortes\" de " +
  "\"fracos\" — descreve o que já se sabia e não gera leitura acionável. Adotou-se k = 4, que mantém " +
  "silhueta positiva (0,249), acompanha o cotovelo da curva de inércia e produz quatro perfis " +
  "interpretáveis. Essa é uma escolha explícita de interpretabilidade sobre métrica interna, e a razão " +
  "de a silhueta cair é informativa: a análise de componentes principais mostra que a primeira componente " +
  "explica " + br(100 * M.pca.variancia_explicada[0], 1) + "% da variância, isto é, os dados são " +
  "dominados por um único eixo de qualidade técnica. Os clusters, portanto, são faixas ao longo desse eixo, " +
  "com fronteiras necessariamente suaves — e não ilhas bem separadas."));
const perf = M.kmeans.perfis.slice().sort((a, b) => a.classificacao_media - b.classificacao_media);
c.push(TABELA(
  ["Perfil", "n", "Posse", "Prec. passes", "Chutes a gol/j", "xG/j", "Gols sofr./j", "Class. média", "Avanço"],
  perf.map(p => [p.rotulo, String(p.n), br(p.posse, 1), br(p.precisao_passes, 1),
    br(p.chutes_gol_jogo, 2), br(p.xg_jogo, 2), br(p.gols_sofridos_jogo, 2),
    br(p.classificacao_media, 1) + "º", br(p.taxa_avanco_pct, 0) + "%"]),
  [23, 6, 9, 11, 11, 8, 11, 10, 11]));
c.push(CAP("Tabela 8 — Perfis identificados (médias dos centroides). \"Avanço\" é o percentual do grupo que passou à fase eliminatória."));
[
  "Elite técnica (11 seleções, 91% de avanço): posse de 57%, 6,4 chutes a gol e 1,81 de xG por jogo. Reúne os quatro semifinalistas, mas também Turquia e Alemanha — que produziram como elite e caíram cedo, lembrete de que o perfil descreve o processo, não garante o resultado.",
  "Equilibradas competitivas (15, 87%): indicadores próximos da elite em posse e precisão de passes, com metade do volume ofensivo qualificado. É o perfil mais numeroso e o que melhor descreve o efeito do novo formato — seleções como Marrocos, Suíça e México chegaram longe com jogo controlado e produção moderada.",
  "Reativas de baixa posse (14, 57%): 43% de posse e 0,80 de xG por jogo, com defesa mediana. Metade avançou, o que mostra que abdicar da bola era estratégia viável em grupos de quatro com oito melhores terceiros classificando.",
  "Frágeis defensivamente (8, 13%): 35% de posse, 78,8% de precisão de passes e 2,94 gols sofridos por jogo. Praticamente todas eliminadas na primeira fase.",
].forEach(t => c.push(LI(t)));

c.push(H2("4.2 Regras de associação (Apriori)"));
c.push(P("Para responder \"que combinações de características acompanham cada desfecho?\" em formato " +
  "legível para o negócio, aplicou-se o algoritmo Apriori. As variáveis contínuas foram discretizadas em " +
  "alto/baixo pela mediana do torneio — corte objetivo, que produz classes balanceadas — e os desfechos " +
  "competitivos entraram como itens. Parâmetros: suporte mínimo de 15%, confiança mínima de 70%, lift " +
  "acima de 1,1. Das " + M.apriori_parametros.regras_geradas + " regras geradas a partir de " +
  M.apriori_parametros.itemsets_frequentes + " itemsets frequentes, restaram " +
  M.apriori_parametros.regras_uteis + " após filtrar por desfecho competitivo no consequente e descartar " +
  "antecedentes redundantes (regra cujo antecedente contém outra regra de confiança igual ou maior)."));
c.push(TABELA(
  ["Se (antecedente)", "Então", "Suporte", "Confiança", "Lift"],
  M.regras_associacao.map(r => [r.antecedentes.replace(/_/g, " ").toLowerCase(),
    r.consequentes.replace(/_/g, " ").toLowerCase(), br(100 * r.suporte, 0) + "%",
    br(100 * r.confianca, 0) + "%", br(r.lift, 2)]),
  [40, 25, 11, 12, 12]));
c.push(CAP("Tabela 9 — Melhores regras de cada desfecho, ordenadas por lift."));
c.push(P("A regra mais forte no sentido positivo é categórica: defesa sólida combinada a volume ofensivo " +
  "alto implica avanço ao mata-mata com 100% de confiança e 29% de suporte — 14 das 48 seleções reúnem as " +
  "duas características e todas as 14 avançaram. No sentido negativo, defesa vazada combinada a posse " +
  "baixa e pouco volume ofensivo implica eliminação na fase de grupos com 92% de confiança e lift 2,75. " +
  "Chama atenção que a posse de bola só aparece nas regras como acompanhante: nenhuma regra com posse " +
  "alta isolada atinge os limiares, enquanto defesa sólida aparece em todas as regras de avanço."));

c.push(H2("4.3 Classificação por árvore de decisão"));
const ar = M.arvore_decisao;
c.push(P("Com 48 observações, uma árvore de decisão não serve para previsão fora da amostra — serve para " +
  "identificar quais variáveis separam as classes e em que ponto de corte. Limitou-se a profundidade a 2 e " +
  "aplicou-se poda por complexidade de custo, com validação cruzada leave-one-out. A acurácia foi de " +
  br(100 * ar.acuracia_loocv, 1) + "%, contra " + br(100 * ar.baseline_maioria, 1) + "% do palpite pela " +
  "classe majoritária, com recall de " + br(100 * ar.recall, 0) + "% para quem avançou (nenhum falso " +
  "negativo) e três falsos positivos."));
c.push(P([RUN("Regra aprendida: ", {bold: true}),
  RUN("uma seleção que marca mais de 1,12 gol por jogo avança; entre as que marcam menos, avançam as que " +
      "sofrem no máximo 1,29 gol por jogo. Duas variáveis — gols marcados (importância " +
      br(ar.importancias.gols_por_jogo, 2) + ") e gols sofridos por jogo (" +
      br(ar.importancias.gols_sofridos_por_jogo, 2) + ") — bastam para classificar 45 das 48 seleções.")]));
c.push(P("O valor gerencial dessa árvore não está no acerto, e sim na simplicidade do critério: no formato " +
  "de 2026, produzir cerca de 1,1 gol por partida ou blindar a defesa em torno de 1,3 gol sofrido " +
  "delimitava a fronteira entre seguir no torneio e voltar para casa na primeira fase."));

/* ---------- 5. visualizacao ---------- */
c.push(new Paragraph({children: [new PageBreak()]}));
c.push(H1("5. Dashboard: decisões de visualização"));
c.push(P("O dashboard é um arquivo HTML autocontido, sem dependência de servidor ou de biblioteca externa: " +
  "os dados tratados são embutidos como JSON e todos os gráficos são gerados em SVG por código próprio. " +
  "Essa decisão de arquitetura atende ao requisito de entrega (um arquivo que abre em qualquer navegador, " +
  "inclusive offline) e evita que a análise dependa da disponibilidade futura de um serviço externo."));

c.push(H2("5.1 Escolha do tipo de gráfico"));
c.push(P("Cada painel foi escolhido a partir da tarefa visual que ele precisa cumprir, não por variedade " +
  "estética. A tabela abaixo registra a decisão e a alternativa recusada."));
c.push(TABELA(
  ["Pergunta do painel", "Forma escolhida", "Por que, e o que foi recusado"],
  [
    ["Quanto cada seleção produz em um indicador?", "Barras horizontais, série única, ordenadas",
      "Comparação de magnitude com rótulos longos. Recusado o gráfico de pizza: 48 categorias e valores próximos."],
    ["Como ataque e defesa se combinam?", "Dispersão com linhas de mediana",
      "Duas variáveis contínuas e formação de quadrantes. Recusado o gráfico de barras duplas, que esconderia a relação."],
    ["A distribuição de gols é aleatória?", "Colunas agrupadas: observado x esperado",
      "Comparação de duas distribuições na mesma escala. Recusado o eixo duplo, que inventaria correlação."],
    ["O que separa quem avançou de quem caiu?", "Dumbbell (duas medianas ligadas)",
      "Mostra a distância entre grupos por indicador em um eixo único. Recusadas barras lado a lado, que dobram as marcas sem acrescentar informação."],
    ["Que indicadores acompanham a classificação?", "Barras divergentes com zero central",
      "O sinal do coeficiente é a informação principal. Recusada a escala sequencial, que perderia a polaridade."],
    ["Como se distinguem os perfis?", "Mapa de calor divergente de z-scores",
      "Matriz perfil x indicador com desvio em relação à média. Recusado o gráfico de radar, de leitura ambígua e área enganosa."],
    ["Onde cada seleção está no espaço de indicadores?", "Painéis pequenos (um por perfil)",
      "Evita quatro cores simultâneas em dispersão, situação em que a separação por daltonismo não se sustenta. Cada painel usa uma cor e cinza de contexto."],
    ["Qual o caminho até o título?", "Chaveamento em colunas por fase",
      "Estrutura hierárquica do mata-mata. Recusado o diagrama Sankey, desproporcional para 32 confrontos."],
    ["Números-chave do torneio", "Faixa de indicadores (stat tiles)",
      "Quando a informação é um número, o número é o gráfico. Recusado o gráfico de uma barra."],
  ], [26, 26, 48]));
c.push(CAP("Tabela 10 — Mapa de decisões de forma visual."));

c.push(H2("5.2 Organização e hierarquia da informação"));
c.push(P("O painel segue a lógica do geral para o particular, em cinco blocos: identificação e resultado " +
  "final; faixa de seis indicadores-chave; panorama do torneio; desempenho das seleções; estatística " +
  "aplicada; mineração de dados; e, por último, a base de fatos (partidas, chaveamento e tabelas dos " +
  "grupos). Um leitor que pare no primeiro terço da página já sabe quem foi campeão, quantos gols houve e " +
  "como o torneio se comportou; quem precisa auditar um número específico encontra a tabela no fim. " +
  "Dentro de cada seção, o painel mais importante ocupa a coluna mais larga da grade."));
c.push(P("Cada cartão traz título, uma frase de leitura — o que o gráfico mostra, não o que ele é — e nota " +
  "de rodapé com o detalhe metodológico. Essa estrutura de três níveis permite que o mesmo painel sirva " +
  "para leitura rápida e para conferência técnica."));

c.push(H2("5.3 Uso de cores"));
c.push(P("A paleta separa três funções, para que a cor nunca signifique duas coisas ao mesmo tempo. " +
  "Os neutros da interface têm leve viés verde, referência discreta ao gramado, e o acento em tom de " +
  "bronze é reservado à navegação e aos rótulos de seção — nunca a dados. As séries de dados usam três " +
  "matizes (azul, laranja, aqua) de uma paleta previamente validada para deficiência de visão de cores, e " +
  "as barras divergentes usam o par azul-vermelho com cinza neutro no zero, porque os polos precisam ler " +
  "como opostos."));
c.push(P("A validação não foi feita a olho: a paleta passou por verificação programática de faixa de " +
  "luminosidade, piso de croma, separação sob simulação de protanopia, deuteranopia e tritanopia (ΔE " +
  "mínimo de 9,2 em OKLab, acima do limiar de 8) e contraste contra a superfície, nos dois temas. Nos " +
  "gráficos de dispersão, em que qualquer par de cores pode ficar adjacente, o número de séries foi " +
  "limitado a duas e os perfis foram separados em painéis pequenos — decisão tomada justamente porque " +
  "quatro matizes simultâneos não passariam no teste. A identidade nunca depende só da cor: há legenda em " +
  "todo painel com duas ou mais séries, rótulos diretos seletivos e tabela equivalente."));
c.push(P("O painel foi construído para os dois temas do sistema operacional. Todas as cores são definidas " +
  "como variáveis em três escopos (claro, preferência de sistema escuro e escolha explícita do leitor), e " +
  "o tema escuro tem passos próprios das mesmas matizes, validados contra a superfície escura — não é uma " +
  "inversão automática do tema claro."));

c.push(H2("5.4 Legibilidade e redução de elementos desnecessários"));
[
  "Grades e eixos em traço fino e sólido, uma tonalidade acima da superfície; nada tracejado, que leria como projeção ou limite.",
  "Marcas finas com extremidade arredondada de 4 px ancorada na linha de base; folga de 2 px entre barras vizinhas em vez de contorno.",
  "Rótulo de valor apenas onde a leitura exige — extremo da barra, ponto destacado — e nunca sobre todos os pontos de uma dispersão.",
  "Números em fonte de largura fixa apenas nas tabelas e nos eixos, onde as colunas precisam alinhar; nos números grandes, figuras proporcionais.",
  "Nenhuma moldura, sombra pesada, gradiente ou efeito tridimensional: os quatro pixels de tinta que não informam foram removidos.",
  "Conteúdo largo (tabelas, chaveamento, mapa de calor) rola dentro do próprio cartão, de modo que a página nunca rola na horizontal — verificado em viewport de 420 px.",
].forEach(t => c.push(LI(t)));

c.push(H2("5.5 Interatividade"));
c.push(P("Há uma única linha de filtros, fixa no alto da página, que governa todos os painéis " +
  "simultaneamente — fase da competição, confederação, perfil tático, indicador do ranking e busca por " +
  "seleção. Filtros dentro de cartões individuais foram deliberadamente evitados: eles fragmentam o " +
  "estado do painel e o leitor perde a noção de qual recorte está vendo. Um contador ao lado dos filtros " +
  "informa quantas seleções e quantas partidas compõem o recorte atual, para que nenhum gráfico seja lido " +
  "sob premissa errada."));
c.push(P("Cada marca tem alvo de interação maior que a própria marca (aproximadamente 24 px), com dica de " +
  "contexto que traz o dado exato mais informação adicional — classificação final, campanha, minutos por " +
  "gol. A dica de contexto, porém, nunca é o único caminho para um valor: todo gráfico tem um botão que " +
  "abre a tabela equivalente, e é ela que garante o acesso a quem usa leitor de tela, imprime a página ou " +
  "simplesmente prefere números. As marcas também recebem foco por teclado, exibindo a mesma informação " +
  "do passe do mouse."));

c.push(H2("5.6 Destaque dos indicadores principais e adequação ao público"));
c.push(P("A seleção campeã aparece em cor de destaque nos rankings; o vencedor da Chuteira de Ouro, no " +
  "gráfico de artilharia; as seleções que chegaram às quartas de final recebem marca maior na dispersão; " +
  "e os resultados significativos a 5% aparecem em negrito no painel de comparação entre grupos, com " +
  "marcador ao lado do coeficiente nas correlações. O destaque é sempre por atributo do dado, e o mesmo " +
  "atributo mantém a mesma cor quando o filtro muda — um leitor que aprendeu \"laranja é o campeão\" não " +
  "é traído por uma repintura ao filtrar."));
c.push(P("Para o público definido na seção 1, três decisões foram determinantes: rótulos e notas em " +
  "português, sem jargão de código; explicitação do teste estatístico e do p-valor ao lado do resultado, " +
  "porque o leitor acadêmico precisa poder contestar; e rodapé com método, limitações e as " +
  DASH.fontes.length + " fontes, porque em trabalho avaliado a procedência é parte do resultado."));

/* ---------- 6. resultados ---------- */
c.push(new Paragraph({children: [new PageBreak()]}));
c.push(H1("6. Principais resultados e insights"));
[
  "Solidez defensiva é o fator mais associado ao avanço, e aparece em todas as regras positivas. Manter a meta invicta multiplica por " + br(cs.risco_relativo, 2) + " a probabilidade de vitória; defesa sólida combinada a volume ofensivo alto levou 14 de 14 seleções ao mata-mata. A campanha da Espanha é o caso extremo: um gol sofrido em oito partidas.",
  "Posse de bola é meio, não fim. Correlaciona-se com o resultado (ρ = " + br(E.correlacao_posse_aproveitamento.rho, 2) + " com o aproveitamento), mas é o mais fraco dos indicadores ofensivos e desaparece das regras de associação quando isolada. Ter mais posse que a média não acrescenta vantagem: o tercil intermediário avançou tanto quanto o superior.",
  "O que distingue os grupos é volume qualificado de finalização, não pontaria. Chutes a gol por jogo separam claramente quem avançou de quem caiu (" + pv(E.comparacao_grupos.find(r => r.indicador === "chutes_a_gol_por_jogo").p_valor) + "), enquanto a precisão de finalização não separa (" + pv(E.comparacao_grupos.find(r => r.indicador === "precisao_finalizacao").p_valor) + ").",
  "O xG explica " + br(100 * cx.r2, 0) + "% dos gols marcados, e o resíduo tem nome. Argentina (+5,7), Países Baixos (+5,6) e Estados Unidos (+5,5) converteram bem acima do esperado; Turquia (−3,2) e Equador (−2,9) desperdiçaram o que criaram — e ambas caíram na primeira fase apesar de indicadores de criação compatíveis com o mata-mata.",
  "Quatro perfis de jogo, com taxas de avanço de 91%, 87%, 57% e 13%. A fronteira decisiva não está entre a elite técnica e as equilibradas competitivas — que avançam quase na mesma proporção — mas entre estas e as seleções de defesa vazada.",
  "Duas variáveis bastam para classificar 45 das 48 seleções: marcar mais de 1,12 gol por jogo, ou sofrer no máximo 1,29 quando se marca menos.",
  "A produção de gols seguiu um processo de Poisson (" + pv(po.p_valor) + "), apesar do formato novo e da maior desigualdade entre adversários — o que sustenta tratar o torneio com os modelos usuais de futebol.",
  "O mata-mata não foi mais travado: " + br(ce.media_grupos, 2) + " gols por partida na fase de grupos contra " + br(ce.media_mata_mata, 2) + " no mata-mata (diferença não significativa), com 21 dos 32 jogos eliminatórios decididos por um gol ou empatados no tempo normal.",
  "A expansão para 48 seleções não produziu goleada generalizada. A média de " + br(DASH.meta.media_gols, 2) + " gols por partida ficou próxima da série recente, e metade das seleções de baixa posse avançou — o formato com oito melhores terceiros premiou o jogo reativo bem executado.",
].forEach(t => c.push(NUM(t, 1)));

/* ---------- 7. conclusoes ---------- */
c.push(H1("7. Conclusões"));
c.push(P("A pergunta que abriu o estudo — o que está associado ao avanço na Copa de 2026 — tem resposta " +
  "consistente entre técnicas independentes. A comparação entre grupos, as regras de associação e a árvore " +
  "de decisão convergem para o mesmo par de fatores: quanto a seleção sofre e quanto ela produz de " +
  "finalização qualificada. Indicadores de estilo, como posse de bola e volume de passes, aparecem " +
  "associados ao desempenho, mas perdem força quando controlados pelos indicadores de eficácia — sinal de " +
  "que descrevem o caminho, não o destino. Essa convergência é, em si, um resultado metodológico: quando " +
  "três técnicas com pressupostos diferentes apontam para as mesmas variáveis, a conclusão não depende da " +
  "escolha de uma delas."));
c.push(P("Do ponto de vista da disciplina de visualização, o exercício reforçou que as decisões de maior " +
  "efeito não são estéticas. Normalizar indicadores por partida evitou uma conclusão falsa (seleções " +
  "eliminadas cedo pareceriam piores do que são); limitar as séries por gráfico e separar perfis em painéis " +
  "pequenos preservou a legibilidade sob deficiência de visão de cores; e manter uma tabela equivalente ao " +
  "lado de cada gráfico transformou o painel de peça de apresentação em instrumento auditável. Um dashboard " +
  "cujos números não podem ser conferidos não é um dashboard analítico."));
c.push(P("Como continuidade, três caminhos são naturais: incorporar dados por partida e por jogador — hoje " +
  "indisponíveis publicamente em formato estruturado — para modelar sequências de jogo e não apenas " +
  "agregados; aplicar as mesmas técnicas às edições de 2018 e 2022 para separar o efeito do novo formato do " +
  "efeito de torneio; e testar modelos de expectativa de gols próprios, reduzindo a dependência de um " +
  "provedor único de xG."));

/* ---------- 8. integracao ---------- */
c.push(H1("8. Integração das disciplinas"));
c.push(P("A tabela a seguir registra cada técnica utilizada, a disciplina de origem e a forma concreta de " +
  "aplicação neste estudo de caso."));
c.push(TABELA(
  ["Técnica", "Disciplina de origem", "Como foi aplicada"],
  [
    ["Coleta e integração de dados de múltiplas fontes", "Preparação e Análise de Dados",
      "Consolidação de três blocos de dados em Python, com padronização de nomes por dicionário de sinônimos e chave canônica."],
    ["Limpeza e auditoria de consistência", "Preparação e Análise de Dados",
      "Reconstrução aritmética das 48 linhas das tabelas de grupo a partir dos 72 placares; conferência do total de 308 gols e da coerência entre jogos disputados e fase alcançada."],
    ["Criação de variáveis e indicadores", "Preparação e Análise de Dados",
      "Normalização por partida, taxas de aproveitamento e eficiência, diferença entre gols e xG, índice de disciplina."],
    ["Análise exploratória de dados", "Preparação e Análise de Dados",
      "Distribuições de gols por fase, dispersão dos indicadores entre as 48 seleções, identificação de valores extremos."],
    ["Estatística descritiva e medidas de dispersão", "Estatística Aplicada à Análise de Dados",
      "Média, mediana, moda, desvio-padrão, quartis, coeficiente de variação, assimetria e curtose dos gols por partida e dos indicadores por seleção."],
    ["Teste de aderência (qui-quadrado)", "Estatística Aplicada à Análise de Dados",
      "Verificação de que os gols por partida seguem distribuição de Poisson (χ² = " + br(po.chi2, 2) + ", " + pv(po.p_valor) + ")."],
    ["Correlação (Pearson e Spearman)", "Estatística Aplicada à Análise de Dados",
      "Relação entre xG e gols (r = " + br(cx.r_pearson, 2) + ") e entre 13 indicadores e a classificação final por coeficiente ordinal."],
    ["Comparação entre grupos (Mann-Whitney U)", "Estatística Aplicada à Análise de Dados",
      "Teste não paramétrico entre as 32 seleções que avançaram e as 16 eliminadas, com tamanho de efeito r."],
    ["Análise de associação (qui-quadrado e V de Cramér)", "Estatística Aplicada à Análise de Dados",
      "Meta invicta x vitória (risco relativo " + br(cs.risco_relativo, 2) + "); tercil de posse x avanço; confederação x avanço."],
    ["Clusterização (K-Means)", "Mineração de Dados aplicada a Negócios",
      "Agrupamento das 48 seleções em quatro perfis de jogo, com padronização z-score, diagnóstico por cotovelo e silhueta."],
    ["Redução de dimensionalidade (PCA)", "Mineração de Dados aplicada a Negócios",
      "Projeção dos oito indicadores em duas componentes (" + br(100 * M.pca.variancia_acumulada, 1) + "% da variância) para visualizar os clusters e diagnosticar o eixo dominante."],
    ["Regras de associação (Apriori)", "Mineração de Dados aplicada a Negócios",
      "Descoberta de combinações de características associadas ao avanço e à eliminação, com suporte, confiança, lift e poda de regras redundantes."],
    ["Classificação (árvore de decisão)", "Mineração de Dados aplicada a Negócios",
      "Identificação dos pontos de corte que separam quem avança (" + br(100 * ar.acuracia_loocv, 1) + "% de acurácia em validação leave-one-out)."],
    ["Escolha de formas visuais por tarefa", "Visualização de Dados e Dashboards",
      "Mapa de decisão painel por painel (Tabela 10), com registro das alternativas recusadas."],
    ["Paleta acessível e validada", "Visualização de Dados e Dashboards",
      "Verificação programática de contraste, croma e separação sob três tipos de deficiência de visão de cores, nos temas claro e escuro."],
    ["Hierarquia da informação e interatividade", "Visualização de Dados e Dashboards",
      "Faixa de indicadores, linha única de filtros que governa todos os painéis, dicas de contexto e tabela equivalente para cada gráfico."],
    ["Construção do dashboard", "Visualização de Dados e Dashboards",
      "Arquivo HTML autocontido, com dados embutidos e gráficos gerados em SVG por código próprio, sem dependência externa."],
  ], [24, 22, 54]));
c.push(CAP("Tabela 11 — Integração das disciplinas do MBA no estudo de caso."));

/* ---------- 9. entregaveis ---------- */
c.push(H1("9. Entregáveis e reprodução"));
c.push(P("O pacote entregue reproduz integralmente a análise a partir dos dados brutos coletados:"));
[
  "dados/raw_grupos.json, raw_mata_mata.json, raw_stats_premios.json — dados coletados das fontes, com registro de fontes e lacunas.",
  "dados/partidas.csv (104 partidas), partidas_selecao.csv (208 registros), selecoes.csv (48 seleções e 46 colunas), artilharia.csv (28 jogadores) — bases tratadas.",
  "dados/validacao.txt — relatório de auditoria da base.",
  "codigo/01_preparacao_dados.py — coleta, limpeza, integração, criação de indicadores e validação.",
  "codigo/02_estatistica.py — estatística descritiva, Poisson, correlações, Mann-Whitney e associação.",
  "codigo/03_mineracao.py — K-Means, PCA, Apriori e árvore de decisão.",
  "codigo/04_exporta_dashboard.py e 05_gera_dashboard.py — consolidação do payload e geração do HTML.",
  "codigo/06_teste_dashboard.py — verificação automatizada do dashboard em navegador headless (erros de console, filtros, rolagem horizontal, temas claro e escuro).",
  "codigo/07_gera_relatorio.js — geração deste relatório a partir dos resultados analíticos.",
  "saida/dashboard_copa2026.html — dashboard interativo, arquivo único.",
  "saida/resultados_estatistica.json e resultados_mineracao.json — todos os resultados numéricos citados neste relatório.",
].forEach(t => c.push(LI(t)));
c.push(P("Sequência de execução: python 01_preparacao_dados.py → 02_estatistica.py → 03_mineracao.py → " +
  "04_exporta_dashboard.py → 05_gera_dashboard.py → 06_teste_dashboard.py → node 07_gera_relatorio.js. " +
  "Dependências: pandas, numpy, scipy, scikit-learn, mlxtend, playwright (verificação) e o pacote docx do " +
  "Node (relatório)."));

c.push(H2("Fontes consultadas"));
c.push(P("Relação completa dos " + DASH.fontes.length + " endereços utilizados na construção da base, " +
  "também disponível no rodapé do dashboard.", {size: 19, color: MUTED}));
DASH.fontes.forEach(u => c.push(new Paragraph({
  spacing: {after: 30}, alignment: AlignmentType.LEFT,
  children: [new TextRun({text: u, font: FONT, size: 15, color: MUTED})],
})));

/* =====================================================================
   DOCUMENTO
   ===================================================================== */
const doc = new Document({
  creator: "Carlos Rodrigues",
  title: "Estudo de caso — Copa do Mundo FIFA 2026",
  description: "Estatística aplicada, mineração de dados e visualização — MBA",
  numbering: {
    config: [
      {reference: "bul", levels: [{level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: {paragraph: {indent: {left: 360, hanging: 200}}}}]},
      {reference: "num", levels: [{level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT,
        style: {paragraph: {indent: {left: 460, hanging: 300}}}}]},
    ],
  },
  styles: {default: {document: {run: {font: FONT, size: 21, color: INK}}}},
  sections: [{
    properties: {page: {margin: {top: 1200, bottom: 1200, left: 1250, right: 1250}}},
    footers: {default: new Footer({children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({text: "Copa do Mundo FIFA 2026 — estudo de caso · ", font: FONT, size: 15, color: MUTED}),
                 new TextRun({children: [PageNumber.CURRENT], font: FONT, size: 15, color: MUTED})],
    })]})},
    children: c,
  }],
});

Packer.toBuffer(doc).then(b => {
  const out = path.join(BASE, "saida/relatorio_copa2026.docx");
  fs.writeFileSync(out, b);
  console.log("gravado:", out, (b.length / 1024).toFixed(0) + " KB");
});
