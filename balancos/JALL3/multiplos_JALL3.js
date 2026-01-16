// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["JALL3"] = {
  "ticker": "JALL3",
  "ticker_preco": "JALL3",
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
        "VALOR_MERCADO": 846610.93,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": null,
        "ROA": null,
        "ROIC": null,
        "MARGEM_EBITDA": null,
        "MARGEM_LIQUIDA": null,
        "DIV_LIQ_EBITDA": null,
        "DIV_LIQ_PL": null,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": null,
        "LIQ_CORRENTE": null,
        "LIQ_SECA": null,
        "LIQ_GERAL": null,
        "GIRO_ATIVO": null,
        "PME": null,
        "CICLO_CAIXA": null,
        "NCG_RECEITA": null
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 846610.93,
        "P_L": 7.0823,
        "P_VPA": 1.5233,
        "EV_EBITDA": 3.0038,
        "EV_EBIT": 5.5613,
        "EV_RECEITA": 2.0951,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 21.5088,
        "ROA": 4.2513,
        "ROIC": 13.7518,
        "MARGEM_EBITDA": 69.7507,
        "MARGEM_LIQUIDA": 11.7973,
        "DIV_LIQ_EBITDA": 1.8059,
        "DIV_LIQ_PL": 2.2966,
        "ICJ": 0.6783,
        "COMPOSICAO_DIVIDA": 25.0901,
        "LIQ_CORRENTE": 1.8836,
        "LIQ_SECA": 1.5168,
        "LIQ_GERAL": 0.6233,
        "GIRO_ATIVO": 0.3604,
        "PME": 350.0189,
        "CICLO_CAIXA": 332.8491,
        "NCG_RECEITA": 44.064
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 2768881.63,
        "P_L": 7.733,
        "P_VPA": 2.0847,
        "EV_EBITDA": 2.9818,
        "EV_EBIT": 4.2537,
        "EV_RECEITA": 2.6234,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 38.0118,
        "ROA": 10.8824,
        "ROIC": 25.5811,
        "MARGEM_EBITDA": 87.978,
        "MARGEM_LIQUIDA": 25.6529,
        "DIV_LIQ_EBITDA": 0.727,
        "DIV_LIQ_PL": 0.6722,
        "ICJ": 0.9618,
        "COMPOSICAO_DIVIDA": 19.2831,
        "LIQ_CORRENTE": 2.5848,
        "LIQ_SECA": 2.1252,
        "LIQ_GERAL": 0.7975,
        "GIRO_ATIVO": 0.3704,
        "PME": 578.4089,
        "CICLO_CAIXA": 506.0923,
        "NCG_RECEITA": 41.4807
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 2078835.74,
        "P_L": 2.3278,
        "P_VPA": 0.9782,
        "EV_EBITDA": 2.475,
        "EV_EBIT": 3.6532,
        "EV_RECEITA": 2.2604,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 51.7189,
        "ROA": 18.4983,
        "ROIC": 17.8669,
        "MARGEM_EBITDA": 91.3313,
        "MARGEM_LIQUIDA": 48.5471,
        "DIV_LIQ_EBITDA": 1.2376,
        "DIV_LIQ_PL": 0.9784,
        "ICJ": 1.15,
        "COMPOSICAO_DIVIDA": 13.6426,
        "LIQ_CORRENTE": 2.8625,
        "LIQ_SECA": 2.366,
        "LIQ_GERAL": 0.675,
        "GIRO_ATIVO": 0.3125,
        "PME": 275.1514,
        "CICLO_CAIXA": 248.5899,
        "NCG_RECEITA": 42.7684
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 2249897.53,
        "P_L": 6.8631,
        "P_VPA": 1.0858,
        "EV_EBITDA": 3.155,
        "EV_EBIT": 11.6455,
        "EV_RECEITA": 2.7423,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 15.6204,
        "ROA": 5.1922,
        "ROIC": 5.8694,
        "MARGEM_EBITDA": 86.9167,
        "MARGEM_LIQUIDA": 17.4003,
        "DIV_LIQ_EBITDA": 1.7811,
        "DIV_LIQ_PL": 1.4075,
        "ICJ": 0.6554,
        "COMPOSICAO_DIVIDA": 7.5439,
        "LIQ_CORRENTE": 3.8758,
        "LIQ_SECA": 2.7664,
        "LIQ_GERAL": 0.6289,
        "GIRO_ATIVO": 0.2795,
        "PME": 256.2313,
        "CICLO_CAIXA": 245.1064,
        "NCG_RECEITA": 57.0915
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1408434.25,
        "P_L": -261.0871,
        "P_VPA": 0.6983,
        "EV_EBITDA": 2.9326,
        "EV_EBIT": 10.2798,
        "EV_RECEITA": 2.2464,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": -0.2638,
        "ROA": -0.0766,
        "ROIC": 5.6967,
        "MARGEM_EBITDA": 76.6025,
        "MARGEM_LIQUIDA": -0.2529,
        "DIV_LIQ_EBITDA": 2.0705,
        "DIV_LIQ_PL": 1.6772,
        "ICJ": 0.5393,
        "COMPOSICAO_DIVIDA": 8.9449,
        "LIQ_CORRENTE": 3.3019,
        "LIQ_SECA": 2.4522,
        "LIQ_GERAL": 0.573,
        "GIRO_ATIVO": 0.2902,
        "PME": 311.9442,
        "CICLO_CAIXA": 299.5935,
        "NCG_RECEITA": 53.9506
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 831704.71,
        "P_L": -7.4093,
        "P_VPA": 0.4142,
        "EV_EBITDA": 2.8604,
        "EV_EBIT": 161.6305,
        "EV_RECEITA": 1.6649,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": -5.4775,
        "ROA": -1.5106,
        "ROIC": 0.3186,
        "MARGEM_EBITDA": 58.2063,
        "MARGEM_LIQUIDA": -4.4741,
        "DIV_LIQ_EBITDA": 2.2908,
        "DIV_LIQ_PL": 1.6659,
        "ICJ": 0.0599,
        "COMPOSICAO_DIVIDA": 14.8836,
        "LIQ_CORRENTE": 2.7402,
        "LIQ_SECA": 2.1316,
        "LIQ_GERAL": 0.5824,
        "GIRO_ATIVO": 0.3369,
        "PME": 152.8365,
        "CICLO_CAIXA": 143.6902,
        "NCG_RECEITA": 41.3521
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T18:34:39.509243",
    "preco_utilizado": 2.92,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 303541864,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 886342.24,
      "P_L": -7.8961,
      "P_VPA": 0.4414,
      "EV_EBITDA": 2.8978,
      "EV_EBIT": 163.7447,
      "EV_RECEITA": 1.6867,
      "DY": 0.0,
      "PAYOUT": 0.0,
      "ROE": -5.4775,
      "ROA": -1.5106,
      "ROIC": 0.3186,
      "MARGEM_EBITDA": 58.2063,
      "MARGEM_LIQUIDA": -4.4741,
      "DIV_LIQ_EBITDA": 2.2908,
      "DIV_LIQ_PL": 1.6659,
      "ICJ": 0.0599,
      "COMPOSICAO_DIVIDA": 14.8836,
      "LIQ_CORRENTE": 2.7402,
      "LIQ_SECA": 2.1316,
      "LIQ_GERAL": 0.5824,
      "GIRO_ATIVO": 0.3369,
      "PME": 152.8365,
      "CICLO_CAIXA": 143.6902,
      "NCG_RECEITA": 41.3521
    }
  },
  "periodos_disponiveis": [
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
