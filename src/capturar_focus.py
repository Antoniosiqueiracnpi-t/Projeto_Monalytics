#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Capturador do Relatório Focus (BCB) -> JSON estruturado

- Busca o PDF mais recente disponível (até N dias para trás)
- Extrai os indicadores (IPCA, PIB, Câmbio, Selic) para 2026 e 2027:
    - Há 1 semana (Ha1Sem2026/Ha1Sem2027)
    - Hoje (valor_2026/valor_2027)
- Calcula deltas e setas ▲/▼/―
- Salva JSON em caminho configurável (default: site/data/focus.json)

Compatível com GitHub Actions e execução local.

Uso:
  python src/capturar_focus.py
  python src/capturar_focus.py --output site/data/focus.json --days-back 10 --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


# -----------------------------
# Config / Defaults
# -----------------------------

DEFAULT_OUTPUT = "site/data/focus.json"
DEFAULT_DAYS_BACK = 10
BCB_FOCUS_URL_TEMPLATE = "https://www.bcb.gov.br/content/focus/focus/R{yyyymmdd}.pdf"

# Fallback "fixo" (último recurso) - valores meramente de referência.
# O script prioriza:
# 1) Extração real do PDF
# 2) Completar faltantes com o JSON anterior já salvo (se existir)
# 3) Se não existir anterior, usa este fallback fixo
FALLBACK_REFERENCE = {
    "IPCA":  {"Ha1Sem2026": 4.80, "2026": 4.72, "Ha1Sem2027": 4.28, "2027": 4.28},
    "PIB":   {"Ha1Sem2026": 2.16, "2026": 2.16, "Ha1Sem2027": 1.80, "2027": 1.80},
    "Câmbio":{"Ha1Sem2026": 5.45, "2026": 5.45, "Ha1Sem2027": 5.53, "2027": 5.50},
    "Selic": {"Ha1Sem2026": 15.00,"2026": 15.00,"Ha1Sem2027": 12.25,"2027": 12.25},
}


# -----------------------------
# Model
# -----------------------------

@dataclass
class IndicatorRow:
    indicador: str
    ha1sem2026: float
    valor_2026: float
    ha1sem2027: float
    valor_2027: float

    delta_2026: float = 0.0
    delta_2027: float = 0.0
    var_sem_2026: str = "―"
    var_sem_2027: str = "―"

    def compute_deltas(self) -> None:
        self.delta_2026 = float(self.valor_2026) - float(self.ha1sem2026)
        self.delta_2027 = float(self.valor_2027) - float(self.ha1sem2027)

        self.var_sem_2026 = "▲" if self.delta_2026 > 0 else ("▼" if self.delta_2026 < 0 else "―")
        self.var_sem_2027 = "▲" if self.delta_2027 > 0 else ("▼" if self.delta_2027 < 0 else "―")


# -----------------------------
# Helpers
# -----------------------------

def _safe_float_br(s: str) -> Optional[float]:
    """
    Converte string numérica com vírgula/ponto para float.
    Retorna None para '-' ou inválidos.
    """
    s = (s or "").strip()
    if s == "-" or s == "":
        return None
    # remove espaços e normaliza decimal
    s = s.replace(" ", "")
    # mantém apenas dígitos, vírgula, ponto e sinal
    s = re.sub(r"[^0-9,\.\-]", "", s)
    if not s:
        return None
    # Se vier com vírgula como decimal
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    # Se vier com ambos, assume que ponto é milhar e vírgula decimal (caso raro)
    elif s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _is_valid_value(indicator: str, value: float) -> bool:
    """
    Faixas plausíveis (heurística) para filtrar números no PDF.
    """
    try:
        v = float(value)
        if indicator == "IPCA":
            return 0.5 <= v <= 15.0
        if indicator == "PIB":
            return -5.0 <= v <= 10.0
        if indicator == "Câmbio":
            return 3.0 <= v <= 10.0
        if indicator == "Selic":
            return 8.0 <= v <= 25.0
        return False
    except Exception:
        return False


def _extract_number_tokens(text: str) -> List[str]:
    """
    Captura tokens numéricos com decimal e também '-' isolado,
    na ordem em que aparecem na linha.
    """
    # tokens: '-' OU número decimal (com , ou .)
    # Ex.: "15,00 - - 12,25 12,25"
    pattern = r"(?:(?<!\d)-(?=\s|$))|(?:-?\d+[,\.]\d+)"
    return re.findall(pattern, text)


def _detect_indicator(text: str) -> Optional[str]:
    t = (text or "").lower()

    # IMPORTANTE: ignorar IPCA Administrados explicitamente
    if "ipca administrados" in t:
        return None

    # IPCA vem antes para não confundir com outras linhas "ipca ..."
    if "ipca" in t and ("variacao" in t or "variação" in t):
        return "IPCA"

    if "pib" in t and "total" in t:
        return "PIB"

    if "cambio" in t or "câmbio" in t or ("r$" in t and "us$" in t):
        return "Câmbio"

    if "selic" in t and ("a.a" in t or "% a" in t or "%a" in t):
        return "Selic"

    return None


def _parse_indicator_line(indicator: str, text: str, verbose: bool = False) -> Optional[IndicatorRow]:
    """
    Extrai Ha1Sem e Hoje para 2026 e 2027.

    Regra principal (para IPCA/PIB/Câmbio e também Selic quando possível):
      tokens válidos (filtrados por faixa) e índices:
        [0]=Há4_2026, [1]=Há1_2026, [2]=Hoje_2026, [3]=5dias_2026,
        [4]=Há4_2027, [5]=Há1_2027, [6]=Hoje_2027, [7]=5dias_2027 (às vezes existe)
      usamos: 2026 -> [1],[2] e 2027 -> [5],[6]

    Tratamento especial Selic:
      pode aparecer '-' em 2026 (Há1 ou Hoje), então tenta capturar tokens com '-'
      e faz fallback: se Ha1Sem2026 for None usa Há4_2026; se Hoje_2026 for None usa Ha1Sem2026.
    """
    tokens = _extract_number_tokens(text)
    if len(tokens) < 6:
        return None

    # Converte tokens para floats/None
    vals: List[Optional[float]] = []
    for tok in tokens:
        vals.append(_safe_float_br(tok))

    if indicator == "Selic":
        # Para Selic, queremos permitir '-' em Ha1/Hoj 2026
        # Estratégia:
        # 1) coletar também valores plausíveis e manter a posição aproximada
        # 2) se possível, usar o mesmo esquema de índices (após filtrar)
        # 3) se houver None em Ha1/Hoj, aplicar fallback
        float_vals = [v for v in vals if v is not None]
        valid_float_vals = [v for v in float_vals if _is_valid_value("Selic", v)]
        # Precisa de pelo menos 4 valores plausíveis no bloco 2026/2027
        if len(valid_float_vals) >= 6:
            # tenta via índices padrão nos válidos
            try:
                ha1_2026 = valid_float_vals[1]
                hoje_2026 = valid_float_vals[2]
                ha1_2027 = valid_float_vals[5]
                hoje_2027 = valid_float_vals[6]
                row = IndicatorRow("Selic", ha1_2026, hoje_2026, ha1_2027, hoje_2027)
                return row
            except Exception:
                pass

        # fallback: tenta reconstruir mantendo '-' nas primeiras posições
        # Aqui assumimos que os primeiros 3 tokens relevantes são 2026 (Há4, Há1, Hoje)
        # e depois aparece bloco 2027. Isso costuma bater com o PDF.
        # Seleciona apenas tokens que são '-' ou número decimal (já é o caso),
        # mas remove coisas irrelevantes por faixa quando possível.
        # Monta "sequência" de valores candidatos na ordem.
        seq: List[Optional[float]] = []
        for v in vals:
            # mantemos None (para '-') e valores plausíveis
            if v is None:
                seq.append(None)
            else:
                if _is_valid_value("Selic", v):
                    seq.append(v)

        # remove Nones/valores que sobraram demais? Mantemos, mas precisamos encontrar 7 slots úteis.
        # Tenta localizar o primeiro bloco 2026 como 3 slots (h4, h1, hoje).
        # Para robustez, extrai os primeiros 3 slots não-null/None, permitindo None no meio.
        useful: List[Optional[float]] = [x for x in seq if (x is None or isinstance(x, float))]
        if len(useful) < 6:
            return None

        # Heurística: pega as 3 primeiras posições como (h4,h1,hoje) 2026 e as 3 últimas como (h4,h1,hoje) 2027
        h4_2026 = useful[0]
        h1_2026 = useful[1] if len(useful) > 1 else None
        hoje_2026 = useful[2] if len(useful) > 2 else None

        h4_2027 = useful[-3]
        h1_2027 = useful[-2]
        hoje_2027 = useful[-1]

        # fallback conforme sua regra original
        if h1_2026 is None:
            h1_2026 = h4_2026 if h4_2026 is not None else None
        if hoje_2026 is None:
            hoje_2026 = h1_2026

        if None in (h1_2026, hoje_2026, h1_2027, hoje_2027):
            return None

        if verbose:
            print(f"        ✅ Selic (fallback): 2026({h1_2026}→{hoje_2026}) | 2027({h1_2027}→{hoje_2027})")

        return IndicatorRow("Selic", float(h1_2026), float(hoje_2026), float(h1_2027), float(hoje_2027))

    # Lógica padrão para IPCA/PIB/Câmbio
    # Converte apenas floats e filtra pela faixa plausível do indicador
    float_vals = [v for v in vals if v is not None]
    valid = [v for v in float_vals if _is_valid_value(indicator, v)]

    if len(valid) < 7:
        if verbose:
            print(f"        ⚠️ {indicator}: apenas {len(valid)} valores válidos (precisa >= 7)")
        return None

    try:
        ha1_2026 = valid[1]
        hoje_2026 = valid[2]
        ha1_2027 = valid[5]
        hoje_2027 = valid[6]
        return IndicatorRow(indicator, ha1_2026, hoje_2026, ha1_2027, hoje_2027)
    except Exception:
        return None


def _load_previous_reference(output_path: Path) -> Dict[str, Dict[str, float]]:
    """
    Se existir um JSON anterior no output, usa como referência para completar
    indicadores faltantes (melhor do que fallback fixo).
    """
    if not output_path.exists():
        return {}

    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
        out: Dict[str, Dict[str, float]] = {}
        for item in data.get("indicadores", []):
            ind = item.get("indicador")
            if not ind:
                continue
            out[ind] = {
                "Ha1Sem2026": float(item.get("ha1sem2026")),
                "2026": float(item.get("valor_2026")),
                "Ha1Sem2027": float(item.get("ha1sem2027")),
                "2027": float(item.get("valor_2027")),
            }
        return out
    except Exception:
        return {}


# -----------------------------
# PDF Extraction
# -----------------------------

def _ensure_pdfplumber() -> Any:
    try:
        import pdfplumber  # type: ignore
        return pdfplumber
    except Exception as e:
        raise RuntimeError(
            "Dependência ausente: pdfplumber. Instale com: pip install pdfplumber"
        ) from e


def _download_pdf(url: str, dest: Path, timeout: int = 20) -> None:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)


def _extract_lines_from_pdf(pdf_path: Path, verbose: bool = False) -> List[str]:
    """
    Extrai o máximo de linhas possíveis do PDF (primeira página), tentando:
      1) tabelas (extract_tables) -> linhas concatenadas
      2) texto bruto (extract_text) -> splitlines
    """
    pdfplumber = _ensure_pdfplumber()

    lines: List[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        if not pdf.pages:
            return []

        page = pdf.pages[0]

        # 1) tabelas
        try:
            tables = page.extract_tables() or []
        except Exception:
            tables = []

        if tables:
            if verbose:
                print(f"    📊 {len(tables)} tabela(s) encontrada(s)")
            for t_i, table in enumerate(tables, start=1):
                if verbose:
                    print(f"    🔍 Analisando tabela {t_i}")
                for row in table:
                    if not row or not any(row):
                        continue
                    row_text = " ".join(str(c) for c in row if c is not None).strip()
                    if row_text:
                        lines.append(row_text)

        # 2) texto bruto
        if not lines:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if raw_lines:
                if verbose:
                    print(f"    📝 {len(raw_lines)} linha(s) de texto encontradas")
                lines.extend(raw_lines)

    return lines


# -----------------------------
# Focus fetching
# -----------------------------

def _find_latest_focus_pdf(days_back: int, verbose: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Procura o PDF mais recente disponível até `days_back` dias atrás.
    Retorna (url, date_str_ddmmyyyy).
    """
    today = datetime.now()
    for back in range(days_back):
        d = today - timedelta(days=back)
        date_str = d.strftime("%d/%m/%Y")
        url = BCB_FOCUS_URL_TEMPLATE.format(yyyymmdd=d.strftime("%Y%m%d"))

        try:
            head = requests.head(url, timeout=10)
            if head.status_code == 200:
                if verbose:
                    print(f"✅ PDF encontrado: {date_str} | {url}")
                return url, date_str
        except Exception:
            continue

        if verbose:
            print(f"    ⏳ Não encontrado: {date_str}")

    return None, None


# -----------------------------
# Core public function
# -----------------------------

def get_focus_data(
    output_path: str = DEFAULT_OUTPUT,
    days_back: int = DEFAULT_DAYS_BACK,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Extrai dados do Focus com salvamento estruturado em JSON.
    Ajustado para capturar IPCA 2026 e 2027 (e demais indicadores 2026/2027).
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        print("🔍 Buscando PDF do Focus...")

    url, report_date = _find_latest_focus_pdf(days_back=days_back, verbose=verbose)
    extracted: Dict[str, IndicatorRow] = {}
    real_extraction = False

    previous_ref = _load_previous_reference(out_path)
    if verbose and previous_ref:
        print("🧩 Referência anterior encontrada (será usada para completar faltantes).")

    if url and report_date:
        tmp_pdf = Path("/tmp/focus_temp.pdf")
        try:
            _download_pdf(url, tmp_pdf)
            lines = _extract_lines_from_pdf(tmp_pdf, verbose=verbose)

            if verbose:
                print(f"    📄 Linhas analisáveis: {len(lines)}")

            for line in lines:
                ind = _detect_indicator(line)
                if not ind:
                    continue

                row = _parse_indicator_line(ind, line, verbose=verbose)
                if row:
                    extracted[row.indicador] = row
                    if verbose:
                        print(f"        ✅ {row.indicador} encontrado!")

            if extracted:
                real_extraction = True

        except Exception as e:
            if verbose:
                print(f"    ❌ Erro na extração do PDF: {e}")

    # Se não conseguiu extrair nada, usa referência anterior ou fallback fixo
    if not real_extraction:
        if verbose:
            print("⚠️ Não foi possível extrair do PDF. Usando referência.")
        report_date = report_date or datetime.now().strftime("%d/%m/%Y")

    # Completar faltantes: prioriza JSON anterior, depois fallback fixo
    ordered = ["IPCA", "PIB", "Câmbio", "Selic"]
    final_rows: List[IndicatorRow] = []

    for ind in ordered:
        if ind in extracted:
            final_rows.append(extracted[ind])
            continue

        ref_src = None
        ref = None

        if ind in previous_ref:
            ref = previous_ref[ind]
            ref_src = "anterior"
        elif ind in FALLBACK_REFERENCE:
            ref = FALLBACK_REFERENCE[ind]
            ref_src = "fallback"

        if ref:
            if verbose:
                print(f"🧩 Completando {ind} via referência ({ref_src}).")
            final_rows.append(
                IndicatorRow(
                    indicador=ind,
                    ha1sem2026=float(ref["Ha1Sem2026"]),
                    valor_2026=float(ref["2026"]),
                    ha1sem2027=float(ref["Ha1Sem2027"]),
                    valor_2027=float(ref["2027"]),
                )
            )

    # calcular deltas e setas
    for r in final_rows:
        r.compute_deltas()

    # imprimir resumo (opcional)
    if verbose:
        print("\n" + "=" * 70)
        print("RELATÓRIO FOCUS")
        print("=" * 70)
        print(f"📅 Data: {report_date}")
        print("🎯 DADOS EXTRAÍDOS DO PDF" if real_extraction else "📚 DADOS DE REFERÊNCIA (parcial/total)")
        print("-" * 70)

        for r in final_rows:
            if r.indicador == "Câmbio":
                print(f"\n{r.indicador}:")
                print(f"  2026: R$ {r.ha1sem2026:.2f} → R$ {r.valor_2026:.2f} (Δ{r.delta_2026:+.2f}) {r.var_sem_2026}")
                print(f"  2027: R$ {r.ha1sem2027:.2f} → R$ {r.valor_2027:.2f} (Δ{r.delta_2027:+.2f}) {r.var_sem_2027}")
            else:
                print(f"\n{r.indicador}:")
                print(f"  2026: {r.ha1sem2026:.2f}% → {r.valor_2026:.2f}% (Δ{r.delta_2026:+.2f}) {r.var_sem_2026}")
                print(f"  2027: {r.ha1sem2027:.2f}% → {r.valor_2027:.2f}% (Δ{r.delta_2027:+.2f}) {r.var_sem_2027}")

        print("=" * 70)

    # JSON estruturado
    json_output: Dict[str, Any] = {
        "data_relatorio": report_date,
        "dados_reais": bool(real_extraction),
        "indicadores": [
            {
                "indicador": r.indicador,
                "ha1sem2026": float(r.ha1sem2026),
                "valor_2026": float(r.valor_2026),
                "ha1sem2027": float(r.ha1sem2027),
                "valor_2027": float(r.valor_2027),
                "delta_2026": float(r.delta_2026),
                "delta_2027": float(r.delta_2027),
                "var_sem_2026": r.var_sem_2026,
                "var_sem_2027": r.var_sem_2027,
            }
            for r in final_rows
        ],
    }

    out_path.write_text(json.dumps(json_output, ensure_ascii=False, indent=2), encoding="utf-8")

    if verbose:
        print(f"\n💾 Dados salvos em: {out_path.as_posix()}")

    return {
        "data_relatorio": report_date,
        "dados_reais": real_extraction,
        "json_path": out_path.as_posix(),
        "json": json_output,
    }


# -----------------------------
# CLI
# -----------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Capturar Relatório Focus (BCB) e salvar JSON estruturado.")
    p.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Caminho de saída do JSON (default: {DEFAULT_OUTPUT})")
    p.add_argument("--days-back", type=int, default=DEFAULT_DAYS_BACK, help=f"Quantos dias buscar para trás (default: {DEFAULT_DAYS_BACK})")
    p.add_argument("--quiet", action="store_true", help="Sem prints (modo silencioso)")
    return p


def main() -> int:
    args = _build_arg_parser().parse_args()
    verbose = not args.quiet

    try:
        get_focus_data(output_path=args.output, days_back=args.days_back, verbose=verbose)
        return 0
    except Exception as e:
        print(f"❌ Falha ao capturar Focus: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
