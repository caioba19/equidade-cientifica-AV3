-- ==============================================================================
-- PROJETO PRÁTICO: CLOUD DATA ANALYTICS (ODS 5 & ODS 18)
-- GRUPO 3: Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa Científica
-- BANCO DE DADOS: PostgreSQL (Aiven Free Tier - Limite 1GB)
-- ==============================================================================

-- Criação da tabela fato otimizada para consultas analíticas e armazenamento eficiente
DROP TABLE IF EXISTS fato_bolsas_fomento CASCADE;

CREATE TABLE fato_bolsas_fomento (
    id SERIAL PRIMARY KEY,
    ano INT NOT NULL,
    origem_dado VARCHAR(10) NOT NULL CHECK (origem_dado IN ('CNPQ', 'CAPES')),
    beneficiario_sexo VARCHAR(20) NOT NULL,
    beneficiario_raca_cor VARCHAR(30) NOT NULL,
    categoria_interseccional VARCHAR(50) NOT NULL, -- Ex: 'Mulher Negra', 'Mulher Indígena', 'Mulher Branca', 'Homem Negro', etc.
    modalidade_codigo VARCHAR(40),                 -- Ex: PIBIC, PIBITI, GM, GD, PQ-1A, PQ-2
    nivel_bolsa VARCHAR(60) NOT NULL,              -- Iniciação Científica, Mestrado, Doutorado, Pós-Doutorado, Produtividade em Pesquisa
    grande_area VARCHAR(100) NOT NULL,             -- Ex: Ciências Humanas, Ciências Exatas e da Terra, Engenharias
    area_conhecimento VARCHAR(150),
    sigla_ies VARCHAR(50),                         -- Ex: UFBA, USP, UFRJ, UNB, UNICAMP
    uf VARCHAR(2) NOT NULL,                        -- Ex: BA, SP, RJ, MG
    regiao VARCHAR(20) NOT NULL,                   -- Nordeste, Sudeste, Sul, Norte, Centro-Oeste
    duracao_meses INT DEFAULT 12,
    valor_pago NUMERIC(12, 2) NOT NULL,            -- Valor financeiro aportado em R$
    data_carga TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Comentários para documentação do dicionário no próprio banco
COMMENT ON TABLE fato_bolsas_fomento IS 'Tabela consolidada de concessão de bolsas e fomento à pesquisa do CNPq e CAPES com recorte interseccional de gênero e raça.';
COMMENT ON COLUMN fato_bolsas_fomento.beneficiario_sexo IS 'Classificação de sexo/gênero da pessoa bolsista/pesquisadora (Feminino, Masculino, Não informado).';
COMMENT ON COLUMN fato_bolsas_fomento.beneficiario_raca_cor IS 'Autodeclaração étnico-racial segundo categorias do IBGE (Preta, Parda, Indígena, Branca, Amarela, Não informada).';
COMMENT ON COLUMN fato_bolsas_fomento.categoria_interseccional IS 'Cruzamento interseccional direto (ODS 5 x ODS 18) para aceleração de filtros e agregações.';
COMMENT ON COLUMN fato_bolsas_fomento.nivel_bolsa IS 'Posição no funil de formação/carreira acadêmica.';
COMMENT ON COLUMN fato_bolsas_fomento.valor_pago IS 'Orçamento aprovado e executado em Reais (R$).';

-- Índices estratégicos para performance em instâncias com recursos modestos (1 vCPU / 1GB RAM)
CREATE INDEX idx_fato_ano ON fato_bolsas_fomento(ano);
CREATE INDEX idx_fato_interseccional ON fato_bolsas_fomento(categoria_interseccional);
CREATE INDEX idx_fato_sexo_raca ON fato_bolsas_fomento(beneficiario_sexo, beneficiario_raca_cor);
CREATE INDEX idx_fato_nivel ON fato_bolsas_fomento(nivel_bolsa);
CREATE INDEX idx_fato_area ON fato_bolsas_fomento(grande_area);
CREATE INDEX idx_fato_regiao_uf ON fato_bolsas_fomento(regiao, uf);
