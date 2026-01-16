#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Capturador da Curva PRE-DI (B3 / antigo BM&F) -> JSON estruturado (site/data)

- Busca a curva mais recente disponível e também:
  - 1 dia útil antes
  - 5 dias úteis antes (1 semana)
  - 21 dias úteis antes (1 mês)
- Baixa todos os vértices disponíveis e pode interpolar para vértices desejados
- Calcula variações em basis points (bps)
- Salva em: site/data/curva_pre_di.json (por padrão)

Execução:
  python src/capturar_curva_pre_di.py
  python src/capturar_curva_pre_di.py --output site/data/curva_pre_di.json --quiet
"""

from __future__ import annotations

import argparse
import json
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from scipy import interpolate

# Evitar warnings de SSL verify=False
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


DEFAULT_OUTPUT = "site/data/curva_pre_di.json"


# -----------------------------
# Datas úteis
# -----------------------------

def ultimo_dia_util(data: Optional[object] = None) -> pd.Timestamp:
    """
    Retorna a data do último dia útil anterior ou igual à data fornecida.
    Se nenhuma data for fornecida, usa a data atual.
    """
    if data is None:
        data = datetime.today()
    else:
        if isinstance(data, str):
            data = pd.to_datetime(data, dayfirst=True)

    ultimo_util = pd.bdate_range(end=data, periods=1)[0]
    return ultimo_util


def dia_util_anterior(data: object, dias_uteis: int = 1) -> pd.Timestamp:
    """
    Retorna a data de N dias úteis antes da data fornecida.
    """
    data_pd = pd.to_datetime(data)
    dias_extras = dias_uteis * 2 + 10
    datas = pd.bdate_range(end=data_pd, periods=dias_extras)

    if len(datas) > dias_uteis:
        return datas[-(dias_uteis + 1)]
    return datas[0]


# -----------------------------
# Interpolação
# -----------------------------

def interpolar_taxa(dias_conhecidos, taxas_conhecidas, dias_interpolar):
    """
    Interpola taxas de juros usando interpolação linear ou spline cúbica.
    """
    dias_conhecidos = np.array(dias_conhecidos, dtype=float)
    taxas_conhecidas = np.array(taxas_conhecidas, dtype=float)
    dias_interpolar = np.array(dias_interpolar, dtype=float)

    mask = ~np.isnan(taxas_conhecidas)
    dias_validos = dias_conhecidos[mask]
    taxas_validas = taxas_conhecidas[mask]

    if len(dias_validos) < 2:
        return np.full(len(dias_interpolar), np.nan)

    if len(dias_validos) >= 4:
        f = interpolate.interp1d(
            dias_validos, taxas_validas,
            kind="cubic", fill_value="extrapolate", bounds_error=False
        )
    else:
        f = interpolate.interp1d(
            dias_validos, taxas_validas,
            kind="linear", fill_value="extrapolate", bounds_error=False
        )

    taxas_interpoladas = f(dias_interpolar)

    # Limita extrapolação para evitar valores irreais
    min_dia, max_dia = dias_validos.min(), dias_validos.max()
    for i, dia in enumerate(dias_interpolar):
        if dia < min_dia * 0.5 or dia > max_dia * 1.5:
            taxas_interpoladas[i] = np.nan

    return taxas_interpoladas


# -----------------------------
# Captura PRE-DI
# -----------------------------

@dataclass
class CurvaResult:
    data: pd.Timestamp
    df: pd.DataFrame  # index=dias, col=taxa_252


class BaixaPre:
    def __init__(self, headers: Optional[dict] = None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        }

        # Vértices principais (expandido)
        self.vertices_principais = [
            21, 42, 63, 84, 105, 126, 147, 168, 189, 210, 231, 252,
            294, 336, 378, 420, 462, 504,
            588, 672, 756,
            1008, 1260, 1512, 1764, 2016, 2520
        ]

    def formatar_data(self, data) -> Tuple[str, str]:
        if isinstance(data, str):
            data = pd.to_datetime(data, dayfirst=True)

        mes = str(data.month).zfill(2)
        dia = str(data.day).zfill(2)
        ano = data.year

        dt_barra = f"{dia}/{mes}/{ano}"
        dt_corrida = f"{ano}{mes}{dia}"
        return dt_barra, dt_corrida

    def baixa_curva(self, data, filtrar_vertices: bool = True) -> pd.DataFrame:
        """
        Baixa a curva PRE-DI para uma data específica.
        Retorna df index=dias com taxa_252 (decimal), ex.: 0.1225 = 12.25%
        """
        dt_barra, dt_corrida = self.formatar_data(data)

        link = (
            "https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/TxRef1.asp"
            f"?Data={dt_barra}&Data1={dt_corrida}&slcTaxa=PRE"
        )

        try:
            page = requests.get(link, headers=self.headers, verify=False, timeout=20)
            if page.status_code != 200:
                return pd.DataFrame()

            soup = BeautifulSoup(page.content, "html.parser")
            tds = soup.find_all("td")

            dias, taxas252 = [], []
            tabelas = {"['tabelaConteudo1']", "['tabelaConteudo2']"}

            for i in range(0, len(tds), 3):
                try:
                    if str(tds[i].get("class", "")) in tabelas:
                        dia = int(
                            tds[i].text.replace("\r\n", "")
                            .replace(",", ".").replace(" ", "").strip()
                        )
                        taxa252 = float(
                            tds[i + 1].text.replace("\r\n", "")
                            .replace(",", ".").replace(" ", "").strip()
                        ) / 100.0

                        if not filtrar_vertices or dia in self.vertices_principais:
                            dias.append(dia)
                            taxas252.append(taxa252)
                except Exception:
                    continue

            if dias:
                df = pd.DataFrame({"taxa_252": taxas252}, index=dias)
                df.index.name = "dias"
                df = df.sort_index()
                return df

            return pd.DataFrame()

        except Exception:
            return pd.DataFrame()

    def buscar_data_com_dados(
        self,
        data_inicial: pd.Timestamp,
        max_tentativas: int = 5,
        direcao: str = "anterior",
        quiet: bool = False,
    ) -> Tuple[Optional[pd.Timestamp], pd.DataFrame]:
        """
        Busca uma data com dados disponíveis, tentando datas anteriores ou posteriores.
        """
        data_tentativa = data_inicial

        for tentativa in range(max_tentativas):
            if not quiet:
                print(f"  Tentando data: {data_tentativa.strftime('%d/%m/%Y')}...", end=" ")

            curva = self.baixa_curva(data_tentativa, filtrar_vertices=False)

            if not curva.empty:
                if not quiet:
                    print("✓ Dados encontrados!")
                return data_tentativa, curva

            if not quiet:
                print("✗ Sem dados")

            if direcao == "anterior":
                data_tentativa = dia_util_anterior(data_tentativa, 1)
            else:
                data_tentativa = pd.bdate_range(start=data_tentativa, periods=2)[1]

        if not quiet:
            print(f"  ⚠ Não foram encontrados dados após {max_tentativas} tentativas")
        return None, pd.DataFrame()

    def interpolar_curva(self, curva_df: pd.DataFrame, vertices_desejados: List[int]) -> pd.Series:
        if curva_df.empty:
            return pd.Series(index=vertices_desejados, dtype=float)

        dias_conhecidos = curva_df.index.tolist()
        taxas_conhecidas = curva_df["taxa_252"].values
        taxas_interpoladas = interpolar_taxa(dias_conhecidos, taxas_conhecidas, vertices_desejados)
        return pd.Series(taxas_interpoladas, index=vertices_desejados)

    def baixa_curvas_comparativas(
        self,
        vertices_selecionados: Optional[List[int]] = None,
        usar_interpolacao: bool = True,
        max_tentativas: int = 5,
        quiet: bool = False,
    ) -> pd.DataFrame:
        """
        Retorna DataFrame consolidado com curvas:
          - atual
          - 1d_atras
          - 1sem_atras (5 DU)
          - 1mes_atras (21 DU)
        Além de variações em bps.
        """
        ultima_data = ultimo_dia_util()

        if not quiet:
            print("=" * 70)
            print("BAIXANDO CURVAS DE JUROS PRÉ-DI")
            print("=" * 70)
            print(f"Data base inicial: {ultima_data.strftime('%d/%m/%Y')}")
            print("-" * 70)

        curvas: Dict[str, pd.DataFrame] = {}
        datas_efetivas: Dict[str, pd.Timestamp] = {}

        # 1) curva recente
        if not quiet:
            print("\n1. CURVA MAIS RECENTE")
            print("-" * 30)
        data_encontrada, curva_recente = self.buscar_data_com_dados(
            ultima_data, max_tentativas=max_tentativas, direcao="anterior", quiet=quiet
        )

        if data_encontrada is not None and not curva_recente.empty:
            curvas["recente"] = curva_recente
            datas_efetivas["recente"] = data_encontrada
            data_base_para_calculos = data_encontrada
            if not quiet:
                print(f"  ✅ Curva mais recente obtida: {data_encontrada.strftime('%d/%m/%Y')}")
        else:
            data_base_para_calculos = ultima_data
            if not quiet:
                print("  ❌ Não foi possível obter a curva mais recente (seguindo com datas alvo)")

        data_1d_antes = dia_util_anterior(data_base_para_calculos, 1)
        data_1sem_antes = dia_util_anterior(data_base_para_calculos, 5)
        data_1mes_antes = dia_util_anterior(data_base_para_calculos, 21)

        # 2) 1d
        if not quiet:
            print("\n2. CURVA DE 1 DIA ÚTIL ANTES")
            print("-" * 30)
            print(f"  Data alvo: {data_1d_antes.strftime('%d/%m/%Y')}")
        d, c = self.buscar_data_com_dados(data_1d_antes, max_tentativas=max_tentativas, direcao="anterior", quiet=quiet)
        if d is not None and not c.empty:
            curvas["1d"] = c
            datas_efetivas["1d"] = d

        # 3) 1sem
        if not quiet:
            print("\n3. CURVA DE 1 SEMANA ANTES (5 DIAS ÚTEIS)")
            print("-" * 30)
            print(f"  Data alvo: {data_1sem_antes.strftime('%d/%m/%Y')}")
        d, c = self.buscar_data_com_dados(data_1sem_antes, max_tentativas=max_tentativas, direcao="anterior", quiet=quiet)
        if d is not None and not c.empty:
            curvas["1sem"] = c
            datas_efetivas["1sem"] = d

        # 4) 1mes
        if not quiet:
            print("\n4. CURVA DE 1 MÊS ANTES (21 DIAS ÚTEIS)")
            print("-" * 30)
            print(f"  Data alvo: {data_1mes_antes.strftime('%d/%m/%Y')}")
        d, c = self.buscar_data_com_dados(data_1mes_antes, max_tentativas=max_tentativas, direcao="anterior", quiet=quiet)
        if d is not None and not c.empty:
            curvas["1mes"] = c
            datas_efetivas["1mes"] = d

        if vertices_selecionados:
            vertices_usar = sorted(vertices_selecionados)
        else:
            vertices_usar = [21, 63, 126, 252, 378, 504, 756, 1008, 1260, 2520]

        df = pd.DataFrame(index=vertices_usar)
        df.index.name = "dias"
        df.attrs["datas_efetivas"] = {k: v.strftime("%Y-%m-%d") for k, v in datas_efetivas.items()}

        def add_curve(col_name: str, key: str):
            if key not in curvas or curvas[key].empty:
                return
            if usar_interpolacao:
                df[col_name] = self.interpolar_curva(curvas[key], vertices_usar)
                df[f"{col_name}_original"] = curvas[key].reindex(vertices_usar)["taxa_252"]
            else:
                df[col_name] = curvas[key].reindex(vertices_usar)["taxa_252"]

        add_curve("atual", "recente")
        add_curve("1d_atras", "1d")
        add_curve("1sem_atras", "1sem")
        add_curve("1mes_atras", "1mes")

        # variações bps (decimal -> bps)
        if "atual" in df.columns and "1d_atras" in df.columns:
            df["var_1d_bps"] = (df["atual"] - df["1d_atras"]) * 10000

        if "atual" in df.columns and "1sem_atras" in df.columns:
            df["var_1sem_bps"] = (df["atual"] - df["1sem_atras"]) * 10000

        if "atual" in df.columns and "1mes_atras" in df.columns:
            df["var_1mes_bps"] = (df["atual"] - df["1mes_atras"]) * 10000

        # converter taxas para %
        for col in ["atual", "1d_atras", "1sem_atras", "1mes_atras"]:
            if col in df.columns:
                df[col] = df[col] * 100

        if usar_interpolacao:
            for col in ["atual_original", "1d_atras_original", "1sem_atras_original", "1mes_atras_original"]:
                if col in df.columns:
                    df[col] = df[col] * 100

        return df


# -----------------------------
# Saída JSON
# -----------------------------

def df_to_json_payload(df: pd.DataFrame) -> Dict:
    datas_efetivas = df.attrs.get("datas_efetivas", {})

    rows = []
    for dias, row in df.iterrows():
        item = {"dias": int(dias)}
        for col, val in row.items():
            if pd.isna(val):
                item[col] = None
            else:
                # floats normais
                item[col] = float(val)
        rows.append(item)

    payload = {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "datas_efetivas": datas_efetivas,
        "vertices": [int(x) for x in df.index.tolist()],
        "series": rows,
    }
    return payload


def salvar_json(payload: Dict, output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# -----------------------------
# CLI
# -----------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Captura curva PRE-DI e salva JSON em site/data.")
    p.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Saída JSON (default: {DEFAULT_OUTPUT})")
    p.add_argument("--quiet", action="store_true", help="Modo silencioso")
    p.add_argument("--no-interp", action="store_true", help="Desliga interpolação")
    p.add_argument("--max-tentativas", type=int, default=5, help="Max tentativas por período")
    return p


def main() -> int:
    args = build_parser().parse_args()
    quiet = bool(args.quiet)

    b = BaixaPre(headers=None)
    df = b.baixa_curvas_comparativas(
        vertices_selecionados=None,
        usar_interpolacao=not args.no_interp,
        max_tentativas=args.max_tentativas,
        quiet=quiet,
    )

    if df.empty:
        print("❌ Falha: DataFrame consolidado vazio.")
        return 1

    payload = df_to_json_payload(df)
    salvar_json(payload, args.output)

    if not quiet:
        print(f"💾 JSON salvo em: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
