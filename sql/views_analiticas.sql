-- ==============================================================================
-- PROJETO PRÁTICO: CLOUD DATA ANALYTICS (ODS 5 & ODS 18)
-- GRUPO 3: VIEWS ANALÍTICAS PARA O DASHBOARD (STREAMLIT)
-- ==============================================================================

-- 1. Visão de Resumo Interseccional por Ano e Grupo (ODS 5 x ODS 18)
DROP VIEW IF EXISTS vw_resumo_interseccional;
CREATE VIEW vw_resumo_interseccional AS
SELECT
    ano,
    origem_dado,
    categoria_interseccional,
    beneficiario_sexo,
    beneficiario_raca_cor,
    COUNT(*) AS total_bolsas,
    SUM(valor_pago) AS valor_total_investido,
    ROUND(AVG(valor_pago), 2) AS ticket_medio_bolsa,
    ROUND((COUNT(*)::DECIMAL / SUM(COUNT(*)) OVER (PARTITION BY ano)) * 100, 2) AS percentual_participacao_ano
FROM fato_bolsas_fomento
GROUP BY ano, origem_dado, categoria_interseccional, beneficiario_sexo, beneficiario_raca_cor;

-- 2. Visão do Funil de Carreira Acadêmica (Leaky Pipeline)
DROP VIEW IF EXISTS vw_funil_carreira_academica;
CREATE VIEW vw_funil_carreira_academica AS
SELECT
    nivel_bolsa,
    CASE 
        WHEN nivel_bolsa ILIKE '%Iniciação%' THEN 1
        WHEN nivel_bolsa ILIKE '%Mestrado%' THEN 2
        WHEN nivel_bolsa ILIKE '%Doutorado%' THEN 3
        WHEN nivel_bolsa ILIKE '%Pós-Doutorado%' THEN 4
        WHEN nivel_bolsa ILIKE '%Produtividade%' THEN 5
        ELSE 6
    END AS ordem_funil,
    categoria_interseccional,
    beneficiario_sexo,
    beneficiario_raca_cor,
    COUNT(*) AS total_bolsas,
    SUM(valor_pago) AS valor_total,
    ROUND(AVG(valor_pago), 2) AS valor_medio
FROM fato_bolsas_fomento
GROUP BY nivel_bolsa, ordem_funil, categoria_interseccional, beneficiario_sexo, beneficiario_raca_cor;

-- 3. Visão de Disparidade Regional e Grandes Áreas
DROP VIEW IF EXISTS vw_distribuicao_regional_areas;
CREATE VIEW vw_distribuicao_regional_areas AS
SELECT
    regiao,
    uf,
    grande_area,
    categoria_interseccional,
    COUNT(*) AS total_bolsas,
    SUM(valor_pago) AS valor_total
FROM fato_bolsas_fomento
GROUP BY regiao, uf, grande_area, categoria_interseccional;

-- 4. Visão de Indicadores Macro (KPIs de Alto Nível para Cards)
DROP VIEW IF EXISTS vw_kpis_macro;
CREATE VIEW vw_kpis_macro AS
SELECT
    ano,
    COUNT(*) AS total_geral_bolsas,
    SUM(valor_pago) AS orcamento_geral_investido,
    COUNT(*) FILTER (WHERE categoria_interseccional IN ('Mulher Negra (Preta/Parda)', 'Mulher Indígena')) AS bolsas_mulheres_negras_indigenas,
    SUM(valor_pago) FILTER (WHERE categoria_interseccional IN ('Mulher Negra (Preta/Parda)', 'Mulher Indígena')) AS orcamento_mulheres_negras_indigenas,
    ROUND(
        (COUNT(*) FILTER (WHERE categoria_interseccional IN ('Mulher Negra (Preta/Parda)', 'Mulher Indígena'))::DECIMAL / NULLIF(COUNT(*), 0)) * 100, 
        2
    ) AS pct_bolsas_mulheres_negras_indigenas,
    ROUND(
        (SUM(valor_pago) FILTER (WHERE categoria_interseccional IN ('Mulher Negra (Preta/Parda)', 'Mulher Indígena'))::DECIMAL / NULLIF(SUM(valor_pago), 0)) * 100, 
        2
    ) AS pct_orcamento_mulheres_negras_indigenas
FROM fato_bolsas_fomento
GROUP BY ano;
