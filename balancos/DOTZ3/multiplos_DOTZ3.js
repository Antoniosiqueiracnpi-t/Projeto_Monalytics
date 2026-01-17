// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["DOTZ3"] = {
  "ticker": "DOTZ3",
  "ticker_preco": "DOTZ3",
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
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 528811.97,
        "P_L": -8.2322,
        "P_VPA": -1.4381,
        "EV_EBITDA": -199.2391,
        "EV_EBIT": -33.1662,
        "EV_RECEITA": 4.9251,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 17.4692,
        "ROA": -32.1561,
        "ROIC": 3.11,
        "MARGEM_EBITDA": -2.4719,
        "MARGEM_LIQUIDA": -57.868,
        "DIV_LIQ_EBITDA": -6.5233,
        "DIV_LIQ_PL": -0.0487,
        "ICJ": -0.3317,
        "COMPOSICAO_DIVIDA": 39.6109,
        "LIQ_CORRENTE": 0.4293,
        "LIQ_SECA": 0.4293,
        "LIQ_GERAL": 0.2569,
        "GIRO_ATIVO": 0.5557,
        "PME": 0.0,
        "CICLO_CAIXA": -919.9771,
        "NCG_RECEITA": -226.2824
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 3507960.59,
        "P_L": -42.6489,
        "P_VPA": -45.1028,
        "EV_EBITDA": -56.1312,
        "EV_EBIT": -44.2698,
        "EV_RECEITA": 26.2974,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 36.9263,
        "ROA": -27.1293,
        "ROIC": 14.31,
        "MARGEM_EBITDA": -46.8499,
        "MARGEM_LIQUIDA": -66.6073,
        "DIV_LIQ_EBITDA": 4.5035,
        "DIV_LIQ_PL": 3.3499,
        "ICJ": -2.8858,
        "COMPOSICAO_DIVIDA": 60.4709,
        "LIQ_CORRENTE": 1.0224,
        "LIQ_SECA": 1.0224,
        "LIQ_GERAL": 0.7072,
        "GIRO_ATIVO": 0.3037,
        "PME": 0.0,
        "CICLO_CAIXA": -1181.4255,
        "NCG_RECEITA": -215.6922
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 1703681.74,
        "P_L": -17.8968,
        "P_VPA": -10.0553,
        "EV_EBITDA": -19.6486,
        "EV_EBIT": -15.3047,
        "EV_RECEITA": 11.5314,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 77.0161,
        "ROA": -23.7776,
        "ROIC": 25.7199,
        "MARGEM_EBITDA": -58.6884,
        "MARGEM_LIQUIDA": -68.431,
        "DIV_LIQ_EBITDA": 1.2191,
        "DIV_LIQ_PL": 0.5875,
        "ICJ": -3.8664,
        "COMPOSICAO_DIVIDA": 57.1891,
        "LIQ_CORRENTE": 0.6931,
        "LIQ_SECA": 0.6931,
        "LIQ_GERAL": 0.4596,
        "GIRO_ATIVO": 0.353,
        "PME": 0.0,
        "CICLO_CAIXA": -1095.1691,
        "NCG_RECEITA": -183.2501
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 104628.03,
        "P_L": -1.7293,
        "P_VPA": -0.455,
        "EV_EBITDA": -3.7601,
        "EV_EBIT": -1.8869,
        "EV_RECEITA": 0.796,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 30.2996,
        "ROA": -17.8892,
        "ROIC": 17.2197,
        "MARGEM_EBITDA": -21.1689,
        "MARGEM_LIQUIDA": -43.6338,
        "DIV_LIQ_EBITDA": -0.1956,
        "DIV_LIQ_PL": -0.025,
        "ICJ": -1.7401,
        "COMPOSICAO_DIVIDA": 80.3666,
        "LIQ_CORRENTE": 0.4162,
        "LIQ_SECA": 0.4162,
        "LIQ_GERAL": 0.3065,
        "GIRO_ATIVO": 0.4912,
        "PME": 0.0,
        "CICLO_CAIXA": -706.3787,
        "NCG_RECEITA": -152.6356
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 39299.84,
        "P_L": -2.3837,
        "P_VPA": -0.1595,
        "EV_EBITDA": 3.673,
        "EV_EBIT": -11.361,
        "EV_RECEITA": 0.5196,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 6.9221,
        "ROA": -6.9144,
        "ROIC": 2.2602,
        "MARGEM_EBITDA": 14.1466,
        "MARGEM_LIQUIDA": -10.7047,
        "DIV_LIQ_EBITDA": 1.8692,
        "DIV_LIQ_PL": -0.1653,
        "ICJ": -0.2933,
        "COMPOSICAO_DIVIDA": 64.6992,
        "LIQ_CORRENTE": 0.2399,
        "LIQ_SECA": 0.2399,
        "LIQ_GERAL": 0.1872,
        "GIRO_ATIVO": 0.7916,
        "PME": 0.0,
        "CICLO_CAIXA": -395.7099,
        "NCG_RECEITA": -130.2982
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 94586.04,
        "P_L": -33.5055,
        "P_VPA": -0.3802,
        "EV_EBITDA": 2.351,
        "EV_EBIT": 7.1749,
        "EV_RECEITA": 0.8815,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 1.1414,
        "ROA": -1.29,
        "ROIC": -8.6642,
        "MARGEM_EBITDA": 37.4923,
        "MARGEM_LIQUIDA": -1.4942,
        "DIV_LIQ_EBITDA": 1.0157,
        "DIV_LIQ_PL": -0.2892,
        "ICJ": 0.8507,
        "COMPOSICAO_DIVIDA": 19.4398,
        "LIQ_CORRENTE": 0.3522,
        "LIQ_SECA": 0.3522,
        "LIQ_GERAL": 0.2584,
        "GIRO_ATIVO": 0.844,
        "PME": 0.0,
        "CICLO_CAIXA": -420.4434,
        "NCG_RECEITA": -103.6728
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T20:37:24.595294",
    "preco_utilizado": 4.04,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 13321978,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 53820.79,
      "P_L": -19.0651,
      "P_VPA": -0.2164,
      "EV_EBITDA": 1.7755,
      "EV_EBIT": 5.4186,
      "EV_RECEITA": 0.6657,
      "DY": 0.0,
      "PAYOUT": 0.0,
      "ROE": 1.1414,
      "ROA": -1.29,
      "ROIC": -8.6642,
      "MARGEM_EBITDA": 37.4923,
      "MARGEM_LIQUIDA": -1.4942,
      "DIV_LIQ_EBITDA": 1.0157,
      "DIV_LIQ_PL": -0.2892,
      "ICJ": 0.8507,
      "COMPOSICAO_DIVIDA": 19.4398,
      "LIQ_CORRENTE": 0.3522,
      "LIQ_SECA": 0.3522,
      "LIQ_GERAL": 0.2584,
      "GIRO_ATIVO": 0.844,
      "PME": 0.0,
      "CICLO_CAIXA": -420.4434,
      "NCG_RECEITA": -103.6728
    }
  },
  "periodos_disponiveis": [
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
