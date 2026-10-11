"""
Gerador de Dados Amostrais Fidedignos - CNPq & CAPES (ODS 5 & ODS 18)
Grupo 3: Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa Científica

Este script gera uma amostra estratificada e realista simulando o fomento à pesquisa
no Brasil (2019 a 2023), refletindo os padrões documentados na literatura científica sobre
o "Leaky Pipeline" e a sub-representação de pesquisadoras negras e indígenas.
"""

import csv
import os
import random

def gerar_amostra(num_registros=12000, output_path="etl/dados_amostra_fomento.csv"):
    random.seed(42)  # Reprodutibilidade científica

    anos = [2019, 2020, 2021, 2022, 2023]
    origens = ["CNPQ", "CAPES"]

    # Áreas de conhecimento oficiais da tabela CAPES/CNPq
    grandes_areas = {
        "Ciências Humanas": ["Sociologia", "História", "Educação", "Filosofia"],
        "Ciências Sociais Aplicadas": ["Direito", "Administração", "Economia", "Comunicação"],
        "Ciências Exatas e da Terra": ["Física", "Matemática", "Química", "Ciência da Computação"],
        "Engenharias": ["Engenharia Civil", "Engenharia Elétrica", "Engenharia Mecânica", "Engenharia de Produção"],
        "Ciências Biológicas": ["Genética", "Ecologia", "Bioquímica", "Zoologia"],
        "Ciências da Saúde": ["Medicina", "Enfermagem", "Saúde Coletiva", "Farmácia"],
        "Ciências Agrárias": ["Agronomia", "Medicina Veterinária", "Zootecnia"],
        "Lingüística, Letras e Artes": ["Letras", "Artes Visuais", "Música"]
    }

    niveis = [
        ("Iniciação Científica", ["PIBIC", "PIBITI", "IC-Junior"], 700.0, 12),
        ("Mestrado", ["GM", "Bolsa Demanda Social - Mestrado"], 2100.0, 24),
        ("Doutorado", ["GD", "Bolsa Demanda Social - Doutorado"], 3100.0, 48),
        ("Pós-Doutorado", ["Bolsa Recém-Doutor", "Fixação de Doutores"], 5200.0, 12),
        ("Produtividade em Pesquisa", ["PQ-1A", "PQ-1B", "PQ-1C", "PQ-2", "PQ-Senior"], 3500.0, 36)
    ]

    # Distribuição por estado e região
    estados_regiao = [
        ("BA", "Nordeste", "UFBA"),
        ("PE", "Nordeste", "UFPE"),
        ("CE", "Nordeste", "UFC"),
        ("SP", "Sudeste", "USP"),
        ("SP", "Sudeste", "UNICAMP"),
        ("RJ", "Sudeste", "UFRJ"),
        ("MG", "Sudeste", "UFMG"),
        ("RS", "Sul", "UFRGS"),
        ("PR", "Sul", "UFPR"),
        ("SC", "Sul", "UFSC"),
        ("DF", "Centro-Oeste", "UNB"),
        ("GO", "Centro-Oeste", "UFG"),
        ("AM", "Norte", "UFAM"),
        ("PA", "Norte", "UFPA")
    ]

    cabecalho = [
        "ano",
        "origem_dado",
        "beneficiario_sexo",
        "beneficiario_raca_cor",
        "modalidade_codigo",
        "nivel_bolsa",
        "grande_area",
        "area_conhecimento",
        "sigla_ies",
        "uf",
        "regiao",
        "duracao_meses",
        "valor_pago"
    ]

    registros = []

    for _ in range(num_registros):
        ano = random.choice(anos)
        origem = random.choice(origens)
        uf, regiao, ies = random.choice(estados_regiao)

        # Escolhe nível com distribuição típica da pós-graduação e fomento
        # IC (40%), Mestrado (25%), Doutorado (20%), Pós-Doc (8%), PQ (7%)
        peso_niveis = [0.40, 0.25, 0.20, 0.08, 0.07]
        nivel_info = random.choices(niveis, weights=peso_niveis, k=1)[0]
        nivel_nome, modalidades, valor_mensal, duracao = nivel_info
        modalidade = random.choice(modalidades)

        grande_area = random.choice(list(grandes_areas.keys()))
        area_conhecimento = random.choice(grandes_areas[grande_area])

        # Simulação sociológica realística:
        # Na Iniciação Científica a presença de mulheres pretas/pardas é maior (cerca de 28%),
        # mas diminui progressivamente até a Produtividade em Pesquisa (PQ - menos de 4%),
        # fenômeno amplamente documentado como "funil de vidro / leaky pipeline".
        if nivel_nome == "Iniciação Científica":
            perfis = [
                ("Feminino", "Preta", 0.12),
                ("Feminino", "Parda", 0.18),
                ("Feminino", "Indígena", 0.02),
                ("Feminino", "Branca", 0.23),
                ("Feminino", "Amarela", 0.01),
                ("Masculino", "Preta", 0.09),
                ("Masculino", "Parda", 0.15),
                ("Masculino", "Indígena", 0.01),
                ("Masculino", "Branca", 0.17),
                ("Masculino", "Amarela", 0.01),
                ("Não informado", "Não informada", 0.01)
            ]
        elif nivel_nome in ["Mestrado", "Doutorado"]:
            perfis = [
                ("Feminino", "Preta", 0.08),
                ("Feminino", "Parda", 0.14),
                ("Feminino", "Indígena", 0.01),
                ("Feminino", "Branca", 0.29),
                ("Feminino", "Amarela", 0.01),
                ("Masculino", "Preta", 0.06),
                ("Masculino", "Parda", 0.13),
                ("Masculino", "Indígena", 0.005),
                ("Masculino", "Branca", 0.26),
                ("Masculino", "Amarela", 0.01),
                ("Não informado", "Não informada", 0.005)
            ]
        elif nivel_nome == "Pós-Doutorado":
            perfis = [
                ("Feminino", "Preta", 0.04),
                ("Feminino", "Parda", 0.09),
                ("Feminino", "Indígena", 0.003),
                ("Feminino", "Branca", 0.35),
                ("Feminino", "Amarela", 0.01),
                ("Masculino", "Preta", 0.04),
                ("Masculino", "Parda", 0.10),
                ("Masculino", "Indígena", 0.002),
                ("Masculino", "Branca", 0.35),
                ("Masculino", "Amarela", 0.01),
                ("Não informado", "Não informada", 0.005)
            ]
        else:  # Produtividade em Pesquisa (PQ)
            perfis = [
                ("Feminino", "Preta", 0.015),
                ("Feminino", "Parda", 0.04),
                ("Feminino", "Indígena", 0.001),
                ("Feminino", "Branca", 0.29),
                ("Feminino", "Amarela", 0.01),
                ("Masculino", "Preta", 0.02),
                ("Masculino", "Parda", 0.06),
                ("Masculino", "Indígena", 0.001),
                ("Masculino", "Branca", 0.55),
                ("Masculino", "Amarela", 0.01),
                ("Não informado", "Não informada", 0.003)
            ]

        sexos, racas, pesos = zip(*[((p[0]), p[1], p[2]) for p in perfis])
        # Normaliza pesos
        total_p = sum(pesos)
        pesos_norm = [p / total_p for p in pesos]
        escolha_idx = random.choices(range(len(perfis)), weights=pesos_norm, k=1)[0]
        sexo = sexos[escolha_idx]
        raca_cor = racas[escolha_idx]

        # Ajuste por ano (aumento ligeiro pós-2022 devido ao reajuste das bolsas federais)
        fator_reajuste = 1.35 if ano >= 2023 else 1.0
        # Duração anual proporcional para o ano-base
        meses_no_ano = 12
        valor_total = round(valor_mensal * fator_reajuste * meses_no_ano, 2)

        # Adiciona pequena variação aleatória de taxa de bancada / fomento adicional
        if "Produtividade" in nivel_nome:
            valor_total += random.choice([0.0, 12000.0, 24000.0])

        registros.append([
            ano,
            origem,
            sexo,
            raca_cor,
            modalidade,
            nivel_nome,
            grande_area,
            area_conhecimento,
            ies,
            uf,
            regiao,
            duracao,
            valor_total
        ])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cabecalho)
        writer.writerows(registros)

    print(f"[OK] Gerados {len(registros)} registros fidedignos em '{output_path}'.")

if __name__ == "__main__":
    gerar_amostra()
