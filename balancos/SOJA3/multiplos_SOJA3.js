// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["SOJA3"] = {
  "ticker": "SOJA3",
  "ticker_preco": "SOJA3",
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
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 1539223.88,
        "P_L": null,
        "P_VPA": 2.3577,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": null,
        "PAYOUT": null,
        "ROE": null,
        "ROA": null,
        "ROIC": null,
        "MARGEM_EBITDA": null,
        "MARGEM_LIQUIDA": null,
        "DIV_LIQ_EBITDA": null,
        "DIV_LIQ_PL": -0.2418,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 61.4172,
        "LIQ_CORRENTE": 3.1908,
        "LIQ_SECA": 2.7819,
        "LIQ_GERAL": 2.5664,
        "GIRO_ATIVO": null,
        "PME": null,
        "CICLO_CAIXA": null,
        "NCG_RECEITA": null
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 1019120.84,
        "P_L": 4.8812,
        "P_VPA": 1.0648,
        "EV_EBITDA": 4.3416,
        "EV_EBIT": 4.4471,
        "EV_RECEITA": 0.4782,
        "DY": 1.45,
        "PAYOUT": 7.0776,
        "ROE": 25.9369,
        "ROA": 17.3656,
        "ROIC": 15.8428,
        "MARGEM_EBITDA": 11.0155,
        "MARGEM_LIQUIDA": 10.1819,
        "DIV_LIQ_EBITDA": -0.1702,
        "DIV_LIQ_PL": -0.0402,
        "ICJ": 4.149,
        "COMPOSICAO_DIVIDA": 33.6496,
        "LIQ_CORRENTE": 3.2827,
        "LIQ_SECA": 2.8491,
        "LIQ_GERAL": 2.0324,
        "GIRO_ATIVO": 1.4147,
        "PME": 25.6791,
        "CICLO_CAIXA": 46.1731,
        "NCG_RECEITA": 21.496
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 1696191.92,
        "P_L": 4.9172,
        "P_VPA": 1.1519,
        "EV_EBITDA": 5.7237,
        "EV_EBIT": 6.0734,
        "EV_RECEITA": 0.7407,
        "DY": 7.6613,
        "PAYOUT": 37.6719,
        "ROE": 28.3954,
        "ROA": 18.1172,
        "ROIC": 12.7142,
        "MARGEM_EBITDA": 12.9405,
        "MARGEM_LIQUIDA": 16.5942,
        "DIV_LIQ_EBITDA": -0.5819,
        "DIV_LIQ_PL": -0.1063,
        "ICJ": 2.9042,
        "COMPOSICAO_DIVIDA": 6.7179,
        "LIQ_CORRENTE": 4.5827,
        "LIQ_SECA": 4.1742,
        "LIQ_GERAL": 1.9088,
        "GIRO_ATIVO": 0.8814,
        "PME": 28.074,
        "CICLO_CAIXA": 80.3549,
        "NCG_RECEITA": 24.9998
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1277441.04,
        "P_L": 7.9587,
        "P_VPA": 0.6537,
        "EV_EBITDA": 6.34,
        "EV_EBIT": 7.6793,
        "EV_RECEITA": 0.6053,
        "DY": 3.1504,
        "PAYOUT": 25.0734,
        "ROE": 9.3679,
        "ROA": 6.3882,
        "ROIC": 5.347,
        "MARGEM_EBITDA": 9.5475,
        "MARGEM_LIQUIDA": 8.7183,
        "DIV_LIQ_EBITDA": -0.9275,
        "DIV_LIQ_PL": -0.0834,
        "ICJ": 0.9527,
        "COMPOSICAO_DIVIDA": 34.0468,
        "LIQ_CORRENTE": 4.0641,
        "LIQ_SECA": 3.5357,
        "LIQ_GERAL": 2.5997,
        "GIRO_ATIVO": 0.6904,
        "PME": 50.5787,
        "CICLO_CAIXA": 127.6178,
        "NCG_RECEITA": 47.8934
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 1330216.68,
        "P_L": 7.1276,
        "P_VPA": 0.6535,
        "EV_EBITDA": 6.8078,
        "EV_EBIT": 9.7522,
        "EV_RECEITA": 0.7376,
        "DY": 3.0254,
        "PAYOUT": 21.5641,
        "ROE": 9.5057,
        "ROA": 5.3588,
        "ROIC": 4.8072,
        "MARGEM_EBITDA": 10.8344,
        "MARGEM_LIQUIDA": 7.9605,
        "DIV_LIQ_EBITDA": 1.5709,
        "DIV_LIQ_PL": 0.196,
        "ICJ": 0.8893,
        "COMPOSICAO_DIVIDA": 4.9267,
        "LIQ_CORRENTE": 3.6701,
        "LIQ_SECA": 2.4941,
        "LIQ_GERAL": 1.5572,
        "GIRO_ATIVO": 0.5715,
        "PME": 153.8349,
        "CICLO_CAIXA": 159.8742,
        "NCG_RECEITA": 47.3034
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-15T19:04:38.581296",
    "preco_utilizado": 8.83,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 135322144,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 1194894.53,
      "P_L": 6.4025,
      "P_VPA": 0.587,
      "EV_EBITDA": 6.2751,
      "EV_EBIT": 8.9891,
      "EV_RECEITA": 0.6799,
      "DY": 3.3681,
      "PAYOUT": 21.5641,
      "ROE": 9.5057,
      "ROA": 5.3588,
      "ROIC": 4.8072,
      "MARGEM_EBITDA": 10.8344,
      "MARGEM_LIQUIDA": 7.9605,
      "DIV_LIQ_EBITDA": 1.5709,
      "DIV_LIQ_PL": 0.196,
      "ICJ": 0.8893,
      "COMPOSICAO_DIVIDA": 4.9267,
      "LIQ_CORRENTE": 3.6701,
      "LIQ_SECA": 2.4941,
      "LIQ_GERAL": 1.5572,
      "GIRO_ATIVO": 0.5715,
      "PME": 153.8349,
      "CICLO_CAIXA": 159.8742,
      "NCG_RECEITA": 47.3034
    }
  },
  "periodos_disponiveis": [
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
