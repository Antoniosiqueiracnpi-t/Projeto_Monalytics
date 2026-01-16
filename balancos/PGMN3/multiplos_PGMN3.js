// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["PGMN3"] = {
  "ticker": "PGMN3",
  "ticker_preco": "PGMN3",
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
        "VALOR_MERCADO": 3075402.76,
        "P_L": null,
        "P_VPA": 1.4713,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 7.3683,
        "PAYOUT": null,
        "ROE": null,
        "ROA": null,
        "ROIC": null,
        "MARGEM_EBITDA": null,
        "MARGEM_LIQUIDA": null,
        "DIV_LIQ_EBITDA": null,
        "DIV_LIQ_PL": 0.2562,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 36.6256,
        "LIQ_CORRENTE": 1.6028,
        "LIQ_SECA": 0.7098,
        "LIQ_GERAL": 0.9282,
        "GIRO_ATIVO": null,
        "PME": null,
        "CICLO_CAIXA": null,
        "NCG_RECEITA": null
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 1502809.48,
        "P_L": 5.713,
        "P_VPA": 0.6414,
        "EV_EBITDA": 1.9704,
        "EV_EBIT": 4.5665,
        "EV_RECEITA": 0.3165,
        "DY": 15.76,
        "PAYOUT": 90.0375,
        "ROE": 11.8673,
        "ROA": 3.4679,
        "ROIC": 11.2134,
        "MARGEM_EBITDA": 16.0615,
        "MARGEM_LIQUIDA": 2.8626,
        "DIV_LIQ_EBITDA": 0.9522,
        "DIV_LIQ_PL": 0.5998,
        "ICJ": 1.297,
        "COMPOSICAO_DIVIDA": 30.0501,
        "LIQ_CORRENTE": 1.4061,
        "LIQ_SECA": 0.3743,
        "LIQ_GERAL": 0.8317,
        "GIRO_ATIVO": 1.0688,
        "PME": 174.8068,
        "CICLO_CAIXA": 109.9297,
        "NCG_RECEITA": 16.2889
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 1826587.11,
        "P_L": 667.8563,
        "P_VPA": 0.6866,
        "EV_EBITDA": 3.2089,
        "EV_EBIT": 7.3011,
        "EV_RECEITA": 0.2695,
        "DY": 16.2619,
        "PAYOUT": 10860.6203,
        "ROE": 0.1093,
        "ROA": 0.0311,
        "ROIC": 7.083,
        "MARGEM_EBITDA": 8.3977,
        "MARGEM_LIQUIDA": 0.0244,
        "DIV_LIQ_EBITDA": 1.2672,
        "DIV_LIQ_PL": 0.4481,
        "ICJ": 0.5238,
        "COMPOSICAO_DIVIDA": 26.3103,
        "LIQ_CORRENTE": 1.3858,
        "LIQ_SECA": 0.4515,
        "LIQ_GERAL": 0.9248,
        "GIRO_ATIVO": 1.2463,
        "PME": 142.4465,
        "CICLO_CAIXA": 76.5129,
        "NCG_RECEITA": 11.0515
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1731030.21,
        "P_L": 16.782,
        "P_VPA": 0.6358,
        "EV_EBITDA": 1.8712,
        "EV_EBIT": 5.2206,
        "EV_RECEITA": 0.2372,
        "DY": 18.3678,
        "PAYOUT": 308.248,
        "ROE": 3.8324,
        "ROA": 1.1479,
        "ROIC": 9.5007,
        "MARGEM_EBITDA": 12.674,
        "MARGEM_LIQUIDA": 0.8159,
        "DIV_LIQ_EBITDA": 0.7908,
        "DIV_LIQ_PL": 0.4654,
        "ICJ": 0.7577,
        "COMPOSICAO_DIVIDA": 26.1054,
        "LIQ_CORRENTE": 1.3647,
        "LIQ_SECA": 0.3712,
        "LIQ_GERAL": 0.9619,
        "GIRO_ATIVO": 1.4072,
        "PME": 140.3701,
        "CICLO_CAIXA": 66.5612,
        "NCG_RECEITA": 11.4984
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 2148220.94,
        "P_L": 10.8474,
        "P_VPA": 0.7512,
        "EV_EBITDA": 2.101,
        "EV_EBIT": 4.9215,
        "EV_RECEITA": 0.2657,
        "DY": 14.8007,
        "PAYOUT": 160.5492,
        "ROE": 7.1617,
        "ROA": 2.2115,
        "ROIC": 11.2907,
        "MARGEM_EBITDA": 12.6451,
        "MARGEM_LIQUIDA": 1.3881,
        "DIV_LIQ_EBITDA": 0.9102,
        "DIV_LIQ_PL": 0.5742,
        "ICJ": 0.869,
        "COMPOSICAO_DIVIDA": 18.2816,
        "LIQ_CORRENTE": 1.5668,
        "LIQ_SECA": 0.5383,
        "LIQ_GERAL": 1.0078,
        "GIRO_ATIVO": 1.5394,
        "PME": 125.0949,
        "CICLO_CAIXA": 77.5764,
        "NCG_RECEITA": 14.5157
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T21:22:29.662423",
    "preco_utilizado": 6.36,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 622672736,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 3960198.6,
      "P_L": 19.997,
      "P_VPA": 1.3848,
      "EV_EBITDA": 3.1054,
      "EV_EBIT": 7.2744,
      "EV_RECEITA": 0.3927,
      "DY": 8.0287,
      "PAYOUT": 160.5492,
      "ROE": 7.1617,
      "ROA": 2.2115,
      "ROIC": 11.2907,
      "MARGEM_EBITDA": 12.6451,
      "MARGEM_LIQUIDA": 1.3881,
      "DIV_LIQ_EBITDA": 0.9102,
      "DIV_LIQ_PL": 0.5742,
      "ICJ": 0.869,
      "COMPOSICAO_DIVIDA": 18.2816,
      "LIQ_CORRENTE": 1.5668,
      "LIQ_SECA": 0.5383,
      "LIQ_GERAL": 1.0078,
      "GIRO_ATIVO": 1.5394,
      "PME": 125.0949,
      "CICLO_CAIXA": 77.5764,
      "NCG_RECEITA": 14.5157
    }
  },
  "periodos_disponiveis": [
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
