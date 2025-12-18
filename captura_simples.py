#!/usr/bin/env python3
"""
Captura balanços da B3/CVM com sistema de seleção de tickers.
Segue a ordem do arquivo mapeamento_final_b3_completo_utf8.csv

PATCH CIRÚRGICO:
- Garante que REPO_ROOT e REPO_ROOT/src estão no sys.path
- Tenta importar captura_balancos_b3 (se existir). Se não, faz fallback para subprocess
- Localiza mapeamento tanto na raiz quanto em src/
"""

import sys
import os
import argparse
import subprocess
import importlib
import inspect
from pathlib import Path
from typing import List, Optional

import pandas as pd


# ------------------ Repo root robusto ------------------
def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(6):
        if (cur / "balancos").exists() or (cur / ".github").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    # fallback: 1 nível acima do src/ (se existir)
    if (start.parent / "balancos").exists():
        return start.parent
    return start.parent


HERE = Path(__file__).resolve()
REPO_ROOT = _find_repo_root(HERE.parent)
SRC_DIR = REPO_ROOT / "src"

# Garante imports
sys.path.insert(0, str(REPO_ROOT))
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))


# ------------------ Leitura do CSV na ordem ------------------
def carregar_tickers_ordenados(csv_path: Path) -> List[str]:
    """
    Carrega os tickers na ordem exata em que aparecem no CSV de mapeamento.
    """
    possible_paths = [
        csv_path,                          # caminho passado
        REPO_ROOT / csv_path.name,         # raiz do repo
        SRC_DIR / csv_path.name,           # src/
        Path.cwd() / csv_path.name,        # diretório atual
        Path(os.environ.get("GITHUB_WORKSPACE", ".")) / csv_path.name,  # actions
        Path(os.environ.get("GITHUB_WORKSPACE", ".")) / "src" / csv_path.name,
    ]

    csv_file: Optional[Path] = None
    for path in possible_paths:
        if path.exists():
            csv_file = path
            break

    if csv_file is None:
        print("[AVISO] Arquivo de mapeamento não encontrado")
        print("        Procurado em:")
        for p in possible_paths:
            print(f"        - {p}")
        return []

    try:
        df = pd.read_csv(csv_file, sep=";", encoding="utf-8")
        if "ticker" not in df.columns:
            print("[AVISO] Coluna 'ticker' não encontrada no CSV de mapeamento")
            return []

        tickers = df["ticker"].dropna().astype(str).str.strip().str.upper()

        # Remove duplicatas mantendo ordem (primeira ocorrência)
        seen = set()
        ordered_tickers = []
        for t in tickers:
            if t and t not in seen:
                seen.add(t)
                ordered_tickers.append(t)

        print(f"[INFO] Usando arquivo: {csv_file}")
        return ordered_tickers

    except Exception as e:
        print(f"[ERRO] Falha ao ler CSV de mapeamento: {e}")
        return []


def filtrar_tickers(
    all_tickers: List[str],
    modo: str,
    quantidade: str,
    ticker: str,
    lista: str,
    faixa: str,
) -> List[str]:
    """
    Filtra a lista de tickers baseado no modo de seleção.
    Mantém a ordem original dos tickers.
    """
    if modo == "quantidade":
        try:
            n = int(quantidade) if quantidade else 10
            return all_tickers[:n]
        except ValueError:
            print(f"[AVISO] Quantidade inválida '{quantidade}', usando 10")
            return all_tickers[:10]

    if modo == "ticker":
        if not ticker:
            print("[AVISO] Ticker não especificado, processando todos")
            return all_tickers
        ticker_upper = ticker.strip().upper()
        return [t for t in all_tickers if t == ticker_upper]

    if modo == "lista":
        if not lista:
            print("[AVISO] Lista vazia, processando todos")
            return all_tickers
        tickers_list = [t.strip().upper() for t in lista.split(",") if t.strip()]
        return [t for t in all_tickers if t in tickers_list]

    if modo == "faixa":
        if not faixa or "-" not in faixa:
            print(f"[AVISO] Faixa inválida '{faixa}', usando 1-50")
            start, end = 1, 50
        else:
            try:
                a, b = faixa.split("-", 1)
                start = int(a.strip())
                end = int(b.strip())
            except Exception:
                print(f"[AVISO] Faixa inválida '{faixa}', usando 1-50")
                start, end = 1, 50

        start_idx = max(0, start - 1)
        end_idx = max(start_idx, end)
        return all_tickers[start_idx:end_idx]

    return all_tickers


# ------------------ Execução da captura (import OU subprocess) ------------------
def _try_call_module_capture(ticker: str) -> Optional[int]:
    """
    Tenta usar um módulo captura_balancos_b3 (se existir).
    Retorna returncode (0/!=0) ou None se não conseguiu usar módulo.
    """
    try:
        mod = importlib.import_module("captura_balancos_b3")
    except Exception:
        return None

    # tenta achar uma função de entrada razoável
    candidates = ["main", "capturar", "capturar_ticker", "run", "executar"]
    for fn_name in candidates:
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            try:
                sig = inspect.signature(fn)
                # tenta passar somente ticker
                if len(sig.parameters) == 1:
                    fn(ticker)
                else:
                    # tenta padrões comuns (ticker, repo_root/base_dir)
                    try:
                        fn(ticker, str(REPO_ROOT))
                    except Exception:
                        fn(ticker)
                return 0
            except SystemExit as se:
                return int(se.code) if se.code is not None else 0
            except Exception:
                # função existe mas falhou, propaga como erro !=0
                return 1

    # módulo existe, mas não tem função esperada
    return 1


def _find_capture_script() -> Optional[Path]:
    """
    Procura um script de captura existente no repo (prioridade para 'capturar_balancos.py').
    """
    script_names = [
        "src/capturar_balancos.py",
        "src/captura_balancos.py",
        "capturar_balancos.py",
        "captura_balancos.py",
    ]

    for script_name in script_names:
        p = REPO_ROOT / script_name
        if p.exists():
            return p

    # fallback: pega qualquer captura*.py que não seja este arquivo
    for pattern in ["src/captura*.py", "captura*.py", "src/capturar*.py", "capturar*.py"]:
        for p in REPO_ROOT.glob(pattern):
            if p.resolve() != HERE.resolve():
                return p

    return None


def _run_capture_subprocess(captura_script: Path, ticker: str) -> int:
    """
    Executa o script via subprocess mantendo stdout/stderr.
    """
    result = subprocess.run(
        [sys.executable, str(captura_script), ticker],
        capture_output=False,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    return int(result.returncode)


# ------------------ Main ------------------
def main():
    parser = argparse.ArgumentParser(
        description="Captura balanços da B3/CVM com seleção de tickers"
    )
    parser.add_argument(
        "--modo",
        default="quantidade",
        choices=["quantidade", "ticker", "lista", "faixa"],
        help="Modo de seleção de tickers",
    )
    parser.add_argument("--quantidade", default="10", help="Número de tickers (modo quantidade)")
    parser.add_argument("--ticker", default="", help="Ticker único (modo ticker)")
    parser.add_argument("--lista", default="", help="Lista de tickers separados por vírgula (modo lista)")
    parser.add_argument("--faixa", default="1-50", help="Faixa de tickers no formato inicio-fim (modo faixa)")
    args = parser.parse_args()

    mapping_file = Path("mapeamento_final_b3_completo_utf8.csv")  # nome base
    all_tickers = carregar_tickers_ordenados(mapping_file)

    if not all_tickers:
        print("[ERRO] Nenhum ticker encontrado no arquivo de mapeamento")
        sys.exit(1)

    tickers_selecionados = filtrar_tickers(
        all_tickers,
        args.modo,
        args.quantidade,
        args.ticker,
        args.lista,
        args.faixa,
    )

    if not tickers_selecionados:
        print("[AVISO] Nenhum ticker selecionado com os critérios fornecidos")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"Modo: {args.modo}")
    print(f"Tickers selecionados: {len(tickers_selecionados)}")
    print(f"{'='*60}\n")

    preview = tickers_selecionados[:10]
    print("Primeiros tickers a processar:")
    for i, t in enumerate(preview, 1):
        print(f"  {i}. {t}")
    if len(tickers_selecionados) > 10:
        print(f"  ... e mais {len(tickers_selecionados) - 10} tickers")
    print()

    # tenta módulo primeiro (se existir); senão usa subprocess com script
    captura_script = _find_capture_script()

    if captura_script:
        print(f"[INFO] Usando script: {captura_script}")
    else:
        # se não tem script, tentaremos módulo por ticker; se módulo não existir também, erro
        try_mod = True
        if _try_call_module_capture(tickers_selecionados[0]) is None:
            print("[ERRO] Não foi possível importar captura_balancos_b3 e nenhum script de captura foi encontrado.")
            print("       Verifique se existe um dos arquivos abaixo:")
            print("       - src/capturar_balancos.py")
            print("       - src/captura_balancos.py")
            print("       - captura_balancos_b3.py (em src/ ou raiz)")
            sys.exit(1)
        else:
            # módulo existe, mas já consumiu o primeiro ticker; vamos continuar por módulo
            try_mod = True
            # reprocessa desde o primeiro para manter consistência
            # (não capturamos nada de fato acima; usamos apenas como teste de import)
            pass

    sucesso = 0
    falhas = 0

    for idx, ticker in enumerate(tickers_selecionados, 1):
        print(f"\n[{idx}/{len(tickers_selecionados)}] Processando {ticker}...")

        try:
            rc: Optional[int] = None

            # preferir módulo se existir e tiver entrypoint; se não, subprocess
            rc = _try_call_module_capture(ticker)

            if rc is None:
                if not captura_script:
                    print("[ERRO] Script de captura não encontrado e módulo captura_balancos_b3 indisponível.")
                    falhas += 1
                    continue
                rc = _run_capture_subprocess(captura_script, ticker)

            if rc == 0:
                sucesso += 1
            else:
                falhas += 1
                print(f"[ERRO] Falha ao capturar {ticker} (returncode={rc})")

        except Exception as e:
            falhas += 1
            print(f"[ERRO] Falha ao capturar {ticker}: {e}")
            traceback.print_exc()

    print(f"\n{'='*60}")
    print("RESUMO DA CAPTURA")
    print(f"{'='*60}")
    print(f"Total processados: {len(tickers_selecionados)}")
    print(f"Sucesso: {sucesso}")
    print(f"Falhas: {falhas}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
