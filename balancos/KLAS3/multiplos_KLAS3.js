// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["KLAS3"] = {
  "ticker": "KLAS3",
  "ticker_preco": "KLAS3",
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
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 9.2076,
        "ROA": 3.577,
        "ROIC": 6.6076,
        "MARGEM_EBITDA": 19.4083,
        "MARGEM_LIQUIDA": 18.7073,
        "DIV_LIQ_EBITDA": -0.5322,
        "DIV_LIQ_PL": -0.0508,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": null,
        "LIQ_CORRENTE": 6.2178,
        "LIQ_SECA": 6.2178,
        "LIQ_GERAL": 1.4267,
        "GIRO_ATIVO": 0.1912,
        "PME": 0.0,
        "CICLO_CAIXA": 274.704,
        "NCG_RECEITA": 245.6584
      }
    },
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
        "ROE": 11.9271,
        "ROA": 5.9569,
        "ROIC": 6.122,
        "MARGEM_EBITDA": 18.2029,
        "MARGEM_LIQUIDA": 17.2547,
        "DIV_LIQ_EBITDA": 0.5547,
        "DIV_LIQ_PL": 0.0545,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 48.847,
        "LIQ_CORRENTE": 4.2514,
        "LIQ_SECA": 4.2514,
        "LIQ_GERAL": 2.2964,
        "GIRO_ATIVO": 0.3212,
        "PME": 0.0,
        "CICLO_CAIXA": 104.55,
        "NCG_RECEITA": 151.9516
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
        "ROE": 15.0124,
        "ROA": 8.5118,
        "ROIC": 8.4497,
        "MARGEM_EBITDA": 18.5954,
        "MARGEM_LIQUIDA": 18.0971,
        "DIV_LIQ_EBITDA": 0.891,
        "DIV_LIQ_PL": 0.13,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 12.1698,
        "LIQ_CORRENTE": 5.571,
        "LIQ_SECA": 5.571,
        "LIQ_GERAL": 2.0202,
        "GIRO_ATIVO": 0.427,
        "PME": 0.0,
        "CICLO_CAIXA": 82.0269,
        "NCG_RECEITA": 94.0277
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
        "ROE": 5.8571,
        "ROA": 3.0031,
        "ROIC": 5.1001,
        "MARGEM_EBITDA": 12.4776,
        "MARGEM_LIQUIDA": 7.1635,
        "DIV_LIQ_EBITDA": 2.4271,
        "DIV_LIQ_PL": 0.2476,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 50.2267,
        "LIQ_CORRENTE": 3.1901,
        "LIQ_SECA": 3.1901,
        "LIQ_GERAL": 1.7725,
        "GIRO_ATIVO": 0.3963,
        "PME": 0.0,
        "CICLO_CAIXA": 74.9829,
        "NCG_RECEITA": 118.6194
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
        "ROE": 8.9986,
        "ROA": 4.2878,
        "ROIC": 5.6075,
        "MARGEM_EBITDA": 11.6247,
        "MARGEM_LIQUIDA": 7.8382,
        "DIV_LIQ_EBITDA": 3.3781,
        "DIV_LIQ_PL": 0.4178,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 34.6184,
        "LIQ_CORRENTE": 2.9736,
        "LIQ_SECA": 2.9736,
        "LIQ_GERAL": 1.74,
        "GIRO_ATIVO": 0.4998,
        "PME": 0.0,
        "CICLO_CAIXA": 107.5169,
        "NCG_RECEITA": 94.0783
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
        "ROE": 6.4459,
        "ROA": 3.0044,
        "ROIC": 5.1985,
        "MARGEM_EBITDA": 8.4996,
        "MARGEM_LIQUIDA": 4.6786,
        "DIV_LIQ_EBITDA": 3.9433,
        "DIV_LIQ_PL": 0.4746,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 20.9824,
        "LIQ_CORRENTE": 4.1369,
        "LIQ_SECA": 4.1369,
        "LIQ_GERAL": 1.7371,
        "GIRO_ATIVO": 0.6546,
        "PME": 0.0,
        "CICLO_CAIXA": 130.6611,
        "NCG_RECEITA": 75.316
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
        "ROE": -8.5785,
        "ROA": -3.8995,
        "ROIC": -2.114,
        "MARGEM_EBITDA": -3.6319,
        "MARGEM_LIQUIDA": -8.066,
        "DIV_LIQ_EBITDA": -13.8287,
        "DIV_LIQ_PL": 0.5302,
        "ICJ": -6.7346,
        "COMPOSICAO_DIVIDA": 36.7146,
        "LIQ_CORRENTE": 3.3091,
        "LIQ_SECA": 3.3091,
        "LIQ_GERAL": 1.7133,
        "GIRO_ATIVO": 0.4753,
        "PME": 0.0,
        "CICLO_CAIXA": 179.7439,
        "NCG_RECEITA": 115.9409
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T10:32:17.772988",
    "preco_utilizado": null,
    "periodo_preco": "",
    "acoes_utilizadas": 135602,
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
      "ROE": -8.5785,
      "ROA": -3.8995,
      "ROIC": -2.114,
      "MARGEM_EBITDA": -3.6319,
      "MARGEM_LIQUIDA": -8.066,
      "DIV_LIQ_EBITDA": -13.8287,
      "DIV_LIQ_PL": 0.5302,
      "ICJ": -6.7346,
      "COMPOSICAO_DIVIDA": 36.7146,
      "LIQ_CORRENTE": 3.3091,
      "LIQ_SECA": 3.3091,
      "LIQ_GERAL": 1.7133,
      "GIRO_ATIVO": 0.4753,
      "PME": 0.0,
      "CICLO_CAIXA": 179.7439,
      "NCG_RECEITA": 115.9409
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
