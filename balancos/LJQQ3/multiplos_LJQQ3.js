// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["LJQQ3"] = {
  "ticker": "LJQQ3",
  "ticker_preco": "LJQQ3",
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
        "VALOR_MERCADO": 425148.91,
        "P_L": 14.1142,
        "P_VPA": 2.9187,
        "EV_EBITDA": 2.9844,
        "EV_EBIT": 4.3065,
        "EV_RECEITA": 0.3652,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 20.6788,
        "ROA": 1.8313,
        "ROIC": 35.5892,
        "MARGEM_EBITDA": 12.2374,
        "MARGEM_LIQUIDA": 2.2412,
        "DIV_LIQ_EBITDA": 0.3995,
        "DIV_LIQ_PL": 0.4511,
        "ICJ": 1.382,
        "COMPOSICAO_DIVIDA": 20.6057,
        "LIQ_CORRENTE": 1.631,
        "LIQ_SECA": 1.3139,
        "LIQ_GERAL": 0.8924,
        "GIRO_ATIVO": 0.8171,
        "PME": 100.6947,
        "CICLO_CAIXA": 112.637,
        "NCG_RECEITA": 18.2537
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 2738183.73,
        "P_L": 40.3469,
        "P_VPA": 5.7126,
        "EV_EBITDA": 11.993,
        "EV_EBIT": 16.9759,
        "EV_RECEITA": 1.6081,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 21.7174,
        "ROA": 3.5132,
        "ROIC": 29.1168,
        "MARGEM_EBITDA": 13.4085,
        "MARGEM_LIQUIDA": 4.1863,
        "DIV_LIQ_EBITDA": -0.6037,
        "DIV_LIQ_PL": -0.2738,
        "ICJ": 2.0711,
        "COMPOSICAO_DIVIDA": 44.6869,
        "LIQ_CORRENTE": 1.64,
        "LIQ_SECA": 1.3136,
        "LIQ_GERAL": 1.0208,
        "GIRO_ATIVO": 0.7307,
        "PME": 120.6749,
        "CICLO_CAIXA": 124.432,
        "NCG_RECEITA": 17.6561
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 1900996.23,
        "P_L": 27.8628,
        "P_VPA": 3.5106,
        "EV_EBITDA": 7.3195,
        "EV_EBIT": 11.1474,
        "EV_RECEITA": 0.8987,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 13.3669,
        "ROA": 2.7787,
        "ROIC": 23.1166,
        "MARGEM_EBITDA": 12.2778,
        "MARGEM_LIQUIDA": 3.355,
        "DIV_LIQ_EBITDA": -0.2941,
        "DIV_LIQ_PL": -0.1356,
        "ICJ": 1.4258,
        "COMPOSICAO_DIVIDA": 40.8853,
        "LIQ_CORRENTE": 1.6182,
        "LIQ_SECA": 1.2117,
        "LIQ_GERAL": 0.9556,
        "GIRO_ATIVO": 0.7554,
        "PME": 132.9975,
        "CICLO_CAIXA": 142.3119,
        "NCG_RECEITA": 22.8513
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 713575.92,
        "P_L": -38.153,
        "P_VPA": 1.3293,
        "EV_EBITDA": 3.1991,
        "EV_EBIT": 7.2451,
        "EV_RECEITA": 0.2743,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": -3.4689,
        "ROA": -0.6536,
        "ROIC": 12.6284,
        "MARGEM_EBITDA": 8.5738,
        "MARGEM_LIQUIDA": -0.8087,
        "DIV_LIQ_EBITDA": -0.3996,
        "DIV_LIQ_PL": -0.1476,
        "ICJ": 0.5368,
        "COMPOSICAO_DIVIDA": 15.5232,
        "LIQ_CORRENTE": 1.8912,
        "LIQ_SECA": 1.4532,
        "LIQ_GERAL": 0.9198,
        "GIRO_ATIVO": 0.7629,
        "PME": 109.8082,
        "CICLO_CAIXA": 159.4311,
        "NCG_RECEITA": 22.9096
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 1111914.45,
        "P_L": 56.5026,
        "P_VPA": 2.083,
        "EV_EBITDA": 4.6469,
        "EV_EBIT": 10.5007,
        "EV_RECEITA": 0.451,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 3.6762,
        "ROA": 0.6211,
        "ROIC": 13.5016,
        "MARGEM_EBITDA": 9.7062,
        "MARGEM_LIQUIDA": 0.8206,
        "DIV_LIQ_EBITDA": -0.1301,
        "DIV_LIQ_PL": -0.0567,
        "ICJ": 0.5639,
        "COMPOSICAO_DIVIDA": 22.1991,
        "LIQ_CORRENTE": 1.6969,
        "LIQ_SECA": 1.3339,
        "LIQ_GERAL": 0.9346,
        "GIRO_ATIVO": 0.7254,
        "PME": 108.6596,
        "CICLO_CAIXA": 177.246,
        "NCG_RECEITA": 20.459
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 446941.29,
        "P_L": 3061.2417,
        "P_VPA": 0.8186,
        "EV_EBITDA": 1.3577,
        "EV_EBIT": 3.1087,
        "EV_RECEITA": 0.1232,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 0.027,
        "ROA": 0.0042,
        "ROIC": 16.3114,
        "MARGEM_EBITDA": 9.0732,
        "MARGEM_LIQUIDA": 0.0055,
        "DIV_LIQ_EBITDA": -0.4898,
        "DIV_LIQ_PL": -0.217,
        "ICJ": 0.5209,
        "COMPOSICAO_DIVIDA": 36.693,
        "LIQ_CORRENTE": 1.5575,
        "LIQ_SECA": 1.2518,
        "LIQ_GERAL": 0.9494,
        "GIRO_ATIVO": 0.7202,
        "PME": 107.3072,
        "CICLO_CAIXA": 178.821,
        "NCG_RECEITA": 18.3035
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 469702.19,
        "P_L": -4.1566,
        "P_VPA": 1.0481,
        "EV_EBITDA": 1.7336,
        "EV_EBIT": 13.4444,
        "EV_RECEITA": 0.1804,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": -22.3295,
        "ROA": -3.0867,
        "ROIC": 5.131,
        "MARGEM_EBITDA": 10.4085,
        "MARGEM_LIQUIDA": -4.0916,
        "DIV_LIQ_EBITDA": 0.0996,
        "DIV_LIQ_PL": 0.0639,
        "ICJ": 0.1524,
        "COMPOSICAO_DIVIDA": 31.8365,
        "LIQ_CORRENTE": 1.6385,
        "LIQ_SECA": 1.3028,
        "LIQ_GERAL": 0.9255,
        "GIRO_ATIVO": 0.7532,
        "PME": 106.3976,
        "CICLO_CAIXA": 227.0864,
        "NCG_RECEITA": 24.716
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T20:56:55.558873",
    "preco_utilizado": 2.27,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 206917263,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 469702.19,
      "P_L": -4.1566,
      "P_VPA": 1.0481,
      "EV_EBITDA": 1.7336,
      "EV_EBIT": 13.4444,
      "EV_RECEITA": 0.1804,
      "DY": 0.0,
      "PAYOUT": 0.0,
      "ROE": -22.3295,
      "ROA": -3.0867,
      "ROIC": 5.131,
      "MARGEM_EBITDA": 10.4085,
      "MARGEM_LIQUIDA": -4.0916,
      "DIV_LIQ_EBITDA": 0.0996,
      "DIV_LIQ_PL": 0.0639,
      "ICJ": 0.1524,
      "COMPOSICAO_DIVIDA": 31.8365,
      "LIQ_CORRENTE": 1.6385,
      "LIQ_SECA": 1.3028,
      "LIQ_GERAL": 0.9255,
      "GIRO_ATIVO": 0.7532,
      "PME": 106.3976,
      "CICLO_CAIXA": 227.0864,
      "NCG_RECEITA": 24.716
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
