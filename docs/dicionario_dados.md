# Dicionário de Dados - Auditoria de Fomento à Pesquisa Científica
**Grupo 3:** Caio Vinicius, Daniel Oliveira, Maicon Dias, Yuri Sales, Gabriel Luz  
**Fontes Oficiais:** Microdados de Bolsas e Fomento do CNPq & Portal de Dados Abertos da CAPES  
**Alinhamento Estratégico:** ODS 5 (Igualdade de Gênero) e ODS 18 (Igualdade Étnico-Racial)

---

## 1. Tabela Fato: `fato_bolsas_fomento`

Esta tabela armazena os registros higienizados e normalizados das concessões de fomento e bolsas de estudo no Brasil, com foco no cruzamento interseccional.

| Campo | Tipo SQL | Descrição | Valores Possíveis / Exemplo | Fonte Original |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | Identificador único surrogate key da linha | `1`, `2`, `3`... | Pipeline ETL |
| `ano` | `INT` | Ano-base da concessão/pagamento da bolsa | `2019`, `2020`, `2021`, `2022`, `2023` | `ANO_REFERENCIA` / `AN_BASE` |
| `origem_dado` | `VARCHAR(10)` | Órgão governamental financiador | `CNPQ`, `CAPES` | Metadado de Ingestão |
| `beneficiario_sexo` | `VARCHAR(20)` | Sexo/gênero registrado do bolsista | `Feminino`, `Masculino`, `Não informado` | `SEXO_BENEFICIARIO` / `DS_SEXO` |
| `beneficiario_raca_cor` | `VARCHAR(30)` | Autodeclaração de raça/etnia segundo IBGE | `Preta`, `Parda`, `Indígena`, `Branca`, `Amarela`, `Não informada` | `RACA_COR` / `DS_RACA_COR` |
| `categoria_interseccional`| `VARCHAR(50)` | Enriquecimento analítico direto (ODS 5 x ODS 18) | `Mulher Negra (Preta/Parda)`, `Mulher Indígena`, `Mulher Branca`, `Homem Negro (Preto/Pardo)`, etc. | Calculado pelo ETL |
| `modalidade_codigo` | `VARCHAR(40)` | Código oficial do programa/modalidade | `PIBIC`, `PIBITI`, `GM`, `GD`, `PQ-1A`, `PQ-2` | `SIGLA_MODALIDADE` / `DS_MODALIDADE` |
| `nivel_bolsa` | `VARCHAR(60)` | Estágio na trajetória acadêmica e de pesquisa | `Iniciação Científica`, `Mestrado`, `Doutorado`, `Pós-Doutorado`, `Produtividade em Pesquisa` | Padronizado no ETL |
| `grande_area` | `VARCHAR(100)`| Grande área do conhecimento CNPq/CAPES | `Ciências Humanas`, `Ciências Exatas e da Terra`, `Engenharias`, `Ciências Biológicas`, etc. | `NM_GRANDE_AREA` |
| `area_conhecimento` | `VARCHAR(150)`| Subdivisão do conhecimento | `Sociologia`, `Física`, `Ciência da Computação` | `NM_AREA_CONHECIMENTO` |
| `sigla_ies` | `VARCHAR(50)` | Instituição de Ensino Superior de destino | `UFBA`, `USP`, `UFRJ`, `UNB`, `UNICAMP` | `SIGLA_INSTITUICAO` / `SG_IES` |
| `uf` | `VARCHAR(2)` | Unidade da Federação da instituição | `BA`, `SP`, `RJ`, `MG`, `AM`, `RS` | `UF_DESTINO` / `SG_UF_IES` |
| `regiao` | `VARCHAR(20)` | Macrorregião geográfica brasileira | `Nordeste`, `Sudeste`, `Sul`, `Norte`, `Centro-Oeste` | Derivado de `uf` |
| `duracao_meses` | `INT` | Período de vigência da bolsa | `12`, `24`, `36`, `48` | `DURACAO_MESES` |
| `valor_pago` | `NUMERIC(12,2)`| Montante financeiro total repassado em R$ | `8400.00`, `25200.00`, `37200.00` | `VALOR_PAGO` / `VL_BOLSA_ANO` |
| `data_carga` | `TIMESTAMP` | Carimbo de data/hora da ingestão no PostgreSQL | `2026-09-11 19:50:00+00` | Gerado pelo SGBD |

---

## 2. Regras de Transformação e Tratamento de Dados (ETL)

1. **Tratamento de Nulos:**
   - Registros com ausência de sexo foram tipados como `"Não informado"`.
   - Registros sem declaração de raça foram tipados como `"Não informada"`.
   - Valores monetários ausentes ou corrompidos foram convertidos para `0.00` e auditados.
2. **Definição de Mulheres Negras:**
   - Em conformidade com o Estatuto da Igualdade Racial e os critérios metodológicos do IBGE e IPEA, a população negra é a somatória das pessoas que se autodeclaram **pretas** e **pardas**.
3. **Respeito aos Limites da Nuvem (Aiven Free Tier 1GB):**
   - Para garantir que a base persista confortavelmente dentro da cota de 1 GB, o pipeline faz amostragem representativa das séries de dados, gerando tabelas que ocupam entre 20 MB e 80 MB em disco na Aiven.

---

## 3. Catálogo Oficial de Metadados da CAPES (DPB / DDI-BR-CAPES-CONCESSAO-BOLSAS-IES)

Mapeamento de conformidade com o documento oficial [`metadados_concessao_bolsas_ies_2022a2025.pdf`](file:///c:/Users/caiov/Documents/sheila%20av3/metadados_concessao_bolsas_ies_2022a2025.pdf):

| ID | Código da Variável | Nome Oficial / Definição | Tipo | Tratamento / Destino no Modelo |
| :--- | :--- | :--- | :--- | :--- |
| **V131** | `AN_REFERENCIA` | Ano de referência da concessão da bolsa | Numérico | Mapeado diretamente para `ano` |
| **V148** | `NM_MUNICIPIO_IES_CAPES`| Município da Instituição de Ensino Superior | Texto | Utilizado para auditoria municipal |
| **V149** | `SG_UF_IES_CAPES` | Sigla da UF da Instituição de Ensino Superior | Texto | Mapeado para `uf` |
| **V150** | `NM_REGIAO_IES_CAPES` | Região Geográfica da IES | Texto | Mapeado para `regiao` |
| **V135** | `CD_IES_CAPES` | Código da IES no sistema Sucupira | Numérico | Chave técnica de identificação |
| **V159** | `NM_IES_CAPES` | Nome da Instituição de Ensino Superior | Texto | Auditoria institucional |
| **V151** | `SG_IES_CAPES` | Sigla da Instituição de Ensino Superior | Texto | Mapeado para `sigla_ies` |
| **V152** | `NM_NATUREZA_JURIDICA` | Natureza Jurídica (Pública Federal, Estadual, etc.) | Texto | Auditoria setorial |
| **V155** | `SG_PROGRAMA_FOMENTO` | Sigla do Programa de Fomento (ex: DS, PDPG) | Texto | Mapeado para `modalidade_codigo` |
| **V139** | `CD_PROGRAMA` | Código do Programa de Pós-Graduação (PPG) | Numérico | Código único CAPES |
| **V154** | `NM_PROGRAMA` | Nome do Programa de Pós-Graduação | Texto | Auditoria de curso |
| **V161** | `CD_MUNICIPIO_PPG` | Código do município do PPG | Numérico | IBGE Geocódigo |
| **V162** | `NM_MUNICIPIO_PPG` | Nome do município do PPG | Texto | Localização do curso |
| **V163** | `VL_IDHM_MUNICIPIO_PPG`| IDHM do município do PPG | Numérico | Indicador socioeconômico |
| **V164** | `NM_COLEGIO_PPG` | Colégio (Humanidades, Vida, Exatas/Tecnol.) | Texto | Agrupamento de colégios |
| **V165** | `CD_GRANDE_AREA` | Código da grande área do PPG | Numérico | Código numérico oficial |
| **V166** | `CD_AREA_AVALIACAO` | Código da área de avaliação do PPG | Numérico | Área de avaliação CAPES |
| **V167** | `CD_AREA_CONHECIMENTO`| Código da área de conhecimento | Numérico | Subárea CNPq/CAPES |
| **V156** | `NM_GRANDE_AREA` | Grande área do conhecimento do PPG | Texto | Mapeado para `grande_area` |
| **V157** | `NM_AREA_AVALIACAO` | Área de avaliação do PPG | Texto | Auditoria acadêmica |
| **V158** | `NM_AREA_CONHECIMENTO`| Área de conhecimento do PPG | Texto | Mapeado para `area_conhecimento` |
| **V153** | `NM_NIVEL_PADRAO` | Nível da Bolsa (Mestrado, Doutorado, etc.) | Texto | Mapeado para `nivel_bolsa` |
| **V145** | `QT_BOLSAS_CONCEDIDAS` | Total de bolsas concedidas no ano | Numérico | Base para cálculo do volume e valor |
| **V160** | `TP_PROGRAMA` | Tipo do Programa (Institucional, Estratégico) | Texto | Classificação de fomento |

