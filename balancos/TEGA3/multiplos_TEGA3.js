// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["TEGA3"] = {
  "ticker": "TEGA3",
  "ticker_preco": "TEGA3",
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
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 11.0043,
        "ROA": 6.6234,
        "ROIC": 9.799,
        "MARGEM_EBITDA": 17.0601,
        "MARGEM_LIQUIDA": 12.1262,
        "DIV_LIQ_EBITDA": 0.0771,
        "DIV_LIQ_PL": 0.0119,
        "ICJ": 13.5545,
        "COMPOSICAO_DIVIDA": 32.1812,
        "LIQ_CORRENTE": 3.3315,
        "LIQ_SECA": 1.9963,
        "LIQ_GERAL": 2.1836,
        "GIRO_ATIVO": 0.5462,
        "PME": 236.0307,
        "CICLO_CAIXA": 320.5465,
        "NCG_RECEITA": 55.1917
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 6.9699,
        "ROA": 4.1992,
        "ROIC": 4.3914,
        "MARGEM_EBITDA": 12.6157,
        "MARGEM_LIQUIDA": 10.9135,
        "DIV_LIQ_EBITDA": 0.1284,
        "DIV_LIQ_PL": 0.0099,
        "ICJ": 4.4207,
        "COMPOSICAO_DIVIDA": 13.8112,
        "LIQ_CORRENTE": 4.4686,
        "LIQ_SECA": 2.8076,
        "LIQ_GERAL": 2.0933,
        "GIRO_ATIVO": 0.3682,
        "PME": 343.3924,
        "CICLO_CAIXA": 515.4252,
        "NCG_RECEITA": 94.8659
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 7.7217,
        "ROA": 4.8067,
        "ROIC": 4.0283,
        "MARGEM_EBITDA": 11.4403,
        "MARGEM_LIQUIDA": 12.8541,
        "DIV_LIQ_EBITDA": 0.2602,
        "DIV_LIQ_PL": 0.0173,
        "ICJ": 7.3646,
        "COMPOSICAO_DIVIDA": 6.9266,
        "LIQ_CORRENTE": 4.0697,
        "LIQ_SECA": 1.9492,
        "LIQ_GERAL": 2.2926,
        "GIRO_ATIVO": 0.3736,
        "PME": 461.2563,
        "CICLO_CAIXA": 573.2603,
        "NCG_RECEITA": 97.143
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 4.237,
        "ROA": 2.6384,
        "ROIC": 2.5435,
        "MARGEM_EBITDA": 10.2469,
        "MARGEM_LIQUIDA": 8.8683,
        "DIV_LIQ_EBITDA": 2.6958,
        "DIV_LIQ_PL": 0.1279,
        "ICJ": 3.8655,
        "COMPOSICAO_DIVIDA": 9.2531,
        "LIQ_CORRENTE": 4.4288,
        "LIQ_SECA": 2.0138,
        "LIQ_GERAL": 2.1512,
        "GIRO_ATIVO": 0.2805,
        "PME": 533.9803,
        "CICLO_CAIXA": 671.3394,
        "NCG_RECEITA": 130.4637
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 0.0814,
        "ROA": 0.0501,
        "ROIC": 0.89,
        "MARGEM_EBITDA": 5.146,
        "MARGEM_LIQUIDA": 0.1721,
        "DIV_LIQ_EBITDA": 6.3162,
        "DIV_LIQ_PL": 0.1542,
        "ICJ": 1.0143,
        "COMPOSICAO_DIVIDA": 26.1809,
        "LIQ_CORRENTE": 4.3696,
        "LIQ_SECA": 1.4013,
        "LIQ_GERAL": 2.2122,
        "GIRO_ATIVO": 0.2966,
        "PME": 690.1752,
        "CICLO_CAIXA": 793.5439,
        "NCG_RECEITA": 161.934
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": -2.9648,
        "ROA": -1.8774,
        "ROIC": -1.2112,
        "MARGEM_EBITDA": -3.171,
        "MARGEM_LIQUIDA": -6.9427,
        "DIV_LIQ_EBITDA": -14.496,
        "DIV_LIQ_PL": 0.1992,
        "ICJ": -2.4256,
        "COMPOSICAO_DIVIDA": 51.5241,
        "LIQ_CORRENTE": 3.5132,
        "LIQ_SECA": 0.8741,
        "LIQ_GERAL": 2.2675,
        "GIRO_ATIVO": 0.2747,
        "PME": 854.4073,
        "CICLO_CAIXA": 954.598,
        "NCG_RECEITA": 195.1377
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T10:32:21.852044",
    "preco_utilizado": null,
    "periodo_preco": "",
    "acoes_utilizadas": 334150965,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": null,
      "P_L": null,
      "P_VPA": null,
      "EV_EBITDA": null,
      "EV_EBIT": null,
      "EV_RECEITA": null,
      "DY": 0.0,
      "PAYOUT": 0.0,
      "ROE": -2.9648,
      "ROA": -1.8774,
      "ROIC": -1.2112,
      "MARGEM_EBITDA": -3.171,
      "MARGEM_LIQUIDA": -6.9427,
      "DIV_LIQ_EBITDA": -14.496,
      "DIV_LIQ_PL": 0.1992,
      "ICJ": -2.4256,
      "COMPOSICAO_DIVIDA": 51.5241,
      "LIQ_CORRENTE": 3.5132,
      "LIQ_SECA": 0.8741,
      "LIQ_GERAL": 2.2675,
      "GIRO_ATIVO": 0.2747,
      "PME": 854.4073,
      "CICLO_CAIXA": 954.598,
      "NCG_RECEITA": 195.1377
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
