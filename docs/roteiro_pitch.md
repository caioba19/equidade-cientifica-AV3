# Roteiro do Pitch Técnico de Apresentação (10 Minutos)
**Disciplina:** Computação em Nuvem / Engenharia de Software  
**Grupo 3:** Caio Vinicius, Daniel Oliveira, Maicon Dias, Yuri Sales, Gabriel Luz  
**Tema:** Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa Científica (ODS 5 & ODS 18)

---

## Estrutura da Apresentação (10 Minutos)

### Minuto 00:00 a 02:00 | 1. Introdução Conceitual e Motivação (ODS 5 & ODS 18)
* **Orador:** Caio Vinicius
* **Mensagem-chave:**
  * Apresentar o problema: o Brasil possui mais de 50% de mulheres e negros em sua população, mas como essa diversidade se reflete no financiamento científico de ponta?
  * Conectar a **ODS 5 (Igualdade de Gênero)** e a **ODS 18 (Igualdade Étnico-Racial)** sob a perspectiva da **interseccionalidade**.
  * Mostrar as fontes oficiais utilizadas: Microdados do CNPq (Bolsas e Fomento) e Portal de Dados Abertos da CAPES.
  * Explicar o objetivo: construir uma infraestrutura 100% em nuvem a custo zero que audita o fluxo de recursos públicos para pesquisadoras negras e indígenas.

---

### Minuto 02:00 a 04:00 | 2. Arquitetura em Nuvem & Infraestrutura como Código (Terraform)
* **Orador:** Daniel Oliveira / Maicon Dias
* **O que exibir na tela:** Terminal com `terraform plan` / `main.tf` e o console web da Aiven.
* **Mensagem-chave:**
  * Explicar a arquitetura Serverless/PaaS:
    * Provedor `aiven/aiven` provisionando um cluster gerenciado **Aiven for PostgreSQL** no plano gratuito (`free-1gb`).
    * Destacar as boas práticas de DevOps: variáveis sensíveis (`aiven_api_token`, senhas) segregadas sem exposição no repositório Git (`.gitignore`).
    * Configuração de segurança com SSL obrigatório (`sslmode=require`) e banco analítico dedicado `fomento_db`.

---

### Minuto 04:00 a 06:00 | 3. Engenharia de Dados, Modelagem SQL e Otimização Free Tier
* **Orador:** Yuri Sales / Gabriel Luz
* **O que exibir na tela:** Código do `etl_pipeline.py` e queries no `schema.sql` / `views_analiticas.sql`.
* **Mensagem-chave:**
  * Desafio do Free Tier: O limite de 1 GB de armazenamento e 1 vCPU da Aiven.
  * Como contornamos:
    * Tratamento e normalização dos dados (nulos, padronização de sexo e categorias IBGE).
    * Criação da coluna materializada `categoria_interseccional` e índices B-Tree estratégicos para acelerar consultas analíticas sem onerar a memória.
    * Estratégia de ingestão em lotes (*batch chunks* de 1.000 registros) para estabilidade de rede.

---

### Minuto 06:00 a 09:00 | 4. Demonstração Prática do Dashboard e Descobertas Analíticas
* **Orador:** Caio Vinicius / Equipe
* **O que exibir na tela:** Dashboard funcional em execução no **Render** (Web Service gratuito conectado via SSL ao Aiven PostgreSQL).
* **Demonstração passo a passo:**
  1. **Métricas Chave (KPIs):**
     * Apontar o volume total de recursos analisados.
     * Demonstrar o **GAP Orçamentário**: Mulheres negras recebem proporcionalmente menos verba do que a quantidade de bolsas que detêm.
  2. **O Funil Científico (Leaky Pipeline):**
     * Clicar na aba "O Funil Científico".
     * Mostrar o gráfico empilhado: presença expressiva de mulheres negras e pardas na Iniciação Científica (~28%), com queda brusca na pós-graduação e quase desaparecimento no topo (Bolsas de Produtividade em Pesquisa PQ - menos de 4%).
  3. **Filtros Dinâmicos:**
     * Filtrar por ano (ver evolução temporal) e por Grande Área (ex: comparar Ciências Humanas com Engenharias/Exatas).

---

### Minuto 09:00 a 10:00 | 5. Conclusão e Encerramento
* **Orador:** Caio Vinicius
* **Mensagem-chave:**
  * Resumir os aprendizados: viabilidade de pipelines analíticos robustos em nuvem a custo zero integrando **Aiven** (banco PostgreSQL gerenciado) e **Render** (computação e visualização em Python).
  * Impacto social: dados como ferramenta para políticas públicas ativas de equidade científica.
  * Agradecer à banca e abrir para perguntas.
