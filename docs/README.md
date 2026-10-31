# Documentação do projeto

Esta pasta reúne materiais de apoio para entender, apresentar e revisar o projeto. Os arquivos daqui documentam o sistema; eles não executam o pipeline nem alimentam o dashboard.

## Arquivos

- [`dicionario_dados.md`](dicionario_dados.md): descreve os campos da tabela analítica, seus significados e regras de tratamento. Consulte junto com o ETL e as fontes originais. Se uma regra documentada divergir do código, confirme qual versão está correta e atualize a documentação.
- [`entrega_etapa2.md`](entrega_etapa2.md): registra o material da entrega da segunda etapa do projeto e seu contexto.
- [`roteiro_pitch.md`](roteiro_pitch.md): organiza a apresentação oral, com tópicos, sequência e demonstração planejada. É um roteiro, então os resultados e afirmações devem ser conferidos com os dados atuais antes da apresentação.

## Como as partes se relacionam

1. Os arquivos de dados de origem ficam na raiz do repositório.
2. O pipeline que lê e transforma esses dados fica em [`../etl/etl_pipeline.py`](../etl/etl_pipeline.py).
3. Os arquivos tratados são armazenados na pasta `etl` e podem ser consultados pelo dashboard em [`../app/app.py`](../app/app.py).
4. Este diretório explica campos, decisões e apresentação; não substitui a conferência do código e dos dados.

## Cuidado ao descrever os resultados

Ao revisar o ETL, o grupo deve distinguir os campos observados nas fontes oficiais dos campos inferidos, estimados ou sorteados pelo código. O dicionário e o roteiro precisam refletir o comportamento real do pipeline. Não descreva valores sintéticos como autodeclarações ou informações confirmadas de beneficiários, e valide percentuais e conclusões antes de apresentá-los.

## Sugestão de revisão antes da entrega

- Confirmar se as descrições do dicionário correspondem ao código e às colunas das fontes.
- Conferir se o roteiro usa resultados reproduzíveis da versão atual dos dados.
- Informar as fontes, o período, os critérios de seleção e as limitações da análise.
- Padronizar nomes do grupo, caminhos e demais informações que aparecem nos documentos.
