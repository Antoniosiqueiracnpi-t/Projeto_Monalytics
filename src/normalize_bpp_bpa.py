#!/usr/bin/env python3
"""
NORMALIZE_BPP_BPA.PY - VERSÃO DEFINITIVA
=========================================
PROCESSA APENAS BPA e BPP - NÃO TOCA EM DRE/DFC

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
sys.path.insert(0, str(REPO_ROOT))

from padronizar_bpa_bpp import padronizar_bpa_trimestral_e_anual, padronizar_bpp_trimestral_e_anual

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


def _classify_balanco(df: pd.DataFrame) -> Optional[str]:
    """Classifica se é BPA (códigos 1.x) ou BPP (códigos 2.x)"""
    if df is None or "cd_conta" not in df.columns:
        return None
    s = df["cd_conta"].astype(str).str.strip()
    n1 = (s.str.startswith("1").sum())
    n2 = (s.str.startswith("2").sum())
    if n1 == 0 and n2 == 0:
        return None
    return "bpa" if n1 >= n2 else "bpp"


def _find_balanco_files(ticker_dir: Path, tipo: str) -> dict:
    """
    Encontra arquivos BPA ou BPP na pasta do ticker.
    tipo: "bpa" ou "bpp"
    """
    result = {"trimestral": None, "anual": None}
    
    # Prioridade 1: Nomes padrão
    for name, key in [(f"{tipo}_consolidado.csv", "trimestral"), (f"{tipo}_anual.csv", "anual")]:
        path = ticker_dir / name
        if path.exists():
            result[key] = path
    
    # Prioridade 2: Nomes alternativos
    if result["trimestral"] is None:
        for alt in [f"{tipo}_trimestral.csv", f"{tipo}_itr.csv"]:
            path = ticker_dir / alt
            if path.exists():
                result["trimestral"] = path
                break
    
    if result["anual"] is None:
        for alt in [f"{tipo}_dfp.csv"]:
            path = ticker_dir / alt
            if path.exists():
                result["anual"] = path
                break
    
    # Prioridade 3: Fallback por conteúdo
    if result["trimestral"] is None or result["anual"] is None:
        for csv_file in ticker_dir.glob("*.csv"):
            if "_padronizada" in csv_file.name.lower():
                continue
            if tipo not in csv_file.name.lower():
                continue
            
            dfh = _safe_read_head(csv_file)
            if dfh is None or not REQUIRED_COLS.issubset(set(dfh.columns)):
                continue
            
            classificacao = _classify_balanco(dfh)
            if classificacao != tipo:
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


def processar_bpa_ticker(ticker_dir: Path, b3_map: Optional[str] = None) -> bool:
    """Processa BPA de um único ticker."""
    ticker = ticker_dir.name.upper()
    
    files = _find_balanco_files(ticker_dir, "bpa")
    
    if not files["trimestral"]:
        print(f"[{ticker}] ⚠ BPA trimestral não encontrado")
        return False
    
    if not files["anual"]:
        print(f"[{ticker}] ⚠ BPA anual não encontrado")
        return False
    
    try:
        out_bpa = padronizar_bpa_trimestral_e_anual(
            str(files["trimestral"]),
            str(files["anual"]),
            ticker=ticker,
            b3_mapping_csv=b3_map,
        )
        
        out_path = ticker_dir / "bpa_padronizada.csv"
        out_bpa.to_csv(out_path, index=False)
        print(f"[{ticker}] ✅ BPA padronizada")
        return True
        
    except Exception as e:
        print(f"[{ticker}] ❌ BPA Erro: {e}")
        traceback.print_exc()
        return False


def processar_bpp_ticker(ticker_dir: Path, b3_map: Optional[str] = None) -> bool:
    """Processa BPP de um único ticker."""
    ticker = ticker_dir.name.upper()
    
    files = _find_balanco_files(ticker_dir, "bpp")
    
    if not files["trimestral"]:
        print(f"[{ticker}] ⚠ BPP trimestral não encontrado")
        return False
    
    if not files["anual"]:
        print(f"[{ticker}] ⚠ BPP anual não encontrado")
        return False
    
    try:
        out_bpp = padronizar_bpp_trimestral_e_anual(
            str(files["trimestral"]),
            str(files["anual"]),
            ticker=ticker,
            b3_mapping_csv=b3_map,
        )
        
        out_path = ticker_dir / "bpp_padronizada.csv"
        out_bpp.to_csv(out_path, index=False)
        print(f"[{ticker}] ✅ BPP padronizada")
        return True
        
    except Exception as e:
        print(f"[{ticker}] ❌ BPP Erro: {e}")
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Normalizar BPA e BPP - APENAS BALANÇOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python normalize_bpp_bpa.py --modo ticker --ticker PETR4
  python normalize_bpp_bpa.py --modo lista --lista PETR4,VALE3,ITUB4
  python normalize_bpp_bpa.py --modo faixa --faixa 1-10
  python normalize_bpp_bpa.py --modo quantidade --quantidade 5
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
    print("NORMALIZAÇÃO BPA/BPP - VERSÃO DEFINITIVA")
    print("=" * 60)
    print(f"Modo: {args.modo}")
    print()
    
    # Localizar pasta balancos
    base = REPO_ROOT / "balancos"
    if not base.exists():
        print(f"[ERRO] Pasta balancos/ não existe em {REPO_ROOT}")
        sys.exit(1)
    
    # Carregar mapeamento B3 (opcional)
    b3_map_path = REPO_ROOT / "mapeamento_final_b3_completo_utf8.csv"
    b3_map = str(b3_map_path) if b3_map_path.exists() else None
    
    if b3_map:
        print(f"✓ Mapeamento B3: {b3_map_path.name}")
    else:
        print("⚠ Mapeamento B3 não encontrado")
    
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
    print("PROCESSANDO BPA e BPP")
    print("-" * 60)
    
    # Processar
    bpa_ok = 0
    bpa_err = 0
    bpp_ok = 0
    bpp_err = 0
    
    for ticker_dir in tickers:
        # BPA
        if processar_bpa_ticker(ticker_dir, b3_map):
            bpa_ok += 1
        else:
            bpa_err += 1
        
        # BPP
        if processar_bpp_ticker(ticker_dir, b3_map):
            bpp_ok += 1
        else:
            bpp_err += 1
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"BPA: ✅ {bpa_ok} | ❌ {bpa_err}")
    print(f"BPP: ✅ {bpp_ok} | ❌ {bpp_err}")
    print(f"📊 Total tickers: {len(tickers)}")
    
    if (bpa_err + bpp_err) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
