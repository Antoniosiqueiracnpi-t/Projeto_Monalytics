// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["BLAU3"] = {
  "ticker": "BLAU3",
  "ticker_preco": "BLAU3",
  "padrao_fiscal": {
    "tipo": "PADRAO",
    "descricao": "Ano fiscal padrão (jan-dez) com T1-T4",
    "trimestres_ltm": 4
  },
  "metadata": {
    "VALOR_MERCADO": {
      "nome": "Valor de Mercado",
      "categoria": "Valuation",
      "formula": "Preço × Ações (3+4)",
      "unidade": "R$ mil",
      "usa_preco": true
    },
    "P_L": {
      "nome": "P/L",
      "categoria": "Valuation",
      "formula": "Preço / Lucro por Ação LTM",
      "unidade": "x",
      "usa_preco": true
    },
    "P_VPA": {
      "nome": "P/VPA",
      "categoria": "Valuation",
      "formula": "Preço / Valor Patrimonial por Ação",
      "unidade": "x",
      "usa_preco": true
    },
    "EV_EBITDA": {
      "nome": "EV/EBITDA",
      "categoria": "Valuation",
      "formula": "Enterprise Value / EBITDA LTM",
      "unidade": "x",
      "usa_preco": true
    },
    "EV_EBIT": {
      "nome": "EV/EBIT",
      "categoria": "Valuation",
      "formula": "Enterprise Value / EBIT LTM",
      "unidade": "x",
      "usa_preco": true
    },
    "EV_RECEITA": {
      "nome": "EV/Receita",
      "categoria": "Valuation",
      "formula": "Enterprise Value / Receita LTM",
      "unidade": "x",
      "usa_preco": true
    },
    "DY": {
      "nome": "Dividend Yield",
      "categoria": "Valuation",
      "formula": "Dividendos LTM / Market Cap",
      "unidade": "%",
      "usa_preco": true
    },
    "PAYOUT": {
      "nome": "Payout",
      "categoria": "Valuation",
      "formula": "Dividendos LTM / Lucro Líquido LTM",
      "unidade": "%",
      "usa_preco": false
    },
    "ROE": {
      "nome": "ROE",
      "categoria": "Rentabilidade",
      "formula": "Lucro Líquido LTM / PL Médio",
      "unidade": "%",
      "usa_preco": false
    },
    "ROA": {
      "nome": "ROA",
      "categoria": "Rentabilidade",
      "formula": "Lucro Líquido LTM / Ativo Total Médio",
      "unidade": "%",
      "usa_preco": false
    },
    "ROIC": {
      "nome": "ROIC",
      "categoria": "Rentabilidade",
      "formula": "NOPAT / Capital Investido",
      "unidade": "%",
      "usa_preco": false
    },
    "MARGEM_EBITDA": {
      "nome": "Margem EBITDA",
      "categoria": "Rentabilidade",
      "formula": "EBITDA / Receita",
      "unidade": "%",
      "usa_preco": false
    },
    "MARGEM_LIQUIDA": {
      "nome": "Margem Líquida",
      "categoria": "Rentabilidade",
      "formula": "Lucro Líquido / Receita",
      "unidade": "%",
      "usa_preco": false
    },
    "DIV_LIQ_EBITDA": {
      "nome": "Dív.Líq/EBITDA",
      "categoria": "Endividamento",
      "formula": "(Emp CP + LP - Caixa) / EBITDA",
      "unidade": "x",
      "usa_preco": false
    },
    "DIV_LIQ_PL": {
      "nome": "Dív.Líq/PL",
      "categoria": "Endividamento",
      "formula": "Dívida Líquida / Patrimônio Líquido",
      "unidade": "x",
      "usa_preco": false
    },
    "ICJ": {
      "nome": "ICJ",
      "categoria": "Endividamento",
      "formula": "EBIT / Despesas Financeiras",
      "unidade": "x",
      "usa_preco": false
    },
    "COMPOSICAO_DIVIDA": {
      "nome": "Composição Dívida",
      "categoria": "Endividamento",
      "formula": "Emp CP / (Emp CP + LP)",
      "unidade": "%",
      "usa_preco": false
    },
    "LIQ_CORRENTE": {
      "nome": "Liquidez Corrente",
      "categoria": "Liquidez",
      "formula": "Ativo Circulante / Passivo Circulante",
      "unidade": "x",
      "usa_preco": false
    },
    "LIQ_SECA": {
      "nome": "Liquidez Seca",
      "categoria": "Liquidez",
      "formula": "(AC - Estoques) / PC",
      "unidade": "x",
      "usa_preco": false
    },
    "LIQ_GERAL": {
      "nome": "Liquidez Geral",
      "categoria": "Liquidez",
      "formula": "(AC + RLP) / (PC + PNC)",
      "unidade": "x",
      "usa_preco": false
    },
    "GIRO_ATIVO": {
      "nome": "Giro do Ativo",
      "categoria": "Eficiência",
      "formula": "Receita LTM / Ativo Total",
      "unidade": "x",
      "usa_preco": false
    },
    "CICLO_CAIXA": {
      "nome": "Ciclo de Caixa",
      "categoria": "Eficiência",
      "formula": "PMR + PME - PMP",
      "unidade": "dias",
      "usa_preco": false
    },
    "PME": {
      "nome": "PME",
      "categoria": "Eficiência",
      "formula": "(Estoques + AtBio) × 360 / CPV",
      "unidade": "dias",
      "usa_preco": false
    },
    "NCG_RECEITA": {
      "nome": "NCG/Receita",
      "categoria": "Eficiência",
      "formula": "NCG / Receita LTM",
      "unidade": "%",
      "usa_preco": false
    }
  },
  "historico_anual": {
    "2017": {
      "periodo_referencia": "2017T4",
      "multiplos": {
        "VALOR_MERCADO": 1320160.0,
        "P_L": 12.8012,
        "P_VPA": 9.5431,
        "EV_EBITDA": 8.5856,
        "EV_EBIT": 8.5856,
        "EV_RECEITA": 2.2843,
        "DY": 10.3002,
        "PAYOUT": 131.8553,
        "ROE": 74.5489,
        "ROA": 28.1708,
        "ROIC": 47.3462,
        "MARGEM_EBITDA": 26.6058,
        "MARGEM_LIQUIDA": 16.6966,
        "DIV_LIQ_EBITDA": 0.5522,
        "DIV_LIQ_PL": 0.656,
        "ICJ": 9.988,
        "COMPOSICAO_DIVIDA": 99.0974,
        "LIQ_CORRENTE": 1.1092,
        "LIQ_SECA": 0.573,
        "LIQ_GERAL": 1.129,
        "GIRO_ATIVO": 1.6872,
        "PME": 127.1226,
        "CICLO_CAIXA": 106.8273,
        "NCG_RECEITA": 18.4672
      }
    },
    "2018": {
      "periodo_referencia": "2018T4",
      "multiplos": {
        "VALOR_MERCADO": 1320160.0,
        "P_L": 10.711,
        "P_VPA": 5.9111,
        "EV_EBITDA": 7.0553,
        "EV_EBIT": 7.0553,
        "EV_RECEITA": 1.8313,
        "DY": 10.3002,
        "PAYOUT": 110.3257,
        "ROE": 68.1577,
        "ROA": 25.6714,
        "ROIC": 39.9355,
        "MARGEM_EBITDA": 25.9559,
        "MARGEM_LIQUIDA": 15.7579,
        "DIV_LIQ_EBITDA": 0.5526,
        "DIV_LIQ_PL": 0.5023,
        "ICJ": 6.5836,
        "COMPOSICAO_DIVIDA": 14.4018,
        "LIQ_CORRENTE": 2.4763,
        "LIQ_SECA": 1.6397,
        "LIQ_GERAL": 1.2122,
        "GIRO_ATIVO": 1.3164,
        "PME": 117.7244,
        "CICLO_CAIXA": 122.9586,
        "NCG_RECEITA": 22.4563
      }
    },
    "2019": {
      "periodo_referencia": "2019T4",
      "multiplos": {
        "VALOR_MERCADO": 1320160.0,
        "P_L": 6.593,
        "P_VPA": 4.9676,
        "EV_EBITDA": 4.7766,
        "EV_EBIT": 4.7766,
        "EV_RECEITA": 1.4732,
        "DY": 10.3002,
        "PAYOUT": 67.9091,
        "ROE": 81.8819,
        "ROA": 30.0523,
        "ROIC": 51.5994,
        "MARGEM_EBITDA": 30.8415,
        "MARGEM_LIQUIDA": 20.4847,
        "DIV_LIQ_EBITDA": 0.3976,
        "DIV_LIQ_PL": 0.451,
        "ICJ": 13.1914,
        "COMPOSICAO_DIVIDA": 26.827,
        "LIQ_CORRENTE": 1.9086,
        "LIQ_SECA": 1.1943,
        "LIQ_GERAL": 1.1064,
        "GIRO_ATIVO": 1.3237,
        "PME": 123.3497,
        "CICLO_CAIXA": 119.1554,
        "NCG_RECEITA": 15.79
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 1320160.0,
        "P_L": 5.1907,
        "P_VPA": 5.9643,
        "EV_EBITDA": 4.6149,
        "EV_EBIT": 4.6149,
        "EV_RECEITA": 1.5196,
        "DY": 10.3002,
        "PAYOUT": 53.4659,
        "ROE": 104.4264,
        "ROA": 25.293,
        "ROIC": 36.8471,
        "MARGEM_EBITDA": 32.9269,
        "MARGEM_LIQUIDA": 21.5205,
        "DIV_LIQ_EBITDA": 1.2224,
        "DIV_LIQ_PL": 2.149,
        "ICJ": 8.9099,
        "COMPOSICAO_DIVIDA": 9.174,
        "LIQ_CORRENTE": 2.2002,
        "LIQ_SECA": 1.3001,
        "LIQ_GERAL": 0.8046,
        "GIRO_ATIVO": 0.9286,
        "PME": 188.3837,
        "CICLO_CAIXA": 187.2875,
        "NCG_RECEITA": 24.1681
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 4274957.57,
        "P_L": 13.1999,
        "P_VPA": 2.6148,
        "EV_EBITDA": 8.1613,
        "EV_EBIT": 8.1613,
        "EV_RECEITA": 2.7273,
        "DY": 3.8556,
        "PAYOUT": 50.8929,
        "ROE": 34.8949,
        "ROA": 17.9891,
        "ROIC": 27.7358,
        "MARGEM_EBITDA": 33.4179,
        "MARGEM_LIQUIDA": 23.7019,
        "DIV_LIQ_EBITDA": -1.2008,
        "DIV_LIQ_PL": -0.3354,
        "ICJ": 14.7293,
        "COMPOSICAO_DIVIDA": 25.0087,
        "LIQ_CORRENTE": 4.9459,
        "LIQ_SECA": 3.7306,
        "LIQ_GERAL": 2.5053,
        "GIRO_ATIVO": 0.5869,
        "PME": 214.2342,
        "CICLO_CAIXA": 241.8113,
        "NCG_RECEITA": 38.3713
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 3186036.36,
        "P_L": 8.838,
        "P_VPA": 1.7526,
        "EV_EBITDA": 6.3117,
        "EV_EBIT": 6.3117,
        "EV_RECEITA": 2.0286,
        "DY": 5.1733,
        "PAYOUT": 45.7219,
        "ROE": 20.881,
        "ROA": 14.9362,
        "ROIC": 20.0838,
        "MARGEM_EBITDA": 32.1407,
        "MARGEM_LIQUIDA": 25.623,
        "DIV_LIQ_EBITDA": -0.7341,
        "DIV_LIQ_PL": -0.1826,
        "ICJ": 8.2898,
        "COMPOSICAO_DIVIDA": 26.8006,
        "LIQ_CORRENTE": 4.5212,
        "LIQ_SECA": 2.9879,
        "LIQ_GERAL": 2.5066,
        "GIRO_ATIVO": 0.563,
        "PME": 277.185,
        "CICLO_CAIXA": 305.0989,
        "NCG_RECEITA": 53.0697
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 2025357.57,
        "P_L": 8.1836,
        "P_VPA": 1.0151,
        "EV_EBITDA": 6.7586,
        "EV_EBIT": 6.7586,
        "EV_RECEITA": 1.6221,
        "DY": 8.138,
        "PAYOUT": 66.5979,
        "ROE": 12.9808,
        "ROA": 8.9145,
        "ROIC": 9.8992,
        "MARGEM_EBITDA": 24.0008,
        "MARGEM_LIQUIDA": 18.0304,
        "DIV_LIQ_EBITDA": 0.6108,
        "DIV_LIQ_PL": 0.1009,
        "ICJ": 6.446,
        "COMPOSICAO_DIVIDA": 12.3276,
        "LIQ_CORRENTE": 4.6256,
        "LIQ_SECA": 2.7542,
        "LIQ_GERAL": 1.846,
        "GIRO_ATIVO": 0.4495,
        "PME": 256.4797,
        "CICLO_CAIXA": 302.031,
        "NCG_RECEITA": 64.5218
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1677333.33,
        "P_L": 7.8554,
        "P_VPA": 0.7799,
        "EV_EBITDA": 5.3024,
        "EV_EBIT": 5.3024,
        "EV_RECEITA": 0.9938,
        "DY": 9.8265,
        "PAYOUT": 77.1919,
        "ROE": 10.3005,
        "ROA": 6.6053,
        "ROIC": 9.7894,
        "MARGEM_EBITDA": 18.7415,
        "MARGEM_LIQUIDA": 12.171,
        "DIV_LIQ_EBITDA": 0.201,
        "DIV_LIQ_PL": 0.0307,
        "ICJ": 3.924,
        "COMPOSICAO_DIVIDA": 13.1247,
        "LIQ_CORRENTE": 3.1159,
        "LIQ_SECA": 1.989,
        "LIQ_GERAL": 1.6484,
        "GIRO_ATIVO": 0.5142,
        "PME": 199.1811,
        "CICLO_CAIXA": 203.0374,
        "NCG_RECEITA": 40.9661
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 1820848.48,
        "P_L": 5.7546,
        "P_VPA": 0.7799,
        "EV_EBITDA": 5.0339,
        "EV_EBIT": 5.0339,
        "EV_RECEITA": 1.1618,
        "DY": 9.052,
        "PAYOUT": 52.0909,
        "ROE": 14.3192,
        "ROA": 9.2215,
        "ROIC": 10.4883,
        "MARGEM_EBITDA": 23.0789,
        "MARGEM_LIQUIDA": 17.8863,
        "DIV_LIQ_EBITDA": 0.5741,
        "DIV_LIQ_PL": 0.1004,
        "ICJ": 3.7264,
        "COMPOSICAO_DIVIDA": 42.3571,
        "LIQ_CORRENTE": 2.8976,
        "LIQ_SECA": 1.8522,
        "LIQ_GERAL": 1.6158,
        "GIRO_ATIVO": 0.4885,
        "PME": 241.871,
        "CICLO_CAIXA": 256.6324,
        "NCG_RECEITA": 68.382
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T21:22:27.639536",
    "preco_utilizado": 8.92,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 179393939,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 1600193.94,
      "P_L": 5.0572,
      "P_VPA": 0.6854,
      "EV_EBITDA": 4.4935,
      "EV_EBIT": 4.4935,
      "EV_RECEITA": 1.037,
      "DY": 10.3002,
      "PAYOUT": 52.0909,
      "ROE": 14.3192,
      "ROA": 9.2215,
      "ROIC": 10.4883,
      "MARGEM_EBITDA": 23.0789,
      "MARGEM_LIQUIDA": 17.8863,
      "DIV_LIQ_EBITDA": 0.5741,
      "DIV_LIQ_PL": 0.1004,
      "ICJ": 3.7264,
      "COMPOSICAO_DIVIDA": 42.3571,
      "LIQ_CORRENTE": 2.8976,
      "LIQ_SECA": 1.8522,
      "LIQ_GERAL": 1.6158,
      "GIRO_ATIVO": 0.4885,
      "PME": 241.871,
      "CICLO_CAIXA": 256.6324,
      "NCG_RECEITA": 68.382
    }
  },
  "periodos_disponiveis": [
    "2017T1",
    "2017T2",
    "2017T3",
    "2017T4",
    "2018T1",
    "2018T2",
    "2018T3",
    "2018T4",
    "2019T1",
    "2019T2",
    "2019T3",
    "2019T4",
    "2020T1",
    "2020T2",
    "2020T3",
    "2020T4",
    "2021T1",
    "2021T2",
    "2021T3",
    "2021T4",
    "2022T1",
    "2022T2",
    "2022T3",
    "2022T4",
    "2023T1",
    "2023T2",
    "2023T3",
    "2023T4",
    "2024T1",
    "2024T2",
    "2024T3",
    "2024T4",
    "2025T1",
    "2025T2",
    "2025T3"
  ],
  "erros": []
};
})();
