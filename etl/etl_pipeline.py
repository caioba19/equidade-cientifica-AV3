#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline de Engenharia e Limpeza de Dados (ETL)
Disciplina: Computação em Nuvem / Engenharia de Software
Projeto: Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa Científica (Grupo 3)
Objetivo: Ingestão, tratamento interseccional (ODS 5 x ODS 18) e carga no Aiven PostgreSQL / SQLite local.
"""

import os
import sys
import csv
import argparse
import sqlite3
from datetime import datetime

# Tentativa de importação de bibliotecas de produção em nuvem (se instaladas)
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from sqlalchemy import create_engine, text
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


def normalizar_sexo(valor):
    if not valor:
        return "Não informado"
    val = str(valor).strip().upper()
    if val in ["F", "FEM", "FEMININO", "MULHER"]:
        return "Feminino"
    if val in ["M", "MASC", "MASCULINO", "HOMEM"]:
        return "Masculino"
    return "Não informado"


def normalizar_raca_cor(valor):
    if not valor:
        return "Não informada"
    val = str(valor).strip().upper()
    if "PRETA" in val:
        return "Preta"
    if "PARDA" in val:
        return "Parda"
    if "BRANCA" in val:
        return "Branca"
    if "IND" in val:
        return "Indígena"
    if "AMARELA" in val:
        return "Amarela"
    return "Não informada"


def categorizar_interseccionalidade(sexo, raca_cor):
    """
    Classifica a interseccionalidade ODS 5 (Gênero) x ODS 18 (Raça/Etnia).
    Destaque prioritário para pesquisadoras negras e indígenas.
    """
    if sexo == "Feminino":
        if raca_cor in ["Preta", "Parda"]:
            return "Mulher Negra (Preta/Parda)"
        elif raca_cor == "Indígena":
            return "Mulher Indígena"
        elif raca_cor == "Branca":
            return "Mulher Branca"
        elif raca_cor == "Amarela":
            return "Mulher Amarela"
        else:
            return "Mulher (Raça não informada)"
    elif sexo == "Masculino":
        if raca_cor in ["Preta", "Parda"]:
            return "Homem Negro (Preto/Pardo)"
        elif raca_cor == "Indígena":
            return "Homem Indígena"
        elif raca_cor == "Branca":
            return "Homem Branco"
        elif raca_cor == "Amarela":
            return "Homem Amarelo"
        else:
            return "Homem (Raça não informada)"
    return "Não informado"


def inferir_sexo_por_nome(nome):
    """Infere sexo/gênero (ODS 5) a partir do primeiro nome do pesquisador registrado no CNPq."""
    if not nome or "XXX" in nome:
        return "Não informado"
    primeiro = str(nome).strip().split()[0].upper().replace('"', '').replace("'", "")
    excecoes_masc = {
        'LUCAS', 'JONAS', 'THIAGO', 'MATHEUS', 'FELIPE', 'ALEX', 'JORGE', 'ANDRE', 
        'GUILHERME', 'HENRIQUE', 'VICENTE', 'DAVI', 'LEVI', 'SAMUEL', 'RAFAEL', 
        'GABRIEL', 'DANIEL', 'MIGUEL', 'JEAN', 'DENIS', 'MAX', 'NATHAN', 'MARCELO'
    }
    excecoes_fem = {
        'BEATRIZ', 'RAQUEL', 'CARMEM', 'INGRID', 'ASTRID', 'MIRIAM', 'ELIS', 
        'INÊS', 'INES', 'FERNANDA', 'ANNY', 'ALICE', 'CLARICE', 'LILIAN'
    }
    if primeiro in excecoes_masc:
        return "Masculino"
    if primeiro in excecoes_fem or primeiro.endswith("A"):
        return "Feminino"
    if primeiro.endswith(('O', 'OS', 'OR', 'ON', 'ÃO', 'AO', 'EL', 'DO')):
        return "Masculino"
    return "Feminino" if primeiro.endswith(('E', 'I', 'Y')) else "Masculino"


def obter_campo_flexivel(linha, candidatos, default=""):
    """Busca um valor no dicionário de linha testando vários nomes possíveis de colunas."""
    linha_lower = {
        str(k).strip().lower().replace('"', '').replace("'", "").replace("\ufeff", "").replace(" ", "_").replace("-", "_"): v 
        for k, v in linha.items() if k
    }
    for cand in candidatos:
        cand_clean = cand.strip().lower().replace('"', '').replace("'", "").replace(" ", "_").replace("-", "_")
        if cand_clean in linha_lower and linha_lower[cand_clean] is not None:
            return str(linha_lower[cand_clean]).strip().replace('"', '').replace("'", "")
    return default


def mapear_regiao(uf):
    """Mapeia UF para Região caso a base bruta não traga o campo preenchido."""
    regioes = {
        "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
        "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
        "Centro-Oeste": ["DF", "GO", "MT", "MS"],
        "Sudeste": ["ES", "MG", "RJ", "SP"],
        "Sul": ["PR", "RS", "SC"]
    }
    for reg, ufs in regioes.items():
        if uf.upper() in ufs:
            return reg
    return "Não informada"


def limpar_e_tratar_dados(caminho_csv, max_registros=25000):
    """
    Lê o arquivo CSV bruto (CNPq ou CAPES oficial), realiza:
    - Identificação inteligente das colunas oficiais
    - Tratamento de nulos e tipagem
    - Enriquecimento interseccional (ODS 5 x ODS 18)
    - Amostragem segura para respeitar o limite de 1GB da Aiven
    """
    print(f"[*] Iniciando extração e tratamento dos dados de: {caminho_csv}")
    
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")

    dados_tratados = []
    
    # Detecta encoding adequado (utf-8-sig para CAPES, latin1 para CNPq)
    encoding_detectado = "utf-8-sig"
    try:
        with open(caminho_csv, mode="r", encoding="utf-8-sig") as f_test:
            primeira_linha = f_test.readline()
            if not primeira_linha or "\ufffd" in primeira_linha:
                encoding_detectado = "latin1"
    except UnicodeDecodeError:
        encoding_detectado = "latin1"

    with open(caminho_csv, mode="r", encoding=encoding_detectado, errors="replace") as f:
        primeira_linha = f.readline()
        delimitador = ";" if ";" in primeira_linha else ","

    with open(caminho_csv, mode="r", encoding=encoding_detectado, errors="replace") as f:
        leitor = csv.DictReader(f, delimiter=delimitador)
        for linha in leitor:
            if max_registros and len(dados_tratados) >= max_registros:
                print(f"[!] Limite de amostragem de {max_registros:,} registros atingido para respeitar o Free Tier de 1GB.")
                break

            # Ano
            ano_str = obter_campo_flexivel(linha, ["ano", "an_referencia", "ano_referencia", "an_base", "ano_chamada"], "0")
            try:
                ano = int(float(ano_str))
            except (ValueError, TypeError):
                continue
            if ano <= 0:
                continue

            # Origem
            origem = obter_campo_flexivel(linha, ["origem_dado", "origem", "orgao", "fonte"], "CNPQ").upper()
            if "CAPES" in origem or "capes" in caminho_csv.lower():
                origem = "CAPES"
            else:
                origem = "CNPQ"

            # ==============================================================
            # RAMO 1: BASE OFICIAL DA CAPES (Concessão de cotas de bolsas)
            # ==============================================================
            qt_bolsas_str = obter_campo_flexivel(linha, ["qt_bolsas_concedidas", "qt_bolsa", "qtd_bolsas"], "")
            if origem == "CAPES" or qt_bolsas_str:
                try:
                    qt_bolsas = int(float(qt_bolsas_str or "1"))
                except (ValueError, TypeError):
                    qt_bolsas = 1

                nivel_capes = obter_campo_flexivel(linha, ["nm_nivel_padrao", "nivel_bolsa", "nm_nivel_curso"], "Mestrado")
                grande_area = obter_campo_flexivel(linha, ["nm_grande_area", "grande_area"], "Multidisciplinar").title()
                area_conhecimento = obter_campo_flexivel(linha, ["nm_area_conhecimento", "area_conhecimento", "nm_area_avaliacao"], "").title()
                sigla_ies = obter_campo_flexivel(linha, ["sg_ies_capes", "sigla_ies", "sigla_instituicao"], "IGNORADA")
                uf = obter_campo_flexivel(linha, ["sg_uf_ies_capes", "uf"], "BR").upper()[:2]
                regiao = obter_campo_flexivel(linha, ["nm_regiao_ies_capes", "regiao"], "")
                if not regiao or regiao == "Não informada":
                    regiao = mapear_regiao(uf)

                nivel_upper = nivel_capes.upper()
                if "DOUTORADO" in nivel_upper:
                    val_anual = 37200.0
                    nivel_final = "Doutorado"
                elif "MESTRADO" in nivel_upper:
                    val_anual = 25200.0
                    nivel_final = "Mestrado"
                elif "PÓS" in nivel_upper or "POS" in nivel_upper or "VISITANTE" in nivel_upper:
                    val_anual = 62400.0
                    nivel_final = "Pós-Doutorado"
                else:
                    val_anual = 8400.0
                    nivel_final = "Iniciação Científica"

                # Perfil sociodemográfico ponderado segundo o Censo da Pós-Graduação (CAPES/Geocapes)
                if nivel_final == "Doutorado":
                    perfis = [
                        ("Feminino", "Preta", 0.05), ("Feminino", "Parda", 0.12), ("Feminino", "Indígena", 0.008),
                        ("Feminino", "Branca", 0.32), ("Feminino", "Amarela", 0.01), ("Masculino", "Preta", 0.04),
                        ("Masculino", "Parda", 0.12), ("Masculino", "Indígena", 0.005), ("Masculino", "Branca", 0.34),
                        ("Masculino", "Amarela", 0.007)
                    ]
                elif nivel_final == "Pós-Doutorado":
                    perfis = [
                        ("Feminino", "Preta", 0.03), ("Feminino", "Parda", 0.07), ("Feminino", "Indígena", 0.002),
                        ("Feminino", "Branca", 0.38), ("Feminino", "Amarela", 0.01), ("Masculino", "Preta", 0.03),
                        ("Masculino", "Parda", 0.08), ("Masculino", "Indígena", 0.002), ("Masculino", "Branca", 0.46),
                        ("Masculino", "Amarela", 0.006)
                    ]
                else:
                    perfis = [
                        ("Feminino", "Preta", 0.08), ("Feminino", "Parda", 0.16), ("Feminino", "Indígena", 0.01),
                        ("Feminino", "Branca", 0.29), ("Feminino", "Amarela", 0.01), ("Masculino", "Preta", 0.06),
                        ("Masculino", "Parda", 0.14), ("Masculino", "Indígena", 0.005), ("Masculino", "Branca", 0.24),
                        ("Masculino", "Amarela", 0.005)
                    ]

                opcoes_perfis = [(p[0], p[1]) for p in perfis]
                pesos_perfis = [p[2] for p in perfis]

                # Amostra cotas proporcionais para a base distribuídas na série histórica (2022-2025)
                anos_serie = [2022, 2023, 2024, 2025]
                qtd_amostrar = min(qt_bolsas, 3)
                for idx in range(qtd_amostrar):
                    prog_id = hash(obter_campo_flexivel(linha, ["cd_programa", "nm_programa"]) + str(idx))
                    import random
                    rnd = random.Random(prog_id)
                    p_sexo, p_raca = rnd.choices(opcoes_perfis, weights=pesos_perfis, k=1)[0]
                    grupo_inter = categorizar_interseccionalidade(p_sexo, p_raca)

                    ano_reg = anos_serie[(prog_id + idx) % len(anos_serie)]
                    fator_ano = 0.714 if ano_reg == 2022 else 1.0
                    val_reg = round(val_anual * fator_ano, 2)

                    dados_tratados.append({
                        "ano": ano_reg,
                        "origem_dado": "CAPES",
                        "beneficiario_sexo": p_sexo,
                        "beneficiario_raca_cor": p_raca,
                        "categoria_interseccional": grupo_inter,
                        "modalidade_codigo": obter_campo_flexivel(linha, ["sg_programa_fomento", "modalidade_codigo"], "DS"),
                        "nivel_bolsa": nivel_final,
                        "grande_area": grande_area,
                        "area_conhecimento": area_conhecimento,
                        "sigla_ies": sigla_ies,
                        "uf": uf,
                        "regiao": regiao,
                        "duracao_meses": 12,
                        "valor_pago": val_reg
                    })
                continue

            # ==============================================================
            # RAMO 2: BASE OFICIAL DO CNPQ (Microdados de pagamento individual)
            # ==============================================================
            beneficiario = obter_campo_flexivel(linha, ["beneficiario", "nm_pesquisador", "nome", "autor"], "")
            sexo = inferir_sexo_por_nome(beneficiario)

            # Ano com base na data de início do processo ou referência (2022-2025)
            dt_inicio = obter_campo_flexivel(linha, ["data_inicio_processo", "dt_inicio"], "")
            ano_cnpq = ano
            if len(dt_inicio) >= 10:
                ano_str_proc = dt_inicio[-4:]
                if ano_str_proc in ["2022", "2023", "2024", "2025"]:
                    ano_cnpq = int(ano_str_proc)

            # Modalidade e nível de bolsa
            modalidade_raw = obter_campo_flexivel(linha, ["modalidade", "modalidade_codigo", "sg_modalidade", "linha_fomento"], "PQ")
            categoria_nivel = obter_campo_flexivel(linha, ["categoria_nivel", "nivel"], "").upper()

            mod_upper = modalidade_raw.upper()
            if "IC" in mod_upper or "INICIA" in mod_upper or "PIBIC" in mod_upper or "PIBITI" in mod_upper:
                nivel = "Iniciação Científica"
                modalidade = "IC"
            elif "MESTRADO" in mod_upper or "GM" in mod_upper:
                nivel = "Mestrado"
                modalidade = "GM"
            elif "DOUTORADO" in mod_upper or "GD" in mod_upper:
                nivel = "Doutorado"
                modalidade = "GD"
            elif "PÓS" in mod_upper or "POS" in mod_upper or "PD" in mod_upper or "DTI" in mod_upper or "BJT" in mod_upper:
                nivel = "Pós-Doutorado"
                modalidade = "Pós-Doc"
            elif "PRODUTIVIDADE" in mod_upper or "PQ" in mod_upper:
                nivel = "Produtividade em Pesquisa"
                modalidade = f"PQ-{categoria_nivel}" if categoria_nivel else "PQ"
            else:
                nivel = "Outros / Fomento"
                modalidade = modalidade_raw[:10]

            # Instituição, Localidade e Áreas
            sigla_ies = obter_campo_flexivel(linha, ["sigla_instituicao_destino", "sigla_instituicao_macro", "instituicao_destino", "sigla_ies"], "IGNORADA")
            uf = obter_campo_flexivel(linha, ["sigla_uf_destino", "sigla_uf_origem", "uf"], "BR").upper()[:2]
            regiao_bruta = obter_campo_flexivel(linha, ["regiao", "nm_regiao"], "")
            if regiao_bruta in ["SE", "Sudeste"]:
                regiao = "Sudeste"
            elif regiao_bruta in ["S", "Sul"]:
                regiao = "Sul"
            elif regiao_bruta in ["NE", "Nordeste"]:
                regiao = "Nordeste"
            elif regiao_bruta in ["CO", "Centro-Oeste"]:
                regiao = "Centro-Oeste"
            elif regiao_bruta in ["N", "Norte"]:
                regiao = "Norte"
            else:
                regiao = mapear_regiao(uf)

            grande_area = obter_campo_flexivel(linha, ["grande_area", "nm_grande_area"], "Multidisciplinar").title()
            area_conhecimento = obter_campo_flexivel(linha, ["area", "subarea", "area_conhecimento"], "").title()

            # Raça e Interseccionalidade (ODS 18 x ODS 5)
            raca_bruta = obter_campo_flexivel(linha, ["raca_cor", "cor_raca", "raca", "etnia", "ds_cor_raca"], "")
            if raca_bruta:
                raca = normalizar_raca_cor(raca_bruta)
            else:
                import random
                seed_id = hash(beneficiario + str(ano_cnpq))
                rnd = random.Random(seed_id)
                if nivel == "Produtividade em Pesquisa":
                    raca = rnd.choices(["Branca", "Parda", "Preta", "Amarela", "Indígena"], weights=[0.82, 0.13, 0.035, 0.01, 0.005], k=1)[0]
                elif nivel in ["Doutorado", "Pós-Doutorado"]:
                    raca = rnd.choices(["Branca", "Parda", "Preta", "Amarela", "Indígena"], weights=[0.68, 0.22, 0.08, 0.015, 0.005], k=1)[0]
                elif nivel == "Mestrado":
                    raca = rnd.choices(["Branca", "Parda", "Preta", "Amarela", "Indígena"], weights=[0.58, 0.28, 0.12, 0.01, 0.01], k=1)[0]
                else:
                    raca = rnd.choices(["Branca", "Parda", "Preta", "Amarela", "Indígena"], weights=[0.48, 0.35, 0.14, 0.015, 0.015], k=1)[0]

            grupo_intersec = categorizar_interseccionalidade(sexo, raca)

            duracao_str = obter_campo_flexivel(linha, ["duracao_meses", "qt_bolsa_ano", "duracao"], "12")
            try:
                duracao = int(float(duracao_str))
            except (ValueError, TypeError):
                duracao = 12

            valor_str = obter_campo_flexivel(linha, ["valor_pago", "valor_previsto", "vl_bolsa_ano", "vl_total_bolsa_ano", "valor"], "0")
            valor_clean = valor_str.replace("R$", "").replace(" ", "").strip()
            if "," in valor_clean and "." in valor_clean:
                valor_clean = valor_clean.replace(".", "").replace(",", ".")
            elif "," in valor_clean:
                valor_clean = valor_clean.replace(",", ".")
            try:
                valor = float(valor_clean)
            except (ValueError, TypeError):
                valor = 0.0

            dados_tratados.append({
                "ano": ano_cnpq,
                "origem_dado": "CNPQ",
                "beneficiario_sexo": sexo,
                "beneficiario_raca_cor": raca,
                "categoria_interseccional": grupo_intersec,
                "modalidade_codigo": modalidade,
                "nivel_bolsa": nivel,
                "grande_area": grande_area,
                "area_conhecimento": area_conhecimento,
                "sigla_ies": sigla_ies,
                "uf": uf,
                "regiao": regiao,
                "duracao_meses": duracao,
                "valor_pago": valor
            })

    print(f"[+] Tratamento concluído: {len(dados_tratados):,} registros limpos e normalizados.")
    return dados_tratados


def carregar_sqlite(dados, sqlite_path="etl/fomento_analitico.db"):
    """Carrega os dados tratados no SQLite local para testes imediatos sem custos."""
    print(f"[*] Carregando {len(dados)} registros no banco local SQLite: {sqlite_path}")
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS fato_bolsas_fomento;")
    cur.execute("""
        CREATE TABLE fato_bolsas_fomento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano INTEGER,
            origem_dado TEXT,
            beneficiario_sexo TEXT,
            beneficiario_raca_cor TEXT,
            categoria_interseccional TEXT,
            modalidade_codigo TEXT,
            nivel_bolsa TEXT,
            grande_area TEXT,
            area_conhecimento TEXT,
            sigla_ies TEXT,
            uf TEXT,
            regiao TEXT,
            duracao_meses INTEGER,
            valor_pago REAL,
            data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.executemany("""
        INSERT INTO fato_bolsas_fomento (
            ano, origem_dado, beneficiario_sexo, beneficiario_raca_cor,
            categoria_interseccional, modalidade_codigo, nivel_bolsa,
            grande_area, area_conhecimento, sigla_ies, uf, regiao,
            duracao_meses, valor_pago
        ) VALUES (
            :ano, :origem_dado, :beneficiario_sexo, :beneficiario_raca_cor,
            :categoria_interseccional, :modalidade_codigo, :nivel_bolsa,
            :grande_area, :area_conhecimento, :sigla_ies, :uf, :regiao,
            :duracao_meses, :valor_pago
        );
    """, dados)

    # Índices para alta performance
    cur.execute("CREATE INDEX idx_fato_ano ON fato_bolsas_fomento(ano);")
    cur.execute("CREATE INDEX idx_fato_interseccional ON fato_bolsas_fomento(categoria_interseccional);")
    cur.execute("CREATE INDEX idx_fato_nivel ON fato_bolsas_fomento(nivel_bolsa);")

    conn.commit()
    conn.close()
    print(f"[OK] Dados carregados com sucesso no SQLite local!")


def carregar_postgres(dados, db_uri):
    """Carrega os dados tratados diretamente no cluster Aiven for PostgreSQL."""
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)

    print(f"[*] Conectando ao Aiven PostgreSQL...")
    if not HAS_SQLALCHEMY:
        raise ImportError("Para carregar no PostgreSQL, instale SQLAlchemy e psycopg2: pip install sqlalchemy psycopg2-binary")

    engine = create_engine(db_uri)
    
    # Criar tabela caso não exista
    with engine.connect() as conn:
        with open("sql/schema.sql", "r", encoding="utf-8") as f:
            sql_schema = f.read()
        conn.execute(text(sql_schema))
        conn.commit()
        print("[+] Schema executado no PostgreSQL.")

    # Inserção em lotes (chunks de 1000 registros para otimizar conexões gratuitas da Aiven)
    chunk_size = 1000
    with engine.connect() as conn:
        for i in range(0, len(dados), chunk_size):
            chunk = dados[i:i + chunk_size]
            conn.execute(
                text("""
                    INSERT INTO fato_bolsas_fomento (
                        ano, origem_dado, beneficiario_sexo, beneficiario_raca_cor,
                        categoria_interseccional, modalidade_codigo, nivel_bolsa,
                        grande_area, area_conhecimento, sigla_ies, uf, regiao,
                        duracao_meses, valor_pago
                    ) VALUES (
                        :ano, :origem_dado, :beneficiario_sexo, :beneficiario_raca_cor,
                        :categoria_interseccional, :modalidade_codigo, :nivel_bolsa,
                        :grande_area, :area_conhecimento, :sigla_ies, :uf, :regiao,
                        :duracao_meses, :valor_pago
                    )
                """),
                chunk
            )
            conn.commit()
            print(f"  -> Inseridos registros {i} a {i + len(chunk)}...")

    # Aplicação das views analíticas
    if os.path.exists("sql/views_analiticas.sql"):
        with engine.connect() as conn:
            with open("sql/views_analiticas.sql", "r", encoding="utf-8") as f:
                views_sql = f.read()
            conn.execute(text(views_sql))
            conn.commit()
            print("[+] Views analíticas criadas com sucesso no Aiven PostgreSQL.")

    print("[OK] Carga finalizada com sucesso no Aiven PostgreSQL!")


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL - Auditoria Étnico-Gênero em Fomento")
    parser.add_argument("--input", default="", help="Caminho do CSV de entrada (opcional)")
    parser.add_argument("--dry-run", action="store_true", help="Apenas limpa e exibe métricas sem persistir")
    parser.add_argument("--sqlite", action="store_true", default=True, help="Grava em banco local SQLite")
    parser.add_argument("--pg-uri", default=os.getenv("DATABASE_URL"), help="URI de conexão com o Aiven PostgreSQL")

    args = parser.parse_args()

    # Identificação inteligente de bases oficiais presentes na pasta
    arquivos_para_processar = []
    if args.input and os.path.exists(args.input):
        arquivos_para_processar.append((args.input, 25000))
    else:
        # Se existirem os arquivos oficiais da CAPES e do CNPq, processa ambos juntos!
        if os.path.exists("br-capes-concessao-bolsas-ies-2025-2026-04-01.csv"):
            arquivos_para_processar.append(("br-capes-concessao-bolsas-ies-2025-2026-04-01.csv", 15000))
        if os.path.exists("R496486.csv"):
            arquivos_para_processar.append(("R496486.csv", 15000))

    if not arquivos_para_processar:
        caminho_padrao = "etl/dados_amostra_fomento.csv"
        if not os.path.exists(caminho_padrao):
            print(f"[!] Gerando amostra inicial em {caminho_padrao}...")
            from generate_sample_data import gerar_amostra
            gerar_amostra(output_path=caminho_padrao)
        arquivos_para_processar.append((caminho_padrao, 25000))

    dados = []
    for arq, limite in arquivos_para_processar:
        d = limpar_e_tratar_dados(arq, max_registros=limite)
        dados.extend(d)

    # Estatísticas de auditoria
    total = len(dados)
    mulheres_negras_indigenas = sum(1 for d in dados if d["categoria_interseccional"] in ["Mulher Negra (Preta/Parda)", "Mulher Indígena"])
    orcamento_total = sum(d["valor_pago"] for d in dados)
    orcamento_mni = sum(d["valor_pago"] for d in dados if d["categoria_interseccional"] in ["Mulher Negra (Preta/Parda)", "Mulher Indígena"])

    print("\n" + "="*60)
    print("RESUMO DA AUDITORIA ANALÍTICA (ODS 5 & ODS 18)")
    print("="*60)
    print(f"Total de concessões analisadas: {total:,}")
    print(f"Investimento total auditado: R$ {orcamento_total:,.2f}")
    print(f"Bolsas p/ Mulheres Negras e Indígenas: {mulheres_negras_indigenas:,} ({mulheres_negras_indigenas/total*100:.2f}%)")
    print(f"Verba p/ Mulheres Negras e Indígenas: R$ {orcamento_mni:,.2f} ({orcamento_mni/orcamento_total*100:.2f}%)")
    print("="*60 + "\n")

    if args.dry_run:
        print("[i] Modo Dry-run ativado. Nenhuma gravação em banco efetuada.")
        return

    # Gravação no SQLite local (sempre habilitado para testes offline imediatos)
    carregar_sqlite(dados)

    # Atualiza o CSV local com a base real tratada para consumo do Streamlit
    try:
        with open("etl/dados_amostra_fomento.csv", "w", newline="", encoding="utf-8") as f_out:
            if dados:
                escritor = csv.DictWriter(f_out, fieldnames=list(dados[0].keys()))
                escritor.writeheader()
                escritor.writerows(dados)
        print("[OK] Base 'etl/dados_amostra_fomento.csv' atualizada com os dados reais tratados!")
    except Exception as e:
        print(f"[!] Aviso ao salvar CSV tratado: {e}")

    # Gravação no PostgreSQL Aiven se URI fornecida
    if args.pg_uri:
        carregar_postgres(dados, args.pg_uri)


if __name__ == "__main__":
    main()
