# -*- coding: utf-8 -*-
"""
Dashboard de Auditoria Analítica em Fomento à Pesquisa Científica (ODS 5 & ODS 18)
Grupo 3: Caio Vinicius, Daniel Oliveira, Maicon Dias, Yuri Sales, Gabriel Luz
Disciplina: Computação em Nuvem / Engenharia de Software
Arquitetura: Aiven for PostgreSQL (Free Tier) + Streamlit Community Cloud
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Auditoria ODS 5 & ODS 18 | Fomento Científico",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada para os cards e interface
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222B;
        border-radius: 10px;
        padding: 16px;
        border-left: 5px solid #2E7D32;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 13px;
        text-transform: uppercase;
        color: #A0AEC0;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF;
        margin-top: 4px;
    }
    .metric-subtitle {
        font-size: 12px;
        color: #81C784;
        margin-top: 2px;
    }
    .metric-warning {
        border-left-color: #E53935 !important;
    }
    .metric-warning-subtitle {
        color: #EF5350 !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=600)
def carregar_dados():
    """
    Função resiliente de conexão:
    1. Tenta conectar ao cluster gerenciado Aiven for PostgreSQL via st.secrets ou DATABASE_URL.
    2. Fallback automático para SQLite local ('etl/fomento_analitico.db').
    3. Fallback secundário para CSV amostral ('etl/dados_amostra_fomento.csv').
    """
    db_uri = None
    fonte_conexao = "Desconhecida"

    # 1. Verifica segredos do Streamlit Cloud / local (com proteção contra arquivo ausente)
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
            db_uri = db_uri.replace("postgres://", "postgresql://", 1)
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
    st.error("Erro crítico: Nenhum dado de fomento à pesquisa foi localizado. Execute o script `py etl/etl_pipeline.py` para gerar a base.")
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
            else:
                return "Mulher Outras/Não inf."
        elif sexo == "Masculino":
            if raca in ["Preta", "Parda"]:
                return "Homem Negro (Preto/Pardo)"
            elif raca == "Indígena":
                return "Homem Indígena"
            elif raca == "Branca":
                return "Homem Branco"
            else:
                return "Homem Outros/Não inf."
        return "Não informado"
    dados_df["categoria_interseccional"] = dados_df.apply(categorizar, axis=1)

# Barra Lateral (Filtros Reativos)
st.sidebar.image("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/graduation-cap.svg", width=50)
st.sidebar.title("Filtros Analíticos")
st.sidebar.caption(f"Conexão ativa: **{fonte_nome}**")

# Seletor Principal de Origem / Agência
st.sidebar.markdown("### 🏛️ Agência Financiadora")
opcao_agencia = st.sidebar.radio(
    "Visualizar fomento de:",
    ["Todas as Agências (CAPES + CNPq)", "Apenas CAPES (MEC)", "Apenas CNPq (MCTI)"],
    index=0
)

if opcao_agencia == "Apenas CAPES (MEC)":
    origens_selecionadas = ["CAPES"]
elif opcao_agencia == "Apenas CNPq (MCTI)":
    origens_selecionadas = ["CNPQ"]
else:
    origens_selecionadas = sorted(list(dados_df["origem_dado"].unique()))

anos_disponiveis = sorted(list(dados_df["ano"].unique()))
anos_selecionados = st.sidebar.multiselect("Ano de Concessão", anos_disponiveis, default=anos_disponiveis)

regioes_disponiveis = sorted(list(dados_df["regiao"].unique()))
regioes_selecionadas = st.sidebar.multiselect("Região do País", regioes_disponiveis, default=regioes_disponiveis)

areas_disponiveis = sorted(list(dados_df["grande_area"].unique()))
areas_selecionadas = st.sidebar.multiselect("Grande Área do Conhecimento", areas_disponiveis, default=areas_disponiveis)

niveis_disponiveis = sorted(list(dados_df["nivel_bolsa"].unique()))
niveis_selecionados = st.sidebar.multiselect("Nível da Bolsa / Fomento", niveis_disponiveis, default=niveis_disponiveis)

# Proteção anti-falha para a apresentação: se todos os itens de um filtro forem desmarcados no 'x',
# restaura automaticamente para 'todos', evitando tela em branco na frente da banca!
if not anos_selecionados:
    anos_selecionados = anos_disponiveis
if not regioes_selecionadas:
    regioes_selecionadas = regioes_disponiveis
if not areas_selecionadas:
    areas_selecionadas = areas_disponiveis
if not niveis_selecionados:
    niveis_selecionados = niveis_disponiveis

# Botão de reset rápido para o apresentador
if st.sidebar.button("🔄 Redefinir Todos os Filtros"):
    st.rerun()

# Aplicação dos Filtros
df_filtrado = dados_df[
    (dados_df["ano"].isin(anos_selecionados)) &
    (dados_df["origem_dado"].isin(origens_selecionadas)) &
    (dados_df["regiao"].isin(regioes_selecionadas)) &
    (dados_df["grande_area"].isin(areas_selecionadas)) &
    (dados_df["nivel_bolsa"].isin(niveis_selecionados))
]

# Cabeçalho Principal
st.title("🔬 Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa")
st.markdown("""
**Grupo 3** | Caio Vinicius, Daniel Oliveira, Maicon Dias, Yuri Sales, Gabriel Luz  
*Pipeline em Nuvem Aiven (PostgreSQL) com foco na interseccionalidade entre a **ODS 5 (Igualdade de Gênero)** e a **ODS 18 (Igualdade Étnico-Racial)**.*
""")

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado para a combinação de filtros selecionada.")
    st.stop()

# ==============================================================================
# 4 MÉTRICAS CHAVE OBRIGATÓRIAS (KPIs)
# ==============================================================================
total_bolsas = len(df_filtrado)
orcamento_total = df_filtrado["valor_pago"].sum()

# Segmento de interesse prioritário: Mulheres Negras e Indígenas
filtro_mni = df_filtrado["categoria_interseccional"].isin(["Mulher Negra (Preta/Parda)", "Mulher Indígena"])
bolsas_mni = filtro_mni.sum()
orcamento_mni = df_filtrado.loc[filtro_mni, "valor_pago"].sum()

pct_bolsas_mni = (bolsas_mni / total_bolsas * 100) if total_bolsas > 0 else 0
pct_orcamento_mni = (orcamento_mni / orcamento_total * 100) if orcamento_total > 0 else 0

# GAP financeiro interseccional (Diferença entre representação quantitativa e orçamentária)
gap_orcamentario = pct_orcamento_mni - pct_bolsas_mni

# Ticket médio
ticket_medio_geral = orcamento_total / total_bolsas if total_bolsas > 0 else 0
ticket_medio_mni = orcamento_mni / bolsas_mni if bolsas_mni > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">1. Orçamento Total Auditado</div>
        <div class="metric-value">R$ {orcamento_total/1e6:,.1f} M</div>
        <div class="metric-subtitle">{total_bolsas:,} concessões analisadas ({', '.join(origens_selecionadas)})</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">2. Mulheres Negras e Indígenas</div>
        <div class="metric-value">{pct_bolsas_mni:.1f}%</div>
        <div class="metric-subtitle">{bolsas_mni:,} bolsas concedidas</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card metric-warning">
        <div class="metric-title">3. Verba Destinada a MNI</div>
        <div class="metric-value">{pct_orcamento_mni:.1f}%</div>
        <div class="metric-subtitle metric-warning-subtitle">GAP de Representação: {gap_orcamentario:.2f} p.p.</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    diff_ticket = ticket_medio_mni - ticket_medio_geral
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">4. Ticket Médio da Bolsa</div>
        <div class="metric-value">R$ {ticket_medio_mni:,.0f}</div>
        <div class="metric-subtitle">Média Geral: R$ {ticket_medio_geral:,.0f} (Dif: {diff_ticket:+,.0f})</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# ABAS ANALÍTICAS INTERATIVAS
# ==============================================================================
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "⚔️ Comparativo CAPES vs CNPq",
    "📊 Disparidade Orçamentária & Equidade",
    "🧪 O Funil Científico (Leaky Pipeline)",
    "🗺️ Assimetrias Regionais e Grandes Áreas",
    "📋 Base de Dados & Auditoria"
])

# ------------------------------------------------------------------------------
# ABA 0: COMPARATIVO DIRETO CAPES VS CNPQ
# ------------------------------------------------------------------------------
with tab0:
    st.subheader("⚔️ Auditoria Comparativa: CAPES (MEC) vs. CNPq (MCTI)")
    st.markdown("""
    Comparação direta entre as duas principais agências federais de fomento à pesquisa e formação científica 
    no Brasil, evidenciando as diferenças em seus papéis e na inclusão de pesquisadoras negras e indígenas.
    """)

    df_capes_comp = dados_df[dados_df["origem_dado"] == "CAPES"]
    df_cnpq_comp = dados_df[dados_df["origem_dado"] == "CNPQ"]

    col_capes, col_cnpq = st.columns(2)

    with col_capes:
        st.markdown("#### 🎓 CAPES (Coordenação de Aperfeiçoamento de Pessoal de Nível Superior)")
        st.caption("Foco prioritário: Pós-graduação *Stricto Sensu* (Mestrado e Doutorado)")
        
        total_c = len(df_capes_comp)
        orc_c = df_capes_comp["valor_pago"].sum()
        mni_c = df_capes_comp[df_capes_comp["categoria_interseccional"].isin(["Mulher Negra (Preta/Parda)", "Mulher Indígena"])]
        pct_mni_c = len(mni_c) / total_c * 100 if total_c > 0 else 0
        orc_mni_c = mni_c["valor_pago"].sum() / orc_c * 100 if orc_c > 0 else 0

        st.metric("Total de Concessões CAPES", f"{total_c:,}")
        st.metric("Orçamento Investido CAPES", f"R$ {orc_c/1e6:,.1f} M")
        st.metric("Bolsas para Mulheres Negras/Indígenas", f"{pct_mni_c:.1f}%")
        st.metric("Orçamento para Mulheres Negras/Indígenas", f"{orc_mni_c:.1f}%")

        # Gráfico Donut CAPES
        fig_pie_c = px.pie(
            df_capes_comp,
            names="categoria_interseccional",
            values="valor_pago",
            title="Distribuição do Orçamento na CAPES por Grupo",
            hole=0.4
        )
        fig_pie_c.update_layout(template="plotly_dark", height=350, showlegend=False)
        st.plotly_chart(fig_pie_c, width='stretch')

    with col_cnpq:
        st.markdown("#### 🔬 CNPq (Conselho Nacional de Desenvolvimento Científico e Tecnológico)")
        st.caption("Foco prioritário: Iniciação Científica (IC) e Produtividade em Pesquisa (PQ)")
        
        total_q = len(df_cnpq_comp)
        orc_q = df_cnpq_comp["valor_pago"].sum()
        mni_q = df_cnpq_comp[df_cnpq_comp["categoria_interseccional"].isin(["Mulher Negra (Preta/Parda)", "Mulher Indígena"])]
        pct_mni_q = len(mni_q) / total_q * 100 if total_q > 0 else 0
        orc_mni_q = mni_q["valor_pago"].sum() / orc_q * 100 if orc_q > 0 else 0

        st.metric("Total de Concessões CNPq", f"{total_q:,}")
        st.metric("Orçamento Investido CNPq", f"R$ {orc_q/1e6:,.1f} M")
        st.metric("Bolsas para Mulheres Negras/Indígenas", f"{pct_mni_q:.1f}%")
        st.metric("Orçamento para Mulheres Negras/Indígenas", f"{orc_mni_q:.1f}%")

        # Gráfico Donut CNPq
        fig_pie_q = px.pie(
            df_cnpq_comp,
            names="categoria_interseccional",
            values="valor_pago",
            title="Distribuição do Orçamento no CNPq por Grupo",
            hole=0.4
        )
        fig_pie_q.update_layout(template="plotly_dark", height=350, showlegend=False)
        st.plotly_chart(fig_pie_q, width='stretch')

    st.markdown("---")
    st.markdown("#### 📊 Distribuição por Nível de Formação: CAPES vs. CNPq")
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
        title="Volume de Bolsas por Nível Acadêmico em Cada Agência",
        labels={"nivel_bolsa": "Nível da Bolsa", "total_bolsas": "Quantidade de Bolsas", "origem_dado": "Agência"},
        color_discrete_map={"CAPES": "#42A5F5", "CNPQ": "#66BB6A"}
    )
    fig_comp_niv.update_layout(template="plotly_dark", height=430)
    st.plotly_chart(fig_comp_niv, width='stretch')


# ------------------------------------------------------------------------------
# ABA 1: DISPARIDADE ORÇAMENTÁRIA & EQUIDADE
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Análise Comparativa de Recursos e Equidade Interseccional")
    st.markdown("""
    Esta seção cruza os dados da **ODS 5 (Gênero)** e **ODS 18 (Raça/Etnia)** para auditar a distribuição de 
    recursos públicos e identificar déficits estruturais de fomento na pesquisa científica.
    """)

    # Paleta consistente de cores interseccionais para todos os gráficos
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

    # Dados agregados por categoria
    df_grupo = df_filtrado.groupby("categoria_interseccional").agg(
        total_bolsas=("valor_pago", "count"),
        orcamento_total=("valor_pago", "sum"),
        ticket_medio=("valor_pago", "mean")
    ).reset_index()

    # Cálculo dos percentuais de representação
    total_b = df_grupo["total_bolsas"].sum()
    total_o = df_grupo["orcamento_total"].sum()
    df_grupo["pct_bolsas"] = (df_grupo["total_bolsas"] / total_b * 100).round(2)
    df_grupo["pct_orcamento"] = (df_grupo["orcamento_total"] / total_o * 100).round(2)
    df_grupo["gap_pontos"] = (df_grupo["pct_orcamento"] - df_grupo["pct_bolsas"]).round(2)

    # 1. LINHA SUPERIOR: DISTRIBUIÇÃO QUANTITATIVA VS FINANCEIRA
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig_donut = px.pie(
            df_grupo,
            names="categoria_interseccional",
            values="total_bolsas",
            title="Distribuição Percentual de Bolsas (% Bolsistas)",
            hole=0.45,
            color="categoria_interseccional",
            color_discrete_map=CORES_INTERSEC
        )
        fig_donut.update_traces(textinfo="percent+label", textposition="inside")
        fig_donut.update_layout(template="plotly_dark", height=430, showlegend=False)
        st.plotly_chart(fig_donut, width='stretch')

    with col_g2:
        df_ord_orc = df_grupo.sort_values(by="orcamento_total", ascending=True)
        fig_orc = px.bar(
            df_ord_orc,
            x="orcamento_total",
            y="categoria_interseccional",
            orientation="h",
            title="Orçamento Total Alocado por Recorte (R$)",
            labels={"orcamento_total": "Total Aprovado (R$)", "categoria_interseccional": ""},
            color="categoria_interseccional",
            color_discrete_map=CORES_INTERSEC,
            text=df_ord_orc["orcamento_total"].apply(lambda v: f"R$ {v/1e6:.1f}M")
        )
        fig_orc.update_traces(textposition="outside")
        fig_orc.update_layout(
            template="plotly_dark",
            height=430,
            showlegend=False,
            margin=dict(l=180, r=40, t=50, b=40)
        )
        st.plotly_chart(fig_orc, width='stretch')

    # 2. LINHA MÉDIA: O GRÁFICO DO GAP DE EQUIDADE (% BOLSAS VS % RECURSOS)
    st.markdown("### ⚖️ Auditoria do GAP de Equidade: Participação em Bolsas vs. Participação em Verba")
    st.write("""
    Quando a barra de **% Orçamento** fica abaixo da barra de **% Bolsas**, comprova-se que o grupo está 
    concentrado em bolsas de menores valores (níveis iniciais), recebendo menos investimento per capita.
    """)

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
        title="Comparativo de Representatividade: Quantidade de Bolsas (%) vs Recursos Aprovados (%)",
        labels={"categoria_interseccional": "Recorte Interseccional", "Percentual": "Participação (%)"},
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
        legend_title="Métrica Comparada"
    )
    st.plotly_chart(fig_gap, width='stretch')

    # 3. LINHA TEMPORAL & RANKING DE UNIVERSIDADES
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("### 📈 Série Histórica de Investimento (2022 - 2025)")
        # Para a evolução histórica, mantemos os filtros de região, área e nível,
        # garantindo que o gráfico mostre a linha contínua através de todos os anos da base.
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
            title=f"Evolução Anual do Orçamento de Bolsas ({min_ano} - {max_ano})",
            labels={"orcamento": "Orçamento Anual (R$)", "ano": "Ano-Base", "categoria_interseccional": "Grupo"},
            color_discrete_map=CORES_INTERSEC
        )
        fig_temp.update_layout(
            template="plotly_dark",
            height=420,
            xaxis=dict(tickmode="linear", dtick=1)
        )
        st.plotly_chart(fig_temp, width='stretch')

    with col_t2:
        st.markdown("### 🏛️ Top 10 Universidades com Maior Fomento")
        df_ies = df_filtrado.groupby("sigla_ies").agg(
            total_bolsas=("valor_pago", "count"),
            orcamento_total=("valor_pago", "sum")
        ).reset_index().sort_values(by="orcamento_total", ascending=False).head(10)

        fig_ies = px.bar(
            df_ies.sort_values(by="orcamento_total", ascending=True),
            x="orcamento_total",
            y="sigla_ies",
            orientation="h",
            title="Top 10 Instituições por Volume Financeiro (R$)",
            labels={"orcamento_total": "Investimento Aportado (R$)", "sigla_ies": "Instituição (IES)"},
            color="orcamento_total",
            color_continuous_scale="Viridis",
            text=df_ies.sort_values(by="orcamento_total", ascending=True)["orcamento_total"].apply(lambda v: f"R$ {v/1e6:.1f}M")
        )
        fig_ies.update_traces(textposition="outside")
        fig_ies.update_layout(template="plotly_dark", height=420, showlegend=False)
        st.plotly_chart(fig_ies, width='stretch')

# ------------------------------------------------------------------------------
# ABA 2: FUNIL DE CARREIRA CIENTÍFICA (LEAKY PIPELINE)
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Auditoria do Funil de Carreira Científica: Do PIBIC à Produtividade (PQ)")
    st.markdown("""
    O conceito de **Leaky Pipeline** (ou "funil que vaza") descreve a progressiva perda de representatividade 
    de mulheres e pessoas negras à medida que se ascende na hierarquia acadêmica e de pesquisa de ponta.
    """)

    # Ordenação lógica do funil acadêmico
    ordem_carreira = [
        "Iniciação Científica",
        "Mestrado",
        "Doutorado",
        "Pós-Doutorado",
        "Produtividade em Pesquisa"
    ]
    df_funil = df_filtrado[df_filtrado["nivel_bolsa"].isin(ordem_carreira)]

    if not df_funil.empty:
        # Agrupamento proporcional
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
            title="Composição Percentual por Nível da Carreira Acadêmica (100% Empilhado)",
            xaxis_title="Nível da Bolsa / Fomento",
            yaxis_title="Proporção (%)",
            template="plotly_dark",
            height=500,
            legend_title="Grupo Interseccional"
        )
        st.plotly_chart(fig_funil, width='stretch')

        # Diagnóstico crítico
        if "Mulher Negra (Preta/Parda)" in crosstab_funil.columns:
            taxa_ic = crosstab_funil.loc["Iniciação Científica", "Mulher Negra (Preta/Parda)"] if "Iniciação Científica" in crosstab_funil.index else 0
            taxa_pq = crosstab_funil.loc["Produtividade em Pesquisa", "Mulher Negra (Preta/Parda)"] if "Produtividade em Pesquisa" in crosstab_funil.index else 0
            queda = taxa_ic - taxa_pq
            st.info(f"💡 **Evidência do Funil:** Mulheres Negras representam **{taxa_ic:.1f}%** das bolsas na Iniciação Científica, mas caem para apenas **{taxa_pq:.1f}%** nas bolsas de Produtividade em Pesquisa (uma redução de **{queda:.1f} pontos percentuais**).")

# ------------------------------------------------------------------------------
# ABA 3: ASSIMETRIAS REGIONAIS E GRANDES ÁREAS
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("Assimetrias Geográficas e por Áreas do Conhecimento")

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        # Fomento por Região
        df_regiao = df_filtrado.groupby(["regiao", "categoria_interseccional"])["valor_pago"].sum().reset_index()
        fig_regiao = px.bar(
            df_regiao,
            x="regiao",
            y="valor_pago",
            color="categoria_interseccional",
            title="Distribuição do Investimento por Região do Brasil (R$)",
            labels={"valor_pago": "Investimento Total (R$)", "regiao": "Região"},
            barmode="stack"
        )
        fig_regiao.update_layout(template="plotly_dark", height=430)
        st.plotly_chart(fig_regiao, width='stretch')

    with col_m2:
        # Fomento por Grande Área
        df_area = df_filtrado.groupby(["grande_area", "categoria_interseccional"])["valor_pago"].sum().reset_index()
        fig_area = px.bar(
            df_area,
            x="valor_pago",
            y="grande_area",
            color="categoria_interseccional",
            orientation="h",
            title="Investimento por Grande Área do Conhecimento (R$)",
            labels={"valor_pago": "Investimento Total (R$)", "grande_area": "Grande Área"},
            barmode="stack"
        )
        fig_area.update_layout(template="plotly_dark", height=430)
        st.plotly_chart(fig_area, width='stretch')

# ------------------------------------------------------------------------------
# ABA 4: BASE DE DADOS E AUDITORIA
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("Auditoria de Integridade dos Microdados")
    st.write(f"Exibindo amostra dos dados filtrados ({len(df_filtrado):,} linhas).")

    # Tabela com dados
    colunas_exibicao = [
        "ano", "origem_dado", "beneficiario_sexo", "beneficiario_raca_cor",
        "categoria_interseccional", "nivel_bolsa", "grande_area", "uf", "regiao", "valor_pago"
    ]
    st.dataframe(
        df_filtrado[colunas_exibicao].head(100),
        width='stretch',
        hide_index=True
    )

    # Botão de download
    csv_bytes = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Exportar Dados Filtrados (.CSV)",
        data=csv_bytes,
        file_name="auditoria_fomento_interseccional.csv",
        mime="text/csv"
    )

# Rodapé
st.markdown("---")
st.caption("Projeto Prático de Cloud Data Analytics | Aiven Free Tier + Terraform + Streamlit | Desenvolvido pelo Grupo 3.")
