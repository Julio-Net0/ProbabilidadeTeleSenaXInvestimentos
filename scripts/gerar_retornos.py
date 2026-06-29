"""Baixa preços via yfinance e gera a série de retornos diários para o caso
contínuo da Lei dos Grandes Números.

Saída: data/retornos.csv com colunas Data, Fechamento, retorno_simples, retorno_log.

Uso:
    python scripts/gerar_retornos.py                      # defaults (PETR4.SA, ~10 anos)
    python scripts/gerar_retornos.py --ticker VALE3.SA
    python scripts/gerar_retornos.py --ticker ^BVSP --anos 15
    python scripts/gerar_retornos.py --ticker ^GSPC --start 2010-01-01 --end 2020-01-01

Lembretes de ticker (yfinance):
    - Ações da B3 exigem o sufixo .SA  -> PETR4.SA, VALE3.SA, ITUB4.SA
    - Índices usam o prefixo ^         -> ^BVSP (Ibovespa), ^GSPC (S&P 500)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    sys.exit(
        "yfinance não está instalado. Rode dentro do container Docker "
        "(docker compose up) ou instale com: pip install -r requirements.txt"
    )

# --- Defaults -------------------------------------------------------------
# Ação individual: variância maior -> convergência mais lenta e dramática,
# que é exatamente o contraste desejado contra a loteria.
TICKER_PADRAO = "PETR4.SA"
ANOS_PADRAO = 10

# Caminho de saída relativo à raiz do projeto (pasta-mãe de scripts/).
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
SAIDA_PADRAO = RAIZ_PROJETO / "data" / "retornos.csv"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Gera CSV de retornos diários via yfinance para o estudo da LGN."
    )
    p.add_argument("--ticker", default=TICKER_PADRAO,
                   help=f"Ticker do ativo (default: {TICKER_PADRAO}).")
    p.add_argument("--anos", type=int, default=ANOS_PADRAO,
                   help=f"Janela em anos a partir de hoje (default: {ANOS_PADRAO}). "
                        "Ignorado se --start for informado.")
    p.add_argument("--start", default=None,
                   help="Data inicial YYYY-MM-DD (sobrepõe --anos).")
    p.add_argument("--end", default=None,
                   help="Data final YYYY-MM-DD (default: hoje).")
    p.add_argument("--saida", type=Path, default=SAIDA_PADRAO,
                   help=f"Arquivo CSV de saída (default: {SAIDA_PADRAO}).")
    return p.parse_args()


def baixar_precos(ticker: str, start: str | None, end: str | None,
                  anos: int) -> pd.DataFrame:
    """Baixa o histórico diário e devolve um DataFrame com índice de datas.

    Usa auto_adjust=True explicitamente (versões recentes do yfinance mudaram
    o default), de modo que 'Close' já é o fechamento ajustado.
    """
    if start is None:
        hoje = date.today()
        start = hoje.replace(year=hoje.year - anos).isoformat()

    print(f"Baixando {ticker} de {start} até {end or 'hoje'} ...")
    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=True,    # 'Close' = fechamento ajustado
            progress=False,
        )
    except Exception as e:  # erro de rede, DNS, etc.
        sys.exit(f"Falha ao baixar dados (problema de rede?): {e}")

    if df is None or df.empty:
        sys.exit(
            f"Nenhum dado retornado para '{ticker}'. Verifique o ticker "
            "(ações B3 precisam de .SA; índices usam ^) e a conexão."
        )

    # Com um único ticker, yfinance pode devolver colunas MultiIndex
    # (nível 0 = campo, nível 1 = ticker). Achatamos para o nível do campo.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if "Close" not in df.columns:
        sys.exit(f"Coluna 'Close' ausente no retorno. Colunas: {list(df.columns)}")

    return df


def calcular_retornos(df: pd.DataFrame) -> pd.DataFrame:
    """Monta o DataFrame final com fechamento e os dois tipos de retorno."""
    fech = df["Close"].astype(float)

    saida = pd.DataFrame({
        "Data": df.index.date,
        "Fechamento": fech.to_numpy(),
        # Retorno simples: variação percentual de um dia para o outro.
        "retorno_simples": fech.pct_change().to_numpy(),
        # Retorno logarítmico: ln(P_t / P_{t-1}).
        "retorno_log": np.log(fech / fech.shift(1)).to_numpy(),
    })

    # O primeiro dia não tem retorno (NaN) -> remover.
    saida = saida.dropna(subset=["retorno_simples", "retorno_log"]).reset_index(drop=True)
    return saida


def resumo_sanidade(saida: pd.DataFrame, ticker: str) -> None:
    """Imprime estatísticas úteis para citar no trabalho e confirmar a alta
    variância relativa (coeficiente de variação)."""
    r = saida["retorno_simples"]
    media = r.mean()
    desvio = r.std()
    cv = desvio / abs(media) if media != 0 else float("inf")

    print("\n" + "=" * 56)
    print(f"  Resumo de sanidade — {ticker}")
    print("=" * 56)
    print(f"  Observações (dias)     : {len(saida)}")
    print(f"  Período                : {saida['Data'].iloc[0]} a {saida['Data'].iloc[-1]}")
    print(f"  Média do retorno diário: {media:.6f}  ({media * 100:.4f}% ao dia)")
    print(f"  Desvio padrão          : {desvio:.6f}  ({desvio * 100:.4f}% ao dia)")
    print(f"  Coef. de variação |σ/μ|: {cv:.1f}x")
    print("=" * 56)
    print("  CV alto confirma: volatilidade enorme frente à média minúscula")
    print("  -> convergência da LGN será LENTA e ruidosa (contraste vs. loteria).")
    print("=" * 56 + "\n")


def main() -> None:
    args = parse_args()
    df = baixar_precos(args.ticker, args.start, args.end, args.anos)
    saida = calcular_retornos(df)

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    saida.to_csv(args.saida, index=False, encoding="utf-8")
    print(f"CSV salvo em: {args.saida}  ({len(saida)} linhas)")

    resumo_sanidade(saida, args.ticker)


if __name__ == "__main__":
    main()
