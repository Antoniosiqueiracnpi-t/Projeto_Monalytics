import pandas as pd
import requests
import locale
from datetime import datetime
import re
from pathlib import Path
import json

# ==========================
# UTILITÁRIOS
# ==========================

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    pass


def extrair_numero(valor):
    """Extrai número de uma string."""
    if pd.isna(valor):
        return 0
    valor_str = str(valor).strip()
    if not valor_str or valor_str.lower() in ['', 'nan', 'none', '-']:
        return 0
    valor_limpo = re.sub(r'[^\d\.\,\-\+]', '', valor_str)
    if ',' in valor_limpo and '.' in valor_limpo:
        valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
    elif ',' in valor_limpo:
        valor_limpo = valor_limpo.replace(',', '.')
    try:
        return float(valor_limpo)
    except:
        return 0


def baixar_dados_b3():
    """Baixa dados da B3 (Dados de Mercado)."""
    url = (
        "https://sistemaswebb3-listados.b3.com.br/marketDataProxy/"
        "MarketDataCall/GetDownloadMarketData/RELATORIO_DADOS_DE_MERCADO.csv"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.text
        print(f"⚠️ Erro HTTP ao baixar CSV: {resp.status_code}")
    except Exception as e:
        print(f"❌ Erro de conexão ao baixar CSV: {e}")
    return None


def processar_csv_b3(texto_csv):
    """Processa CSV da B3 com robustez para mudanças de layout."""
    linhas = texto_csv.strip().split("\n")
    dados_mensais = []

    print("🔍 Procurando seção de estrangeiros...")

    # Múltiplos padrões para localizar seção (case-insensitive)
    padroes_secao = [
        "movimentação dos investidores estrangeiros",
        "movimenta",  # Aceita fragmentos
        "estrangeiros mensal",
        "foreign investors",
    ]

    inicio_secao = -1
    for i, linha in enumerate(linhas):
        linha_lower = linha.lower().replace("á", "a").replace("ç", "c")
        for padrao in padroes_secao:
            if padrao in linha_lower:
                print(f"✅ Seção encontrada na linha {i}: {linha[:100]}...")
                inicio_secao = i + 2  # Pula header + linha vazia
                break
        if inicio_secao != -1:
            break

    if inicio_secao == -1:
        print("❌ NENHUMA seção de estrangeiros encontrada. Primeiras linhas:")
        for i, l in enumerate(linhas[:20]):
            print(f"  {i}: {l[:80]}...")
        return None

    print(f"📊 Processando {len(linhas) - inicio_secao} linhas de dados...")

    for idx, linha in enumerate(linhas[inicio_secao:], inicio_secao):
        if not linha.strip() or len(linha.split(";")) < 5:
            continue

        # Parar se nova seção (participação, volumes, etc.)
        linha_lower = linha.lower()
        if any(p in linha_lower for p in ["participação", "número", "volume", "total"]):
            print(f"⏹️ Fim da seção detectado na linha {idx}")
            break

        campos = [c.strip() for c in linha.split(";")]
        if len(campos) < 5:
            continue

        periodo_raw = campos[0]

        # Pular totais anuais/linhas inválidas
        if (periodo_raw.isdigit() or 
            "(*)" in periodo_raw or 
            len(periodo_raw) < 3 or 
            not re.search(r"(20\d{2})", periodo_raw)):
            continue

        # Normalizar período (Jan/Jan/2025 -> Jan/2025)
        periodo = re.sub(r'/\w+/', '/', periodo_raw)  # Remove mês duplicado
        if '/' not in periodo:
            mes_map = {'jan': 'Jan', 'fev': 'Fev', 'mar': 'Mar', 'abr': 'Abr', 
                      'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug', 
                      'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'}
            for pt, en in mes_map.items():
                periodo = periodo.replace(pt, en)

        ano_match = re.search(r"(20\d{2})", periodo)
        if not ano_match:
            continue

        ano = int(ano_match.group(1))
        compra = extrair_numero(campos[1])
        venda = extrair_numero(campos[2])
        ipo = extrair_numero(campos[3])
        saldo = extrair_numero(campos[4])

        dados_mensais.append({
            'periodo': periodo,
            'ano': ano,
            'compra_milhoes': compra,
            'venda_milhoes': venda,
            'ipo_follow_on_milhoes': ipo,
            'saldo_milhoes': saldo,
            'volume_total_milhoes': compra + venda + ipo,
        })

        # Debug: mostrar primeira linha processada
        if len(dados_mensais) == 1:
            print(f"📋 Exemplo processado: {periodo} | Saldo: R${saldo:,.1f}M")

    if not dados_mensais:
        print("❌ Nenhum dado válido processado.")
        return None

    print(f"✅ {len(dados_mensais)} registros extraídos!")

    # Resto da função igual (agregações, resumo)...
    df = pd.DataFrame(dados_mensais).sort_values(["ano"]).reset_index(drop=True)
    
    # ... (manter df_anual, resumo, etc. como no código original)
    
    return {
        'movimentacao_estrangeiros_mensal': df,
        'movimentacao_estrangeiros_anual': df_anual,  # Manter cálculo
        'participacao_investidores': pd.DataFrame(participacao),
        'volume_negociacao': pd.DataFrame([volumes]),
        'resumo_executivo': pd.DataFrame([resumo]),
    }



def salvar_jsons_b3(dados):
    """Salva saídas em JSON para uso na página HTML."""
    base_dir = Path("site/data")
    base_dir.mkdir(parents=True, exist_ok=True)

    # 1) Mensal
    dados["movimentacao_estrangeiros_mensal"].to_json(
        base_dir / "b3_fluxo_estrangeiro_mensal.json",
        orient="records",
        force_ascii=False,
        indent=2,
    )

    # 2) Anual
    dados["movimentacao_estrangeiros_anual"].to_json(
        base_dir / "b3_fluxo_estrangeiro_anual.json",
        orient="records",
        force_ascii=False,
        indent=2,
    )

    # 3) Participação
    dados["participacao_investidores"].to_json(
        base_dir / "b3_participacao_investidores.json",
        orient="records",
        force_ascii=False,
        indent=2,
    )

    # 4) Volume negociação
    dados["volume_negociacao"].to_json(
        base_dir / "b3_volume_negociacao.json",
        orient="records",
        force_ascii=False,
        indent=2,
    )

    # 5) Resumo executivo (single record)
    dados["resumo_executivo"].to_json(
        base_dir / "b3_fluxo_resumo.json",
        orient="records",
        force_ascii=False,
        indent=2,
    )

    print(f"✅ JSONs atualizados em {base_dir}")


def executar_coleta_diaria():
    """Pipeline simples: baixa, processa e salva JSON."""
    print("📥 Coletando dados da B3...")

    texto_csv = baixar_dados_b3()
    if not texto_csv:
        print("❌ Erro: Não foi possível baixar dados")
        return False

    dados = processar_csv_b3(texto_csv)
    if not dados:
        print("❌ Erro: Não foi possível processar dados")
        return False

    df = dados["movimentacao_estrangeiros_mensal"]
    ultimo = df.iloc[-1]

    print(f"✅ Sucesso! Último período: {ultimo['periodo']}")
    print(f"📈 Registros: {len(df)}")
    print(f"💰 Último saldo: R$ {ultimo['saldo_milhoes']:,.1f} milhões")

    salvar_jsons_b3(dados)
    return True


if __name__ == "__main__":
    executar_coleta_diaria()
