#!/usr/bin/env python3
"""
NORMALIZE DRE - SCRIPT INDEPENDENTE
====================================
APENAS DRE - NÃO PROCESSA BPA/BPP/DFC

Modos de execução:
  python src/normalize_dre.py --modo ticker --ticker AGRO3
  python src/normalize_dre.py --modo lista --lista AGRO3,PETR4,VALE3
  python src/normalize_dre.py --modo quantidade --quantidade 10
  python src/normalize_dre.py --modo faixa --faixa 1-50
"""

from pathlib import Path
import sys
import traceback
import argparse
from typing import Optional, List, Dict

import pandas as pd

# Garante import da raiz do repo
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# IMPORTA APENAS A FUNÇÃO DE DRE - NENHUMA OUTRA
from padronizar_dre_trimestral_e_anual import padronizar_dre_trimestral_e_anual

REQUIRED_COLS = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}


def _sniff_sep(path: Path) -> str:
    """Detecta separador do CSV"""
    try:
        sample = path.read_text(encoding="utf-8", errors="replace")[:4096]
        return ";" if sample.count(";") > sample.count(",") else ","
    except Exception:
        return ","


def _safe_read_head(path: Path, nrows: int = 200) -> Optional[pd.DataFrame]:
    """Lê cabeçalho do CSV com segurança"""
    sep = _sniff_sep(path)
    try:
        return pd.read_csv(path, sep=sep, nrows=nrows, encoding="utf-8", engine="python")
    except Exception:
        return None


def _is_dre(df: pd.DataFrame) -> bool:
    """Verifica se arquivo é DRE (contas começando com 3)"""
    if df is None or "cd_conta" not in df.columns:
        return False
    s = df["cd_conta"].astype(str).str.strip()
    return s.str.startswith("3").sum() > 0


def _score_periodicity(df: pd.DataFrame, path: Path, want: str) -> float:
    """Pontua se arquivo é trimestral ou anual"""
    name = path.name.lower()
    bonus = 0.0

    if want == "trimestral":
        if "itr" in name or "consolid" in name:
            bonus += 0.35
        if "trimes" in name:
            bonus += 0.25
    else:
        if "dfp" in name:
            bonus += 0.35
        if "anual" in name:
            bonus += 0.25

    # Evita outputs já gerados
    if "padron" in name or "normaliz" in name:
        bonus -= 0.50

    tri_score = 0.0
    anu_score = 0.0

    if "trimestre" in df.columns:
        t = df["trimestre"].astype(str).str.upper().str.strip()
        if len(t) > 0:
            tri_score += float(t.isin(["T1", "T2", "T3"]).mean())
            anu_score += float((t == "T4").mean())

    if "data_fim" in df.columns:
        dt = pd.to_datetime(df["data_fim"], errors="coerce")
        m = dt.dt.month.dropna()
        if not m.empty:
            tri_score += float(m.isin([3, 6, 9]).mean())
            anu_score += float((m == 12).mean())

    return (tri_score + bonus) if want == "trimestral" else (anu_score + bonus)


def _discover_dre_files(ticker_dir: Path) -> Dict[str, Optional[Path]]:
    """Descobre arquivos DRE na pasta (fallback)"""
    out = {"trimestral": None, "anual": None}

    files = [p for p in ticker_dir.rglob("*.csv") if p.is_file()]
    files = [p for p in files if not p.name.lower().endswith("_padronizada.csv")]

    tri_candidates = []
    anu_candidates = []

    for f in files:
        dfh = _safe_read_head(f)
        if dfh is None:
            continue
        if not REQUIRED_COLS.issubset(set(dfh.columns)):
            continue
        if not _is_dre(dfh):
            continue

        tri_candidates.append((_score_periodicity(dfh, f, "trimestral"), f))
        anu_candidates.append((_score_periodicity(dfh, f, "anual"), f))

    tri_candidates.sort(key=lambda x: x[0], reverse=True)
    anu_candidates.sort(key=lambda x: x[0], reverse=True)

    out["trimestral"] = tri_candidates[0][1] if tri_candidates and tri_candidates[0][0] > 0 else None
    out["anual"] = anu_candidates[0][1] if anu_candidates and anu_candidates[0][0] > 0 else None

    # Evita mesmo arquivo para ambos
    if out["trimestral"] and out["anual"] and out["trimestral"].resolve() == out["anual"].resolve():
        if len(anu_candidates) > 1 and anu_candidates[1][0] > 0:
            out["anual"] = anu_candidates[1][1]

    return out


def _pick_original_named_dre(tdir: Path) -> Dict[str, Optional[Path]]:
    """Tenta pegar arquivos com nomes padrão"""
    tri = tdir / "dre_trimestral.csv"
    anu = tdir / "dre_anual.csv"
    
    # Fallback para nomes alternativos
    if not tri.exists():
        tri = tdir / "dre_consolidado.csv"
    
    return {
        "trimestral": tri if tri.exists() else None,
        "anual": anu if anu.exists() else None,
    }


def _filtrar_tickers(
    all_tickers: List[Path], 
    modo: str, 
    quantidade: str, 
    ticker: str, 
    lista: str, 
    faixa: str
) -> List[Path]:
    """Filtra lista de tickers baseado no modo"""
    
    if modo == "ticker":
        if not ticker:
            print("[ERRO] Modo 'ticker' requer --ticker especificado")
            return []
        ticker_upper = ticker.strip().upper()
        result = [t for t in all_tickers if t.name.upper() == ticker_upper]
        if not result:
            print(f"[ERRO] Ticker '{ticker_upper}' não encontrado em balancos/")
        return result
    
    elif modo == "lista":
        if not lista:
            print("[ERRO] Modo 'lista' requer --lista especificado")
            return []
        tickers_list = [t.strip().upper() for t in lista.split(",") if t.strip()]
        result = [t for t in all_tickers if t.name.upper() in tickers_list]
        if not result:
            print(f"[ERRO] Nenhum ticker da lista encontrado")
        return result
    
    elif modo == "quantidade":
        try:
            n = int(quantidade) if quantidade else 10
            return all_tickers[:n]
        except ValueError:
            print(f"[AVISO] Quantidade inválida '{quantidade}', usando 10")
            return all_tickers[:10]
    
    elif modo == "faixa":
        if not faixa or "-" not in faixa:
            print(f"[AVISO] Faixa inválida '{faixa}', usando 1-50")
            start, end = 1, 50
        else:
            try:
                parts = faixa.split("-")
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except (ValueError, IndexError):
                print(f"[AVISO] Faixa inválida '{faixa}', usando 1-50")
                start, end = 1, 50
        
        start_idx = max(0, start - 1)
        return all_tickers[start_idx:end]
    
    else:
        return all_tickers


def processar_ticker(tdir: Path, b3_map: Optional[str]) -> Optional[str]:
    """
    Processa UM ticker - APENAS DRE
    
    Returns:
        Caminho do arquivo gerado ou None se falhou
    """
    ticker = tdir.name.upper().strip()
    
    # Tenta nomes padrão primeiro
    original = _pick_original_named_dre(tdir)
    
    # Fallback se não encontrou
    if original["trimestral"] is None or original["anual"] is None:
        fallback = _discover_dre_files(tdir)
        dre_tri = original["trimestral"] or fallback["trimestral"]
        dre_anu = original["anual"] or fallback["anual"]
    else:
        dre_tri = original["trimestral"]
        dre_anu = original["anual"]
    
    if not dre_tri or not dre_anu:
        print(f"[{ticker}] DRE: arquivos não encontrados. Pulando.")
        return None
    
    # Executa padronização - APENAS DRE
    out_dre = padronizar_dre_trimestral_e_anual(
        str(dre_tri),
        str(dre_anu),
        ticker=ticker,
        b3_mapping_csv=b3_map,
    )
    
    out_path = tdir / "dre_padronizada.csv"
    out_dre.to_csv(out_path, index=False)
    
    return str(out_path)


def main():
    parser = argparse.ArgumentParser(
        description="Normalizar DRE - APENAS DRE, independente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python src/normalize_dre.py --modo ticker --ticker AGRO3
  python src/normalize_dre.py --modo lista --lista AGRO3,PETR4,VALE3
  python src/normalize_dre.py --modo quantidade --quantidade 10
  python src/normalize_dre.py --modo faixa --faixa 1-50
        """
    )
    parser.add_argument("--modo", default="quantidade", 
                       choices=["quantidade", "ticker", "lista", "faixa"],
                       help="Modo de seleção de tickers")
    parser.add_argument("--quantidade", default="10",
                       help="Quantidade de tickers (modo quantidade)")
    parser.add_argument("--ticker", default="",
                       help="Ticker único (modo ticker)")
    parser.add_argument("--lista", default="",
                       help="Lista de tickers separados por vírgula (modo lista)")
    parser.add_argument("--faixa", default="1-50",
                       help="Faixa de tickers (modo faixa)")
    
    args = parser.parse_args()

    base = REPO_ROOT / "balancos"
    if not base.exists():
        print("[ERRO] Pasta balancos/ não existe.")
        return 1

    b3_map_path = REPO_ROOT / "mapeamento_final_b3_completo_utf8.csv"
    b3_map = str(b3_map_path) if b3_map_path.exists() else None

    all_tickers = sorted([p for p in base.iterdir() if p.is_dir()])
    print(f"Total de {len(all_tickers)} pastas de empresas encontradas.")

    # Filtra tickers
    tickers = _filtrar_tickers(
        all_tickers, 
        args.modo, 
        args.quantidade, 
        args.ticker, 
        args.lista, 
        args.faixa
    )
    
    if not tickers:
        print("[ERRO] Nenhum ticker selecionado para processar.")
        return 1
    
    print(f"Processando {len(tickers)} ticker(s) - APENAS DRE (modo: {args.modo})")
    print("-" * 60)

    gerados = []
    erros = 0

    for tdir in tickers:
        ticker = tdir.name.upper()
        try:
            resultado = processar_ticker(tdir, b3_map)
            
            if resultado:
                gerados.append(resultado)
                print(f"[OK] {ticker}")
            else:
                print(f"[SKIP] {ticker}")
                
        except Exception as e:
            erros += 1
            print(f"[ERRO] {ticker}: {e}")
            traceback.print_exc()

    print("-" * 60)
    print(f"\n{'='*20} RESUMO DRE {'='*20}")
    print(f"Processados: {len(tickers)}")
    print(f"Gerados: {len(gerados)}")
    print(f"Erros: {erros}")
    
    if gerados:
        print("\nArquivos gerados:")
        for p in gerados:
            print(f"  - {p}")

    return 0 if erros == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
