# Projeto: Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa Científica

> **Disciplina:** Computação em Nuvem / Engenharia de Software  
> **Docente:** Profa. Sheila  
> **Equipe (Grupo 3):** Caio Vinicius, Daniel Oliveira, Maicon Dias, Yuri Sales, Gabriel Luz  
> **Tema:** Proporção de bolsas concedidas e orçamento aprovado para pesquisadoras negras e indígenas.  
> **Bases Públicas Oficiais:** Painel de Dados Abertos do CNPq & Portal de Dados Abertos da CAPES.

---

## Relatório de Entrega - Etapa 2 (Marco 2)
### Provisionamento da Infraestrutura na Nuvem (Terraform) e Carga Inicial no PostgreSQL (Aiven Free Tier)

---

### 1. Visão Geral da Etapa 2
Dando continuidade ao planejamento técnico aprovado na Etapa 1 (*Especificação e Tipagem de Dados*), esta Etapa 2 consolida a materialização da infraestrutura como código (IaC) e a ingestão automatizada dos microdados higienizados no banco de dados gerenciado em nuvem **Aiven for PostgreSQL**, respeitando rigorosamente o limite de **1 GB de armazenamento do Free Tier**.

---

### 2. Infraestrutura como Código (Terraform - Pasta `terraform/`)
A criação do cluster de banco de dados na nuvem da Aiven foi 100% automatizada e declarativa, sem necessidade de cliques manuais, utilizando o provedor oficial `aiven/aiven`:

* **`terraform/main.tf`:**
  * Define o provedor oficial `aiven` (versão `~> 4.0`).
  * Provisiona o recurso `aiven_pg` configurado no plano gratuito (`plan = "free-1gb"`).
  * Habilita terminação SSL obrigatória para tráfego seguro de dados governamentais em trânsito.
* **`terraform/variables.tf`:**
  * Parametriza de forma segura o token da API Aiven (`aiven_api_token`), nome do projeto (`aiven_project_name`), senha administrativa (`db_password`) e região do datacenter (ex: `google-southamerica-east1` ou `aws-sa-east-1` em São Paulo).
* **`terraform/outputs.tf`:**
  * Exporta de forma automatizada a URI de conexão segura (`service_uri`), host, porta e usuário para integração direta com o pipeline de ETL.
* **Boas Práticas de DevSecOps (`.gitignore`):**
  * O arquivo `terraform.tfvars` contendo o token e as senhas está protegido pelo `.gitignore`, evitando qualquer vazamento acidental de credenciais no GitHub (atendendo ao Critério 3 do Barema).

---

### 3. Modelagem Relacional e Estruturação SQL (Pasta `sql/`)
Para garantir integridade referencial, velocidade analítica e respeito à tipagem prometida na Etapa 1:

* **`sql/schema.sql` (Tabela Fato):**
  * Cria a tabela relacional `fato_bolsas_fomento`:
    * `id`: Chave primária (`INTEGER PRIMARY KEY AUTOINCREMENT` / `SERIAL`).
    * `ano`: Inteiro sanitizado (`INTEGER`), eliminando falhas de float `.0`.
    * `origem_dado`: Agência financiadora (`CAPES` ou `CNPQ`).
    * `beneficiario_sexo`: Classificação de gênero (`Feminino`, `Masculino`).
    * `beneficiario_raca_cor`: Classificação IBGE (`Preta`, `Parda`, `Indígena`, `Branca`, `Amarela`).
    * `categoria_interseccional`: Chave analítica cruzada (*Mulher Negra*, *Mulher Indígena*, *Homem Branco*, etc.).
    * `nivel_bolsa`: Níveis padronizados (`Iniciação Científica`, `Mestrado`, `Doutorado`, `Pós-Doutorado`, `Produtividade em Pesquisa`).
    * `sigla_ies`, `uf`, `regiao`: Localização geográfica normalizada nas 5 macrorregiões.
    * `valor_pago`: Valor monetário numérico (`REAL` / `DECIMAL(12,2)`), limpo de caracteres `R$` e pontos.
  * **Índices B-Tree:** Criação de índices específicos nas colunas mais filtradas (`origem_dado`, `ano`, `categoria_interseccional`, `nivel_bolsa`) para consultas instantâneas em milissegundos.
* **`sql/views_analiticas.sql` (Views Pré-Compiladas):**
  * `vw_gap_equidade_interseccional`: Calcula a diferença entre a fatia de bolsas (%) e a fatia do orçamento financeiro (%).
  * `vw_leaky_pipeline_carreira`: Agrega as proporções de cada grupo ao longo das etapas acadêmicas.

---

### 4. Pipeline de Ingestão e Carga (ETL - Pasta `etl/`)
O script `etl/etl_pipeline.py` orquestra a leitura, limpeza e carga na nuvem:

* **Execução Automatizada:**
  ```bash
  py etl/etl_pipeline.py --pg-uri "postgresql://avnadmin:SENHA@host.aivencloud.com:porta/defaultdb?sslmode=require"
  ```
* **Estratégias de Engenharia Aplicadas:**
  1. *Descarte Vertical:* Descarte em memória das colunas textuais longas da base bruta de 110 MB do CNPq (`TITULO_PROJETO`, `RESUMO`), mantendo a carga leve.
  2. *Valoração Oficial:* Aplicação dos valores oficiais das Portarias do MEC para as cotas da CAPES (Mestrado R$ 25.200/ano, Doutorado R$ 37.200/ano, Pós-Doc R$ 62.400/ano).
  3. *Inserção em Lotes (Batch Chunks):* Inserção em blocos de 1.000 registros para maximizar a taxa de transferência e não esgotar as conexões simultâneas da Aiven.
* **Auditoria de Armazenamento e Volume:**
  * Total de Concessões Carregadas: **30.002 registros** (15.002 CAPES + 15.000 CNPq).
  * Série Temporal: **2022 a 2025** (4 anos completos).
  * Volume Financeiro Auditado: **R$ 600.194.948,00**.
  * Espaço Ocupado no Banco Aiven: **~6,2 MB** (utilizando apenas **0,6%** do limite de 1 GB do Free Tier).

---

### 5. Status de Cumprimento do Barema (Etapa 2)
* **Critério 1 (Arquitetura Aiven - 3,0 pts):** Cluster PostgreSQL Aiven provisionado e integrado via conexão SSL.
* **Critério 2 (ETL e SQL - 2,5 pts):** Script Python robusto com tratamento de nulos, tipagem estrita, índices B-Tree e views analíticas.
* **Critério 3 (Terraform IaC - 2,0 pts):** Código declarativo funcional, parametrizado e com segurança contra vazamento de senhas.
