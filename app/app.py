# -*- coding: utf-8 -*-
"""
Painel de Análise de Fomento à Pesquisa Científica (ODS 5 e ODS 18)
Grupo 3: Caio Vinicius, Daniel Oliveira, Maicon Dias, Matheus Rosa, Gabriel Luz
Disciplina: Computação em Nuvem / Engenharia de Software
Arquitetura: Aiven for PostgreSQL (Free Tier) + Streamlit no Render
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Fomento à Pesquisa - ODS 5 e 18",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=600)
def carregar_dados():
    """
    Função de conexão aos dados:
    1. Tenta conectar ao cluster Aiven for PostgreSQL via st.secrets ou DATABASE_URL.
    2. Fallback automático para SQLite local ('etl/fomento_analitico.db').
    3. Fallback secundário para CSV amostral ('etl/dados_amostra_fomento.csv').
    """
    db_uri = None
    fonte_conexao = "Desconhecida"

    # 1. Verifica segredos do Streamlit
    try:
        if hasattr(st, "secrets") and len(st.secrets) > 0 and "connections" in st.secrets:
            if "postgresql" in st.secrets["connections"]:
                db_uri = st.secrets["connections"]["postgresql"]["url"]
                fonte_conexao = "Aiven PostgreSQL (st.secrets)"
    except Exception:
        pass

    if not db_uri and "DATABASE_URL" in os.environ:
        db_uri = os.environ["DATABASE_URL"]
        fonte_conexao = "Aiven PostgreSQL (DATABASE_URL)"

    if db_uri:
        if db_uri.startswith("postgres://"):
            db_uri = db_uri.replace("postgres://", "postgresql+psycopg2://", 1)
        elif db_uri.startswith("postgresql://") and not db_uri.startswith("postgresql+"):
            db_uri = db_uri.replace("postgresql://", "postgresql+psycopg2://", 1)
        try:
            from sqlalchemy import create_engine
            engine = create_engine(db_uri)
            query = "SELECT * FROM fato_bolsas_fomento;"
            df = pd.read_sql(query, engine)
            return df, fonte_conexao
        except Exception as e:
            st.sidebar.warning(f"Não foi possível conectar ao Aiven PostgreSQL ({e}). Usando base local.")

    # 2. Fallback: SQLite local
    sqlite_path = os.path.join(os.path.dirname(__file__), "..", "etl", "fomento_analitico.db")
    if os.path.exists(sqlite_path):
        conn = sqlite3.connect(sqlite_path)
        df = pd.read_sql("SELECT * FROM fato_bolsas_fomento", conn)
        conn.close()
        return df, "Bases Oficiais CAPES + CNPq (SQLite Local)"

    # 3. Fallback: CSV
    csv_path = os.path.join(os.path.dirname(__file__), "..", "etl", "dados_amostra_fomento.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df, "Bases Oficiais CAPES + CNPq (CSV Local)"

    return pd.DataFrame(), "Nenhum dado encontrado"


# Carrega dados
dados_df, fonte_nome = carregar_dados()

if dados_df.empty:
    st.error("Nenhum dado localizado. Execute o script de ETL para popular a base.")
    st.stop()

# Garantir coluna de interseccionalidade preenchida
if "categoria_interseccional" not in dados_df.columns:
    def categorizar(row):
        sexo = row.get("beneficiario_sexo", "")
        raca = row.get("beneficiario_raca_cor", "")
        if sexo == "Feminino":
            if raca in ["Preta", "Parda"]:
                return "Mulher Negra (Preta/Parda)"
            elif raca == "Indígena":
                return "Mulher Indígena"
            elif raca == "Branca":
                return "Mulher Branca"
            elif raca == "Amarela":
                return "Mulher Amarela"
            else:
                return "Mulher (Não informada)"
        elif sexo == "Masculino":
            if raca in ["Preta", "Parda"]:
                return "Homem Negro (Preto/Pardo)"
            elif raca == "Indígena":
                return "Homem Indígena"
            elif raca == "Branca":
                return "Homem Branco"
            elif raca == "Amarela":
                return "Homem Amarelo"
            else:
                return "Homem (Não informada)"
        return "Não informado"

    dados_df["categoria_interseccional"] = dados_df.apply(categorizar, axis=1)

# Normalização de tipos
dados_df["ano"] = dados_df["ano"].astype(int)
dados_df["valor_pago"] = pd.to_numeric(dados_df["valor_pago"], errors="coerce").fillna(0.0)

# Barra Lateral de Filtros
st.sidebar.title("Filtros")
st.sidebar.caption(f"Conexão ativa: **{fonte_nome}**")

opcao_agencia = st.sidebar.radio(
    "Agência de fomento:",
    ["Todas as agências (CAPES e CNPq)", "Apenas CAPES (MEC)", "Apenas CNPq (MCTI)"],
    index=0
)

if opcao_agencia == "Apenas CAPES (MEC)":
    origens_selecionadas = ["CAPES"]
elif opcao_agencia == "Apenas CNPq (MCTI)":
    origens_selecionadas = ["CNPQ"]
else:
    origens_selecionadas = sorted(list(dados_df["origem_dado"].unique()))

anos_disponiveis = sorted(list(dados_df["ano"].unique()))
anos_selecionados = st.sidebar.multiselect("Ano de concessão:", anos_disponiveis, default=anos_disponiveis)

regioes_disponiveis = sorted(list(dados_df["regiao"].unique()))
regioes_selecionadas = st.sidebar.multiselect("Região:", regioes_disponiveis, default=regioes_disponiveis)

areas_disponiveis = sorted(list(dados_df["grande_area"].unique()))
areas_selecionadas = st.sidebar.multiselect("Grande área do conhecimento:", areas_disponiveis, default=areas_disponiveis)

niveis_disponiveis = sorted(list(dados_df["nivel_bolsa"].unique()))
niveis_selecionados = st.sidebar.multiselect("Nível da bolsa:", niveis_disponiveis, default=niveis_disponiveis)

if not anos_selecionados:
    anos_selecionados = anos_disponiveis
if not regioes_selecionadas:
    regioes_selecionadas = regioes_disponiveis
if not areas_selecionadas:
    areas_selecionadas = areas_disponiveis
if not niveis_selecionados:
    niveis_selecionados = niveis_disponiveis

if st.sidebar.button("Redefinir filtros"):
    st.rerun()

# Aplicação dos Filtros
df_filtrado = dados_df[
    (dados_df["ano"].isin(anos_selecionados)) &
    (dados_df["origem_dado"].isin(origens_selecionadas)) &
    (dados_df["regiao"].isin(regioes_selecionadas)) &
    (dados_df["grande_area"].isin(areas_selecionadas)) &
    (dados_df["nivel_bolsa"].isin(niveis_selecionados))
]

# Cabeçalho Principal (limpo, formal e acadêmico)
st.title("Análise de Equidade no Fomento à Pesquisa Científica")
st.markdown("**ODS 5 (Igualdade de Gênero) e ODS 18 (Igualdade Étnico-Racial)**")
st.caption("Grupo 3: Caio Vinicius, Daniel Oliveira, Maicon Dias, Matheus Rosa, Gabriel Luz | Computação em Nuvem / Engenharia de Software (AV3)")

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

# ==============================================================================
# 4 MÉTRICAS PRINCIPAIS (Componente Nativo do Streamlit)
# ==============================================================================
total_bolsas = len(df_filtrado)
orcamento_total = df_filtrado["valor_pago"].sum()

filtro_mni = df_filtrado["categoria_interseccional"].isin(["Mulher Negra (Preta/Parda)", "Mulher Indígena"])
bolsas_mni = filtro_mni.sum()
orcamento_mni = df_filtrado.loc[filtro_mni, "valor_pago"].sum()

pct_bolsas_mni = (bolsas_mni / total_bolsas * 100) if total_bolsas > 0 else 0
pct_orcamento_mni = (orcamento_mni / orcamento_total * 100) if orcamento_total > 0 else 0
gap_orcamentario = pct_orcamento_mni - pct_bolsas_mni

ticket_medio_geral = orcamento_total / total_bolsas if total_bolsas > 0 else 0
ticket_medio_mni = orcamento_mni / bolsas_mni if bolsas_mni > 0 else 0
diff_ticket = ticket_medio_mni - ticket_medio_geral

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Orçamento Total Auditado",
        value=f"R$ {orcamento_total/1e6:,.1f} M",
        help=f"{total_bolsas:,} concessões analisadas ({', '.join(origens_selecionadas)})"
    )

with col2:
    st.metric(
        label="Mulheres Negras e Indígenas",
        value=f"{pct_bolsas_mni:.1f}%",
        help=f"{bolsas_mni:,} bolsas concedidas do total filtrado"
    )

with col3:
    st.metric(
        label="Orçamento para MNI",
        value=f"{pct_orcamento_mni:.1f}%",
        delta=f"{gap_orcamentario:.2f} p.p. (GAP)",
        delta_color="inverse",
        help="Diferença entre o percentual de orçamento recebido e a proporção de bolsas concedidas"
    )

with col4:
    st.metric(
        label="Valor Médio da Bolsa (MNI)",
        value=f"R$ {ticket_medio_mni:,.0f}",
        delta=f"{diff_ticket:+,.0f} vs média geral",
        help=f"Média geral: R$ {ticket_medio_geral:,.0f} por bolsa"
    )

st.markdown("---")

# ==============================================================================
# ABAS ANALÍTICAS
# ==============================================================================
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "Comparativo CAPES e CNPq",
    "Distribuição Orçamentária",
    "Funil de Bolsas por Nível",
    "Distribuição Regional e Áreas",
    "Dados da Amostra"
])

# ------------------------------------------------------------------------------
# ABA 0: COMPARATIVO CAPES E CNPQ
# ------------------------------------------------------------------------------
with tab0:
    st.subheader("Comparativo entre CAPES (MEC) e CNPq (MCTI)")
    st.write(
        "Comparação direta entre as agências federais de fomento, destacando "
        "as diferenças de escopo institucional e a participação de pesquisadoras negras e indígenas."
    )

    df_capes_comp = dados_df[dados_df["origem_dado"] == "CAPES"]
    df_cnpq_comp = dados_df[dados_df["origem_dado"] == "CNPQ"]

    col_capes, col_cnpq = st.columns(2)

    with col_capes:
        st.markdown("#### CAPES")
        st.caption("Foco principal: Pós-graduação Stricto Sensu (Mestrado e Doutorado)")

        total_c = len(df_capes_comp)
        orc_c = df_capes_comp["valor_pago"].sum()
        mni_c = df_capes_comp[df_capes_comp["categoria_interseccional"].isin(["Mulher Negra (Preta/Parda)", "Mulher Indígena"])]
        pct_mni_c = len(mni_c) / total_c * 100 if total_c > 0 else 0
        orc_mni_c = mni_c["valor_pago"].sum() / orc_c * 100 if orc_c > 0 else 0

        st.metric("Total de Bolsas CAPES", f"{total_c:,}")
        st.metric("Orçamento Investido", f"R$ {orc_c/1e6:,.1f} M")
        st.metric("Participação de Mulheres Negras e Indígenas", f"{pct_mni_c:.1f}%")
        st.metric("Orçamento Destinado a MNI", f"{orc_mni_c:.1f}%")

        fig_pie_c = px.pie(
            df_capes_comp,
            names="categoria_interseccional",
            values="valor_pago",
            title="Distribuição do Orçamento na CAPES por Grupo",
            hole=0.4
        )
        fig_pie_c.update_layout(template="plotly_dark", height=340, showlegend=False)
        st.plotly_chart(fig_pie_c, width="stretch")

    with col_cnpq:
        st.markdown("#### CNPq")
        st.caption("Foco principal: Iniciação Científica (IC) e Produtividade em Pesquisa (PQ)")

        total_q = len(df_cnpq_comp)
        orc_q = df_cnpq_comp["valor_pago"].sum()
        mni_q = df_cnpq_comp[df_cnpq_comp["categoria_interseccional"].isin(["Mulher Negra (Preta/Parda)", "Mulher Indígena"])]
        pct_mni_q = len(mni_q) / total_q * 100 if total_q > 0 else 0
        orc_mni_q = mni_q["valor_pago"].sum() / orc_q * 100 if orc_q > 0 else 0

        st.metric("Total de Bolsas CNPq", f"{total_q:,}")
        st.metric("Orçamento Investido", f"R$ {orc_q/1e6:,.1f} M")
        st.metric("Participação de Mulheres Negras e Indígenas", f"{pct_mni_q:.1f}%")
        st.metric("Orçamento Destinado a MNI", f"{orc_mni_q:.1f}%")

        fig_pie_q = px.pie(
            df_cnpq_comp,
            names="categoria_interseccional",
            values="valor_pago",
            title="Distribuição do Orçamento no CNPq por Grupo",
            hole=0.4
        )
        fig_pie_q.update_layout(template="plotly_dark", height=340, showlegend=False)
        st.plotly_chart(fig_pie_q, width="stretch")

    st.markdown("---")
    st.markdown("#### Volume de Bolsas por Nível Acadêmico")
    df_niveis_comp = dados_df.groupby(["origem_dado", "nivel_bolsa"]).agg(
        total_bolsas=("valor_pago", "count"),
        orcamento=("valor_pago", "sum")
    ).reset_index()

    fig_comp_niv = px.bar(
        df_niveis_comp,
        x="nivel_bolsa",
        y="total_bolsas",
        color="origem_dado",
        barmode="group",
        title="Comparação do Volume de Bolsas por Nível de Formação",
        labels={"nivel_bolsa": "Nível da Bolsa", "total_bolsas": "Quantidade de Bolsas", "origem_dado": "Agência"},
        color_discrete_map={"CAPES": "#42A5F5", "CNPQ": "#66BB6A"}
    )
    fig_comp_niv.update_layout(template="plotly_dark", height=420)
    st.plotly_chart(fig_comp_niv, width="stretch")

# ------------------------------------------------------------------------------
# ABA 1: DISTRIBUIÇÃO ORÇAMENTÁRIA
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Distribuição Orçamentária por Grupo Interseccional")
    st.write(
        "Cruzamento entre as metas da ODS 5 (Gênero) e da ODS 18 (Raça/Etnia) "
        "para examinar a proporção de bolsas concedidas em relação ao montante financeiro alocado."
    )

    CORES_INTERSEC = {
        "Mulher Negra (Preta/Parda)": "#E53935",
        "Mulher Indígena": "#FB8C00",
        "Mulher Branca": "#8E24AA",
        "Mulher Amarela": "#FDD835",
        "Homem Negro (Preto/Pardo)": "#1E88E5",
        "Homem Indígena": "#00897B",
        "Homem Branco": "#43A047",
        "Homem Amarelo": "#7CB342",
        "Não informado": "#757575"
    }

    df_grupo = df_filtrado.groupby("categoria_interseccional").agg(
        total_bolsas=("valor_pago", "count"),
        orcamento_total=("valor_pago", "sum"),
        ticket_medio=("valor_pago", "mean")
    ).reset_index()

    total_b = df_grupo["total_bolsas"].sum()
    total_o = df_grupo["orcamento_total"].sum()
    df_grupo["pct_bolsas"] = (df_grupo["total_bolsas"] / total_b * 100).round(2)
    df_grupo["pct_orcamento"] = (df_grupo["orcamento_total"] / total_o * 100).round(2)
    df_grupo["gap_pontos"] = (df_grupo["pct_orcamento"] - df_grupo["pct_bolsas"]).round(2)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig_donut = px.pie(
            df_grupo,
            names="categoria_interseccional",
            values="total_bolsas",
            title="Participação no Total de Bolsas Concedidas (%)",
            hole=0.45,
            color="categoria_interseccional",
            color_discrete_map=CORES_INTERSEC
        )
        fig_donut.update_traces(textinfo="percent+label", textposition="inside")
        fig_donut.update_layout(template="plotly_dark", height=420, showlegend=False)
        st.plotly_chart(fig_donut, width="stretch")

    with col_g2:
        df_ord_orc = df_grupo.sort_values(by="orcamento_total", ascending=True)
        fig_orc = px.bar(
            df_ord_orc,
            x="orcamento_total",
            y="categoria_interseccional",
            orientation="h",
            title="Orçamento Total por Recorte Demográfico (R$)",
            labels={"orcamento_total": "Total Aprovado (R$)", "categoria_interseccional": ""},
            color="categoria_interseccional",
            color_discrete_map=CORES_INTERSEC,
            text=df_ord_orc["orcamento_total"].apply(lambda v: f"R$ {v/1e6:.1f}M")
        )
        fig_orc.update_traces(textposition="outside")
        fig_orc.update_layout(
            template="plotly_dark",
            height=420,
            showlegend=False,
            margin=dict(l=180, r=40, t=50, b=40)
        )
        st.plotly_chart(fig_orc, width="stretch")

    st.markdown("#### Comparação entre Participação em Bolsas e Recursos")
    st.caption("Quando a barra verde (% da Verba) é menor que a azul (% de Bolsas), evidencia-se que o grupo recebe bolsas de menor valor monetário per capita.")

    df_gap_melt = pd.melt(
        df_grupo,
        id_vars=["categoria_interseccional"],
        value_vars=["pct_bolsas", "pct_orcamento"],
        var_name="Tipo_Indicador",
        value_name="Percentual"
    )
    df_gap_melt["Tipo_Indicador"] = df_gap_melt["Tipo_Indicador"].map({
        "pct_bolsas": "% do Total de Bolsas",
        "pct_orcamento": "% da Verba Orçamentária"
    })

    fig_gap = px.bar(
        df_gap_melt,
        x="categoria_interseccional",
        y="Percentual",
        color="Tipo_Indicador",
        barmode="group",
        title="Proporção de Bolsistas vs. Proporção do Orçamento por Grupo",
        labels={"categoria_interseccional": "Grupo", "Percentual": "Participação (%)"},
        color_discrete_map={
            "% do Total de Bolsas": "#42A5F5",
            "% da Verba Orçamentária": "#66BB6A"
        },
        text=df_gap_melt["Percentual"].apply(lambda v: f"{v:.1f}%")
    )
    fig_gap.update_traces(textposition="outside")
    fig_gap.update_layout(
        template="plotly_dark",
        height=420,
        xaxis_tickangle=-20,
        legend_title="Métrica"
    )
    st.plotly_chart(fig_gap, width="stretch")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("#### Evolução Anual do Orçamento")
        df_temporal_base = dados_df[
            (dados_df["origem_dado"].isin(origens_selecionadas)) &
            (dados_df["regiao"].isin(regioes_selecionadas)) &
            (dados_df["grande_area"].isin(areas_selecionadas)) &
            (dados_df["nivel_bolsa"].isin(niveis_selecionados))
        ]

        df_temporal = df_temporal_base.groupby(["ano", "categoria_interseccional"]).agg(
            orcamento=("valor_pago", "sum"),
            bolsas=("valor_pago", "count")
        ).reset_index()

        min_ano = int(df_temporal["ano"].min())
        max_ano = int(df_temporal["ano"].max())

        fig_temp = px.line(
            df_temporal,
            x="ano",
            y="orcamento",
            color="categoria_interseccional",
            markers=True,
            title=f"Evolução Histórica do Orçamento ({min_ano} a {max_ano})",
            labels={"orcamento": "Orçamento Anual (R$)", "ano": "Ano", "categoria_interseccional": "Grupo"},
            color_discrete_map=CORES_INTERSEC
        )
        fig_temp.update_layout(
            template="plotly_dark",
            height=420,
            xaxis=dict(tickmode="linear", dtick=1)
        )
        st.plotly_chart(fig_temp, width="stretch")

    with col_t2:
        st.markdown("#### Maiores Instituições por Volume Financeiro")
        df_ies = df_filtrado.groupby("sigla_ies").agg(
            total_bolsas=("valor_pago", "count"),
            orcamento_total=("valor_pago", "sum")
        ).reset_index().sort_values(by="orcamento_total", ascending=False).head(10)

        fig_ies = px.bar(
            df_ies.sort_values(by="orcamento_total", ascending=True),
            x="orcamento_total",
            y="sigla_ies",
            orientation="h",
            title="Top 10 Instituições com Maior Fomento Aprovado (R$)",
            labels={"orcamento_total": "Total Aprovado (R$)", "sigla_ies": "Instituição (IES)"},
            color="orcamento_total",
            color_continuous_scale="Viridis",
            text=df_ies.sort_values(by="orcamento_total", ascending=True)["orcamento_total"].apply(lambda v: f"R$ {v/1e6:.1f}M")
        )
        fig_ies.update_traces(textposition="outside")
        fig_ies.update_layout(template="plotly_dark", height=420, showlegend=False)
        st.plotly_chart(fig_ies, width="stretch")

# ------------------------------------------------------------------------------
# ABA 2: FUNIL DE BOLSAS POR NÍVEL ACADÊMICO
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Distribuição de Bolsistas por Nível de Formação")
    st.write(
        "Análise comparativa da presença dos diferentes grupos em cada etapa da formação científica, "
        "desde a Iniciação Científica até as bolsas de Produtividade em Pesquisa."
    )

    ordem_carreira = [
        "Iniciação Científica",
        "Mestrado",
        "Doutorado",
        "Pós-Doutorado",
        "Produtividade em Pesquisa"
    ]
    df_funil = df_filtrado[df_filtrado["nivel_bolsa"].isin(ordem_carreira)]

    if not df_funil.empty:
        crosstab_funil = pd.crosstab(
            df_funil["nivel_bolsa"],
            df_funil["categoria_interseccional"],
            normalize="index"
        ) * 100

        crosstab_funil = crosstab_funil.reindex([n for n in ordem_carreira if n in crosstab_funil.index])

        fig_funil = go.Figure()
        for col in crosstab_funil.columns:
            fig_funil.add_trace(go.Bar(
                name=col,
                x=crosstab_funil.index,
                y=crosstab_funil[col],
                text=crosstab_funil[col].apply(lambda v: f"{v:.1f}%" if v > 3 else ""),
                textposition="inside"
            ))

        fig_funil.update_layout(
            barmode="stack",
            title="Composição Percentual por Nível Acadêmico (100% Empilhado)",
            xaxis_title="Nível da Bolsa",
            yaxis_title="Proporção (%)",
            template="plotly_dark",
            height=500,
            legend_title="Grupo Interseccional"
        )
        st.plotly_chart(fig_funil, width="stretch")

        if "Mulher Negra (Preta/Parda)" in crosstab_funil.columns:
            taxa_ic = crosstab_funil.loc["Iniciação Científica", "Mulher Negra (Preta/Parda)"] if "Iniciação Científica" in crosstab_funil.index else 0
            taxa_pq = crosstab_funil.loc["Produtividade em Pesquisa", "Mulher Negra (Preta/Parda)"] if "Produtividade em Pesquisa" in crosstab_funil.index else 0
            queda = taxa_ic - taxa_pq
            st.info(
                f"Observação analítica: A proporção de mulheres negras é de {taxa_ic:.1f}% na Iniciação Científica "
                f"e recua para {taxa_pq:.1f}% nas bolsas de Produtividade em Pesquisa (diferença de {queda:.1f} pontos percentuais)."
            )

# ------------------------------------------------------------------------------
# ABA 3: DISTRIBUIÇÃO REGIONAL E ÁREAS
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("Distribuição por Região Geográfica e Grande Área")

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        df_regiao = df_filtrado.groupby(["regiao", "categoria_interseccional"])["valor_pago"].sum().reset_index()
        fig_regiao = px.bar(
            df_regiao,
            x="regiao",
            y="valor_pago",
            color="categoria_interseccional",
            title="Investimento Total por Região do Brasil (R$)",
            labels={"valor_pago": "Investimento (R$)", "regiao": "Região"},
            barmode="stack"
        )
        fig_regiao.update_layout(template="plotly_dark", height=430)
        st.plotly_chart(fig_regiao, width="stretch")

    with col_m2:
        df_area = df_filtrado.groupby(["grande_area", "categoria_interseccional"])["valor_pago"].sum().reset_index()
        fig_area = px.bar(
            df_area,
            x="valor_pago",
            y="grande_area",
            color="categoria_interseccional",
            orientation="h",
            title="Investimento por Grande Área do Conhecimento (R$)",
            labels={"valor_pago": "Investimento (R$)", "grande_area": "Grande Área"},
            barmode="stack"
        )
        fig_area.update_layout(template="plotly_dark", height=430)
        st.plotly_chart(fig_area, width="stretch")

# ------------------------------------------------------------------------------
# ABA 4: BASE DE DADOS E EXPORTAÇÃO
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("Amostra dos Dados Utilizados")
    st.write(f"Exibindo os primeiros 100 registros da seleção atual ({len(df_filtrado):,} linhas no total).")

    colunas_exibicao = [
        "ano", "origem_dado", "beneficiario_sexo", "beneficiario_raca_cor",
        "categoria_interseccional", "nivel_bolsa", "grande_area", "uf", "regiao", "valor_pago"
    ]
    st.dataframe(
        df_filtrado[colunas_exibicao].head(100),
        width="stretch",
        hide_index=True
    )

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        csv_bytes = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Baixar dados filtrados em CSV",
            data=csv_bytes,
            file_name="dados_fomento_filtrados.csv",
            mime="text/csv"
        )
    with col_d2:
        json_bytes = df_filtrado.head(1000).to_json(orient="records", indent=2, force_ascii=False).encode("utf-8")
        st.download_button(
            label="Baixar amostra em JSON",
            data=json_bytes,
            file_name="dados_fomento_amostra.json",
            mime="application/json"
        )

# Nota Metodológica Retrátil (Transparência Acadêmica)
with st.expander("Nota metodológica e fontes dos dados"):
    st.markdown("""
    * **Fontes de dados:** Microdados públicos abertos do CNPq (Bolsas e Fomento) e Portal de Dados Abertos da CAPES (2022 a 2025).
    * **Valoração:** Bolsas da pós-graduação valoradas segundo as Portarias oficiais do MEC/CAPES e valores nominais de pagamentos individuais do CNPq.
    * **Classificação:** O gênero no CNPq foi inferido pelo primeiro nome registrado; na CAPES, a distribuição sociodemográfica segue as proporções demográficas oficiais do Censo da Pós-Graduação (Geocapes).
    * **Infraestrutura em nuvem:** Banco de dados relacional Aiven for PostgreSQL com índices B-Tree e hospedagem no Render.
    """)

# Rodapé
st.markdown("---")
st.caption("Projeto Prático de Computação em Nuvem | Aiven PostgreSQL + Streamlit no Render | Grupo 3")
