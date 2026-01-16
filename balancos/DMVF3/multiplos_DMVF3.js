// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["DMVF3"] = {
  "ticker": "DMVF3",
  "ticker_preco": "DMVF3",
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
    "2019": {
      "periodo_referencia": "2019T4",
      "multiplos": {
        "VALOR_MERCADO": 354219.89,
        "P_L": -47.3113,
        "P_VPA": 0.76,
        "EV_EBITDA": 38.9668,
        "EV_EBIT": -25.036,
        "EV_RECEITA": 0.4626,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": -1.6065,
        "ROA": -0.6833,
        "ROIC": -2.1724,
        "MARGEM_EBITDA": 1.1871,
        "MARGEM_LIQUIDA": -0.6613,
        "DIV_LIQ_EBITDA": 12.6131,
        "DIV_LIQ_PL": 0.3638,
        "ICJ": -0.5194,
        "COMPOSICAO_DIVIDA": 60.0899,
        "LIQ_CORRENTE": 0.7442,
        "LIQ_SECA": 0.3569,
        "LIQ_GERAL": 0.4621,
        "GIRO_ATIVO": 1.0334,
        "PME": 58.9687,
        "CICLO_CAIXA": 11.4103,
        "NCG_RECEITA": -0.2883
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 646704.32,
        "P_L": 5257.7587,
        "P_VPA": 0.7734,
        "EV_EBITDA": 24.0133,
        "EV_EBIT": 85.9991,
        "EV_RECEITA": 0.5691,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 0.0189,
        "ROA": 0.0096,
        "ROIC": 0.5764,
        "MARGEM_EBITDA": 2.3701,
        "MARGEM_LIQUIDA": 0.0122,
        "DIV_LIQ_EBITDA": -3.1535,
        "DIV_LIQ_PL": -0.0898,
        "ICJ": 0.2024,
        "COMPOSICAO_DIVIDA": 64.2947,
        "LIQ_CORRENTE": 1.5205,
        "LIQ_SECA": 1.1053,
        "LIQ_GERAL": 0.9419,
        "GIRO_ATIVO": 0.6903,
        "PME": 69.8867,
        "CICLO_CAIXA": 24.9166,
        "NCG_RECEITA": 4.3166
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 213037.96,
        "P_L": 107.6493,
        "P_VPA": 0.2542,
        "EV_EBITDA": 9.6656,
        "EV_EBIT": -79.393,
        "EV_RECEITA": 0.1469,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 0.2364,
        "ROA": 0.1353,
        "ROIC": -0.1758,
        "MARGEM_EBITDA": 1.5199,
        "MARGEM_LIQUIDA": 0.1734,
        "DIV_LIQ_EBITDA": -2.6147,
        "DIV_LIQ_PL": -0.0541,
        "ICJ": -0.0872,
        "COMPOSICAO_DIVIDA": 95.1644,
        "LIQ_CORRENTE": 1.1044,
        "LIQ_SECA": 0.7123,
        "LIQ_GERAL": 0.8314,
        "GIRO_ATIVO": 0.7762,
        "PME": 65.4442,
        "CICLO_CAIXA": 8.1297,
        "NCG_RECEITA": -0.9216
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 206965.62,
        "P_L": 18.2268,
        "P_VPA": 0.2436,
        "EV_EBITDA": 2.2972,
        "EV_EBIT": 5.0349,
        "EV_RECEITA": 0.121,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 1.3457,
        "ROA": 0.7721,
        "ROIC": 2.8612,
        "MARGEM_EBITDA": 5.2656,
        "MARGEM_LIQUIDA": 0.7656,
        "DIV_LIQ_EBITDA": -0.3529,
        "DIV_LIQ_PL": -0.0324,
        "ICJ": 1.144,
        "COMPOSICAO_DIVIDA": 8.1722,
        "LIQ_CORRENTE": 1.1998,
        "LIQ_SECA": 0.7458,
        "LIQ_GERAL": 0.8674,
        "GIRO_ATIVO": 1.0085,
        "PME": 55.5715,
        "CICLO_CAIXA": 8.7077,
        "NCG_RECEITA": 0.9675
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 300074.85,
        "P_L": 14.0471,
        "P_VPA": 0.3446,
        "EV_EBITDA": 3.7997,
        "EV_EBIT": 5.5079,
        "EV_RECEITA": 0.1616,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 2.4835,
        "ROA": 1.4151,
        "ROIC": 3.9689,
        "MARGEM_EBITDA": 4.2538,
        "MARGEM_LIQUIDA": 1.2214,
        "DIV_LIQ_EBITDA": -0.2338,
        "DIV_LIQ_PL": -0.02,
        "ICJ": 1.6603,
        "COMPOSICAO_DIVIDA": 34.6128,
        "LIQ_CORRENTE": 1.158,
        "LIQ_SECA": 0.6944,
        "LIQ_GERAL": 0.8776,
        "GIRO_ATIVO": 1.1294,
        "PME": 56.9231,
        "CICLO_CAIXA": 7.7731,
        "NCG_RECEITA": 1.688
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 311207.48,
        "P_L": 12.0357,
        "P_VPA": 0.3471,
        "EV_EBITDA": 3.2675,
        "EV_EBIT": 4.6253,
        "EV_RECEITA": 0.1354,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 2.9257,
        "ROA": 1.5287,
        "ROIC": 4.7535,
        "MARGEM_EBITDA": 4.1429,
        "MARGEM_LIQUIDA": 1.1967,
        "DIV_LIQ_EBITDA": -0.2092,
        "DIV_LIQ_PL": -0.0209,
        "ICJ": 1.4784,
        "COMPOSICAO_DIVIDA": 27.4318,
        "LIQ_CORRENTE": 1.1398,
        "LIQ_SECA": 0.6092,
        "LIQ_GERAL": 0.7907,
        "GIRO_ATIVO": 1.1778,
        "PME": 67.3512,
        "CICLO_CAIXA": 10.0183,
        "NCG_RECEITA": 1.2478
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 253014.21,
        "P_L": 15.1878,
        "P_VPA": 0.2781,
        "EV_EBITDA": 2.0077,
        "EV_EBIT": 3.9735,
        "EV_RECEITA": 0.1046,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 1.8478,
        "ROA": 0.9118,
        "ROIC": 4.8593,
        "MARGEM_EBITDA": 5.2084,
        "MARGEM_LIQUIDA": 0.6413,
        "DIV_LIQ_EBITDA": 0.1376,
        "DIV_LIQ_PL": 0.0205,
        "ICJ": 1.0765,
        "COMPOSICAO_DIVIDA": 91.305,
        "LIQ_CORRENTE": 1.0644,
        "LIQ_SECA": 0.6076,
        "LIQ_GERAL": 0.7586,
        "GIRO_ATIVO": 1.3435,
        "PME": 51.9367,
        "CICLO_CAIXA": 16.2393,
        "NCG_RECEITA": 2.0701
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T21:22:27.834442",
    "preco_utilizado": 7.0,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 50602842,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 354219.89,
      "P_L": 21.263,
      "P_VPA": 0.3893,
      "EV_EBITDA": 2.7557,
      "EV_EBIT": 5.454,
      "EV_RECEITA": 0.1435,
      "DY": 0.0,
      "PAYOUT": 0.0,
      "ROE": 1.8478,
      "ROA": 0.9118,
      "ROIC": 4.8593,
      "MARGEM_EBITDA": 5.2084,
      "MARGEM_LIQUIDA": 0.6413,
      "DIV_LIQ_EBITDA": 0.1376,
      "DIV_LIQ_PL": 0.0205,
      "ICJ": 1.0765,
      "COMPOSICAO_DIVIDA": 91.305,
      "LIQ_CORRENTE": 1.0644,
      "LIQ_SECA": 0.6076,
      "LIQ_GERAL": 0.7586,
      "GIRO_ATIVO": 1.3435,
      "PME": 51.9367,
      "CICLO_CAIXA": 16.2393,
      "NCG_RECEITA": 2.0701
    }
  },
  "periodos_disponiveis": [
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
