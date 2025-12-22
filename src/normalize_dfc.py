#!/usr/bin/env python3
"""
NORMALIZE_DFC.PY - VERSÃO DEFINITIVA
=====================================
PROCESSA APENAS DFC - NÃO TOCA EM DRE/BPA/BPP

Modos de execução:
  --modo ticker --ticker PETR4     → Processa apenas PETR4
  --modo lista --lista PETR4,VALE3 → Processa lista específica
  --modo faixa --faixa 1-10        → Processa faixa de índices
  --modo quantidade --quantidade 5 → Processa N primeiras (CUIDADO)

SEM ARGUMENTOS: NÃO PROCESSA NADA (segurança)
"""

from pathlib import Path
import sys
import traceback
import argparse
from typing import Optional, List

import pandas as pd

# Garantir import da raiz do repo
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

sys.path.insert(0, str(REPO_ROOT))
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

# Importar função de padronização
try:
    from padronizar_dfc_mi import padronizar_dfc_mi_trimestral_e_anual
except ImportError:
    padronizar_dfc_mi_trimestral_e_anual = None


REQUIRED_COLS = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}


def _sniff_sep(path: Path) -> str:
    """Detecta separador do CSV"""
    try:
        sample = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except Exception:
        return ","
    return ";" if sample.count(";") > sample.count(",") else ","


def _safe_read_head(path: Path, nrows: int = 200) -> Optional[pd.DataFrame]:
    """Lê cabeçalho do arquivo de forma segura"""
    sep = _sniff_sep(path)
    try:
        return pd.read_csv(path, sep=sep, nrows=nrows, encoding="utf-8", engine="python")
    except Exception:
        return None


def _is_dfc(df: pd.DataFrame) -> bool:
    """Verifica se é arquivo DFC (códigos começam com 6)"""
    if df is None or "cd_conta" not in df.columns:
        return False
    s = df["cd_conta"].astype(str).str.strip()
    return (s.str.startswith("6").sum()) > 0


def _find_dfc_files(ticker_dir: Path) -> dict:
    """
    Encontra arquivos DFC na pasta do ticker.
    Prioriza nomes padrão, depois faz fallback por conteúdo.
    """
    result = {"trimestral": None, "anual": None}
    
    # Prioridade 1: Nomes padrão
    for name, key in [("dfc_mi_consolidado.csv", "trimestral"), ("dfc_mi_anual.csv", "anual")]:
        path = ticker_dir / name
        if path.exists():
            result[key] = path
    
    # Prioridade 2: Nomes alternativos
    if result["trimestral"] is None:
        for alt in ["dfc_consolidado.csv", "dfc_trimestral.csv", "dfc_mi_trimestral.csv", "dfc_itr.csv"]:
            path = ticker_dir / alt
            if path.exists():
                result["trimestral"] = path
                break
    
    if result["anual"] is None:
        for alt in ["dfc_anual.csv", "dfc_dfp.csv"]:
            path = ticker_dir / alt
            if path.exists():
                result["anual"] = path
                break
    
    # Prioridade 3: Fallback por conteúdo
    if result["trimestral"] is None or result["anual"] is None:
        for csv_file in ticker_dir.glob("*.csv"):
            if "_padronizada" in csv_file.name.lower():
                continue
            if "dfc" not in csv_file.name.lower():
                continue
            
            dfh = _safe_read_head(csv_file)
            if dfh is None or not REQUIRED_COLS.issubset(set(dfh.columns)):
                continue
            if not _is_dfc(dfh):
                continue
            
            name_lower = csv_file.name.lower()
            if "anual" in name_lower or "dfp" in name_lower:
                if result["anual"] is None:
                    result["anual"] = csv_file
            else:
                if result["trimestral"] is None:
                    result["trimestral"] = csv_file
    
    return result


def _filtrar_tickers(all_tickers: List[Path], args) -> List[Path]:
    """
    Filtra tickers baseado nos argumentos.
    IMPORTANTE: Sem argumentos específicos, retorna lista VAZIA (segurança)
    """
    modo = args.modo
    
    if modo == "ticker":
        if not args.ticker:
            print("[ERRO] --ticker não especificado!")
            return []
        ticker_upper = args.ticker.strip().upper()
        result = [t for t in all_tickers if t.name.upper() == ticker_upper]
        if not result:
            print(f"[ERRO] Ticker '{ticker_upper}' não encontrado em balancos/")
        return result
    
    elif modo == "lista":
        if not args.lista:
            print("[ERRO] --lista não especificada!")
            return []
        tickers_list = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        result = [t for t in all_tickers if t.name.upper() in tickers_list]
        nao_encontrados = set(tickers_list) - {t.name.upper() for t in result}
        if nao_encontrados:
            print(f"[AVISO] Tickers não encontrados: {nao_encontrados}")
        return result
    
    elif modo == "faixa":
        if not args.faixa or "-" not in args.faixa:
            print(f"[ERRO] Faixa inválida: '{args.faixa}'")
            return []
        try:
            parts = args.faixa.split("-")
            start = int(parts[0].strip())
            end = int(parts[1].strip())
            start_idx = max(0, start - 1)
            return all_tickers[start_idx:end]
        except (ValueError, IndexError):
            print(f"[ERRO] Faixa inválida: '{args.faixa}'")
            return []
    
    elif modo == "quantidade":
        try:
            n = int(args.quantidade) if args.quantidade else 0
            if n <= 0:
                print("[ERRO] Quantidade deve ser > 0")
                return []
            return all_tickers[:n]
        except ValueError:
            print(f"[ERRO] Quantidade inválida: '{args.quantidade}'")
            return []
    
    else:
        print(f"[ERRO] Modo desconhecido: '{modo}'")
        return []


def processar_dfc_ticker(ticker_dir: Path) -> bool:
    """Processa DFC de um único ticker."""
    ticker = ticker_dir.name.upper()
    
    if padronizar_dfc_mi_trimestral_e_anual is None:
        print(f"[{ticker}] ❌ Função padronizar_dfc_mi_trimestral_e_anual não disponível")
        return False
    
    files = _find_dfc_files(ticker_dir)
    
    if not files["trimestral"]:
        print(f"[{ticker}] ⚠ DFC trimestral não encontrado")
        return False
    
    if not files["anual"]:
        print(f"[{ticker}] ⚠ DFC anual não encontrado")
        return False
    
    try:
        out_dfc = padronizar_dfc_mi_trimestral_e_anual(
            str(files["trimestral"]),
            str(files["anual"]),
            unidade="mil",
            permitir_rollup_descendentes=True,
        )
        
        out_path = ticker_dir / "dfc_padronizada.csv"
        out_dfc.to_csv(out_path, index=False)
        print(f"[{ticker}] ✅ DFC padronizada")
        return True
        
    except Exception as e:
        print(f"[{ticker}] ❌ DFC Erro: {e}")
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Normalizar DFC - APENAS DFC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python normalize_dfc.py --modo ticker --ticker PETR4
  python normalize_dfc.py --modo lista --lista PETR4,VALE3,ITUB4
  python normalize_dfc.py --modo faixa --faixa 1-10
  python normalize_dfc.py --modo quantidade --quantidade 5
        """
    )
    parser.add_argument("--modo", required=True, 
                        choices=["quantidade", "ticker", "lista", "faixa"],
                        help="Modo de seleção de tickers")
    parser.add_argument("--quantidade", default="0",
                        help="Quantidade de tickers (modo quantidade)")
    parser.add_argument("--ticker", default="",
                        help="Ticker único (modo ticker)")
    parser.add_argument("--lista", default="",
                        help="Lista de tickers separados por vírgula (modo lista)")
    parser.add_argument("--faixa", default="",
                        help="Faixa de índices: 1-10 (modo faixa)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("NORMALIZAÇÃO DFC - VERSÃO DEFINITIVA")
    print("=" * 60)
    print(f"Modo: {args.modo}")
    print()
    
    if padronizar_dfc_mi_trimestral_e_anual is None:
        print("[ERRO FATAL] padronizar_dfc_mi.py não encontrado!")
        print("             Verifique se o arquivo existe na raiz do repo ou em src/")
        sys.exit(1)
    
    # Localizar pasta balancos
    base = REPO_ROOT / "balancos"
    if not base.exists():
        print(f"[ERRO] Pasta balancos/ não existe em {REPO_ROOT}")
        sys.exit(1)
    
    # Listar todos os tickers disponíveis
    all_tickers = sorted([p for p in base.iterdir() if p.is_dir()])
    print(f"✓ Total de pastas em balancos/: {len(all_tickers)}")
    
    # Filtrar tickers conforme argumentos
    tickers = _filtrar_tickers(all_tickers, args)
    
    if not tickers:
        print("\n[!] Nenhum ticker selecionado para processamento.")
        print("    Use --help para ver exemplos de uso.")
        sys.exit(0)
    
    print(f"\n→ Selecionados para processamento: {len(tickers)} ticker(s)")
    for t in tickers[:10]:
        print(f"   - {t.name}")
    if len(tickers) > 10:
        print(f"   ... e mais {len(tickers) - 10}")
    
    print("\n" + "-" * 60)
    print("PROCESSANDO DFC")
    print("-" * 60)
    
    # Processar
    sucesso = 0
    erros = 0
    
    for ticker_dir in tickers:
        if processar_dfc_ticker(ticker_dir):
            sucesso += 1
        else:
            erros += 1
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"✅ Sucesso: {sucesso}")
    print(f"❌ Erros:   {erros}")
    print(f"📊 Total:   {len(tickers)}")
    
    if erros > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
