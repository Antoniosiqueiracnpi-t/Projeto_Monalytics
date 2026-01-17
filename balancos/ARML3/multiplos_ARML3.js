// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["ARML3"] = {
  "ticker": "ARML3",
  "ticker_preco": "ARML3",
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
        "VALOR_MERCADO": 1452189.99,
        "P_L": null,
        "P_VPA": 17.0725,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 5.0751,
        "PAYOUT": null,
        "ROE": null,
        "ROA": null,
        "ROIC": null,
        "MARGEM_EBITDA": null,
        "MARGEM_LIQUIDA": null,
        "DIV_LIQ_EBITDA": null,
        "DIV_LIQ_PL": 2.3958,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 22.5132,
        "LIQ_CORRENTE": 1.3606,
        "LIQ_SECA": 1.3385,
        "LIQ_GERAL": 0.3573,
        "GIRO_ATIVO": null,
        "PME": null,
        "CICLO_CAIXA": null,
        "NCG_RECEITA": null
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 7233289.18,
        "P_L": 108.6438,
        "P_VPA": 6.5007,
        "EV_EBITDA": 36.3292,
        "EV_EBIT": 49.4536,
        "EV_RECEITA": 16.7154,
        "DY": 1.0189,
        "PAYOUT": 110.6973,
        "ROE": 11.1171,
        "ROA": 3.5876,
        "ROIC": 7.3604,
        "MARGEM_EBITDA": 46.0109,
        "MARGEM_LIQUIDA": 14.8857,
        "DIV_LIQ_EBITDA": 1.1803,
        "DIV_LIQ_PL": 0.2183,
        "ICJ": 1.9873,
        "COMPOSICAO_DIVIDA": 8.9285,
        "LIQ_CORRENTE": 6.0921,
        "LIQ_SECA": 6.0365,
        "LIQ_GERAL": 0.8752,
        "GIRO_ATIVO": 0.1363,
        "PME": 26.8197,
        "CICLO_CAIXA": 87.1821,
        "NCG_RECEITA": 19.7285
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 3345975.12,
        "P_L": 22.5179,
        "P_VPA": 2.8881,
        "EV_EBITDA": 9.9402,
        "EV_EBIT": 14.1969,
        "EV_RECEITA": 4.778,
        "DY": 2.2043,
        "PAYOUT": 49.6357,
        "ROE": 13.0848,
        "ROA": 4.2379,
        "ROIC": 8.958,
        "MARGEM_EBITDA": 48.0669,
        "MARGEM_LIQUIDA": 15.6124,
        "DIV_LIQ_EBITDA": 2.6263,
        "DIV_LIQ_PL": 1.0371,
        "ICJ": 1.1469,
        "COMPOSICAO_DIVIDA": 2.8843,
        "LIQ_CORRENTE": 3.2836,
        "LIQ_SECA": 3.195,
        "LIQ_GERAL": 0.5025,
        "GIRO_ATIVO": 0.2551,
        "PME": 24.8584,
        "CICLO_CAIXA": -88.2821,
        "NCG_RECEITA": 2.1979
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 4923681.12,
        "P_L": 24.9683,
        "P_VPA": 4.0032,
        "EV_EBITDA": 10.3661,
        "EV_EBIT": 13.2684,
        "EV_RECEITA": 4.6122,
        "DY": 1.5,
        "PAYOUT": 37.4532,
        "ROE": 16.5125,
        "ROA": 5.1129,
        "ROIC": 11.9416,
        "MARGEM_EBITDA": 44.4931,
        "MARGEM_LIQUIDA": 14.3665,
        "DIV_LIQ_EBITDA": 2.304,
        "DIV_LIQ_PL": 1.1441,
        "ICJ": 1.3882,
        "COMPOSICAO_DIVIDA": 12.6303,
        "LIQ_CORRENTE": 1.5885,
        "LIQ_SECA": 1.5129,
        "LIQ_GERAL": 0.4424,
        "GIRO_ATIVO": 0.3446,
        "PME": 28.133,
        "CICLO_CAIXA": -83.7154,
        "NCG_RECEITA": -1.4307
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1500319.44,
        "P_L": 8.5421,
        "P_VPA": 1.1444,
        "EV_EBITDA": 4.5943,
        "EV_EBIT": 6.3815,
        "EV_RECEITA": 1.8901,
        "DY": 4.9227,
        "PAYOUT": 42.0502,
        "ROE": 13.8246,
        "ROA": 4.0751,
        "ROIC": 10.9642,
        "MARGEM_EBITDA": 41.1407,
        "MARGEM_LIQUIDA": 9.9458,
        "DIV_LIQ_EBITDA": 2.5292,
        "DIV_LIQ_PL": 1.4016,
        "ICJ": 1.2612,
        "COMPOSICAO_DIVIDA": 3.2994,
        "LIQ_CORRENTE": 2.1309,
        "LIQ_SECA": 2.0121,
        "LIQ_GERAL": 0.4284,
        "GIRO_ATIVO": 0.3808,
        "PME": 26.0443,
        "CICLO_CAIXA": -8.0732,
        "NCG_RECEITA": 9.3196
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 1146895.46,
        "P_L": 20.7047,
        "P_VPA": 0.8693,
        "EV_EBITDA": 3.5954,
        "EV_EBIT": 7.3095,
        "EV_RECEITA": 1.6241,
        "DY": 6.4397,
        "PAYOUT": 133.332,
        "ROE": 4.2454,
        "ROA": 1.1379,
        "ROIC": 8.5415,
        "MARGEM_EBITDA": 45.1718,
        "MARGEM_LIQUIDA": 2.979,
        "DIV_LIQ_EBITDA": 2.23,
        "DIV_LIQ_PL": 1.4196,
        "ICJ": 0.8927,
        "COMPOSICAO_DIVIDA": 2.4761,
        "LIQ_CORRENTE": 2.2124,
        "LIQ_SECA": 2.0825,
        "LIQ_GERAL": 0.4361,
        "GIRO_ATIVO": 0.4013,
        "PME": 24.396,
        "CICLO_CAIXA": -26.0773,
        "NCG_RECEITA": 10.4996
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T20:16:16.339218",
    "preco_utilizado": 4.2,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 346494097,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 1455275.21,
      "P_L": 26.2718,
      "P_VPA": 1.103,
      "EV_EBITDA": 3.9625,
      "EV_EBIT": 8.0559,
      "EV_RECEITA": 1.7899,
      "DY": 5.0751,
      "PAYOUT": 133.332,
      "ROE": 4.2454,
      "ROA": 1.1379,
      "ROIC": 8.5415,
      "MARGEM_EBITDA": 45.1718,
      "MARGEM_LIQUIDA": 2.979,
      "DIV_LIQ_EBITDA": 2.23,
      "DIV_LIQ_PL": 1.4196,
      "ICJ": 0.8927,
      "COMPOSICAO_DIVIDA": 2.4761,
      "LIQ_CORRENTE": 2.2124,
      "LIQ_SECA": 2.0825,
      "LIQ_GERAL": 0.4361,
      "GIRO_ATIVO": 0.4013,
      "PME": 24.396,
      "CICLO_CAIXA": -26.0773,
      "NCG_RECEITA": 10.4996
    }
  },
  "periodos_disponiveis": [
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
