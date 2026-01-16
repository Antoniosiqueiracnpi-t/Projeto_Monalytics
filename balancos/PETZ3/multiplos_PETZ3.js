// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["PETZ3"] = {
  "ticker": "PETZ3",
  "ticker_preco": "PETZ3",
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
        "VALOR_MERCADO": 6625647.49,
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
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 7041684.39,
        "P_L": 58.7914,
        "P_VPA": 4.0026,
        "EV_EBITDA": 19.0834,
        "EV_EBIT": 25.3972,
        "EV_RECEITA": 2.0637,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 13.6164,
        "ROA": 6.9488,
        "ROIC": 13.1817,
        "MARGEM_EBITDA": 10.8141,
        "MARGEM_LIQUIDA": 3.7567,
        "DIV_LIQ_EBITDA": -1.3403,
        "DIV_LIQ_PL": -0.2627,
        "ICJ": 2.0219,
        "COMPOSICAO_DIVIDA": 56.7354,
        "LIQ_CORRENTE": 1.9478,
        "LIQ_SECA": 1.4697,
        "LIQ_GERAL": 0.8422,
        "GIRO_ATIVO": 0.9248,
        "PME": 72.7328,
        "CICLO_CAIXA": 28.2461,
        "NCG_RECEITA": 3.2358
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 2714706.31,
        "P_L": 53.6609,
        "P_VPA": 1.4749,
        "EV_EBITDA": 7.3729,
        "EV_EBIT": 19.4766,
        "EV_RECEITA": 0.9322,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 2.8107,
        "ROA": 1.4262,
        "ROIC": 5.0639,
        "MARGEM_EBITDA": 12.6438,
        "MARGEM_LIQUIDA": 1.7848,
        "DIV_LIQ_EBITDA": -0.2018,
        "DIV_LIQ_PL": -0.0393,
        "ICJ": 1.0805,
        "COMPOSICAO_DIVIDA": 76.2761,
        "LIQ_CORRENTE": 1.4775,
        "LIQ_SECA": 0.8968,
        "LIQ_GERAL": 0.6627,
        "GIRO_ATIVO": 0.7772,
        "PME": 103.8525,
        "CICLO_CAIXA": 56.6168,
        "NCG_RECEITA": 8.9213
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 1715962.19,
        "P_L": 104.9582,
        "P_VPA": 0.9486,
        "EV_EBITDA": 5.9127,
        "EV_EBIT": 13.4613,
        "EV_RECEITA": 0.5434,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 0.896,
        "ROA": 0.4278,
        "ROIC": 4.6522,
        "MARGEM_EBITDA": 9.1898,
        "MARGEM_LIQUIDA": 0.5152,
        "DIV_LIQ_EBITDA": 0.0283,
        "DIV_LIQ_PL": 0.0046,
        "ICJ": 0.6933,
        "COMPOSICAO_DIVIDA": 10.8171,
        "LIQ_CORRENTE": 1.814,
        "LIQ_SECA": 1.2331,
        "LIQ_GERAL": 0.6996,
        "GIRO_ATIVO": 0.7942,
        "PME": 93.9685,
        "CICLO_CAIXA": 48.2313,
        "NCG_RECEITA": 7.5382
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1883351.49,
        "P_L": -44.0488,
        "P_VPA": 1.1334,
        "EV_EBITDA": 8.1667,
        "EV_EBIT": 31.6295,
        "EV_RECEITA": 0.5996,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": -2.4639,
        "ROA": -1.0837,
        "ROIC": 2.3479,
        "MARGEM_EBITDA": 7.3423,
        "MARGEM_LIQUIDA": -1.2868,
        "DIV_LIQ_EBITDA": 0.4466,
        "DIV_LIQ_PL": 0.0656,
        "ICJ": 0.272,
        "COMPOSICAO_DIVIDA": 13.4975,
        "LIQ_CORRENTE": 1.6724,
        "LIQ_SECA": 1.0981,
        "LIQ_GERAL": 0.6972,
        "GIRO_ATIVO": 0.8529,
        "PME": 96.6106,
        "CICLO_CAIXA": 55.0351,
        "NCG_RECEITA": 7.7837
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 1753784.32,
        "P_L": 481.148,
        "P_VPA": 1.0219,
        "EV_EBITDA": 3.6828,
        "EV_EBIT": 13.8294,
        "EV_RECEITA": 0.4764,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 0.2135,
        "ROA": 0.0919,
        "ROIC": 4.8819,
        "MARGEM_EBITDA": 12.9373,
        "MARGEM_LIQUIDA": 0.1037,
        "DIV_LIQ_EBITDA": -0.1753,
        "DIV_LIQ_PL": -0.0464,
        "ICJ": 0.5007,
        "COMPOSICAO_DIVIDA": 22.498,
        "LIQ_CORRENTE": 1.7058,
        "LIQ_SECA": 1.1664,
        "LIQ_GERAL": 0.7572,
        "GIRO_ATIVO": 0.8908,
        "PME": 94.0105,
        "CICLO_CAIXA": 51.9825,
        "NCG_RECEITA": 6.1983
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T20:56:56.692918",
    "preco_utilizado": 4.39,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 462739925,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 2031428.27,
      "P_L": 557.3191,
      "P_VPA": 1.1836,
      "EV_EBITDA": 4.2935,
      "EV_EBIT": 16.1229,
      "EV_RECEITA": 0.5555,
      "DY": 0.0,
      "PAYOUT": 0.0,
      "ROE": 0.2135,
      "ROA": 0.0919,
      "ROIC": 4.8819,
      "MARGEM_EBITDA": 12.9373,
      "MARGEM_LIQUIDA": 0.1037,
      "DIV_LIQ_EBITDA": -0.1753,
      "DIV_LIQ_PL": -0.0464,
      "ICJ": 0.5007,
      "COMPOSICAO_DIVIDA": 22.498,
      "LIQ_CORRENTE": 1.7058,
      "LIQ_SECA": 1.1664,
      "LIQ_GERAL": 0.7572,
      "GIRO_ATIVO": 0.8908,
      "PME": 94.0105,
      "CICLO_CAIXA": 51.9825,
      "NCG_RECEITA": 6.1983
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
