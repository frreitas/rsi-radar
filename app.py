import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Radar RSI Cripto", layout="wide")
st.title("📊 Radar RSI com Tendência de Alta")
st.markdown("Analisa as principais criptos com RSI e EMAs em tempo real via Binance API.")

# ===== INTERVALOS E PARÂMETROS =====
intervalo = st.selectbox("⏱️ Intervalo de tempo", ["1h", "4h", "1d"], index=0)
binance_interval = {"1h": "1h", "4h": "4h", "1d": "1d"}[intervalo]
limite_velas = 100
limite_moedas = st.selectbox("🏆 Quantidade de moedas a analisar", [20, 50, 100], index=2)

executar_analise = st.button("🔄 Atualizar agora")

# ===== FUNÇÕES AUXILIARES =====
@st.cache_data(ttl=600)
def get_binance_symbols():
    """Retorna lista de símbolos disponíveis na Binance"""
    url = "https://api.binance.com/api/v3/exchangeInfo"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        return set([s["symbol"] for s in data["symbols"]])
    except Exception as e:
        st.error(f"Erro ao obter símbolos da Binance: {e}")
        return set()

@st.cache_data(ttl=300)
def get_top_symbols_existentes_na_binance(limit=100):
    """Retorna os top N símbolos do CoinGecko que também existem na Binance como pares USDT"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        coins = res.json()
        binance_symbols = get_binance_symbols()
        valid_symbols = []

        for coin in coins:
            symbol = coin["symbol"].upper()
            pair = symbol + "USDT"
            if pair in binance_symbols:
                valid_symbols.append(pair)

        return valid_symbols
    except Exception as e:
        st.error(f"Erro ao buscar moedas: {e}")
        return []

def get_klines(symbol, interval="1h", limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        r = requests.get(url, params=params, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()
        if not data or len(data) < 50:
            return None

        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df["close"] = df["close"].astype(float)
        return df

    except Exception as e:
        print(f"Erro em get_klines para {symbol}: {e}")
        return None

def classificar_rsi(rsi):
    if rsi <= 30:
        return "Sobrevendida"
    elif rsi >= 70:
        return "Sobrecomprada"
    else:
        return "Neutra"

def classificar_tendencia(ema20, ema50):
    if ema20 > ema50:
        return "Alta"
    elif ema20 < ema50:
        return "Baixa"
    else:
        return "Neutra"

def analisar_moeda(symbol):
    try:
        df = get_klines(symbol, interval=binance_interval, limit=limite_velas)
        if df is None or df.empty or len(df) < 50:
            return None

        rsi = RSIIndicator(close=df["close"]).rsi().iloc[-1]
        ema20 = EMAIndicator(close=df["close"], window=20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(close=df["close"], window=50).ema_indicator().iloc[-1]
        preco = df["close"].iloc[-1]

        return {
            "Moeda": symbol.replace("USDT", ""),
            "Preço (USDT)": round(preco, 4),
            "RSI": round(rsi, 2),
            "Classificação RSI": classificar_rsi(rsi),
            "Tendência": classificar_tendencia(ema20, ema50),
            "Alerta": "🔔" if rsi <= 30 and ema20 > ema50 else ""
        }

    except Exception as e:
        print(f"Erro ao analisar {symbol}: {e}")
        return None

# ===== EXECUÇÃO =====
if executar_analise:
    with st.spinner("🔍 Analisando mercado..."):
        symbols = get_top_symbols_existentes_na_binance(limit=limite_moedas)

        resultados = []
        status_list = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_symbol = {executor.submit(analisar_moeda, sym): sym for sym in symbols}
            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result:
                        resultados.append(result)
                        status_list.append({"Moeda": symbol.replace("USDT", ""), "Status": "✅ Sucesso"})
                    else:
                        status_list.append({"Moeda": symbol.replace("USDT", ""), "Status": "❌ Erro na análise"})
                except Exception as e:
                    status_list.append({"Moeda": symbol.replace("USDT", ""), "Status": f"❌ Exceção: {str(e)}"})

    if status_list:
        status_df = pd.DataFrame(status_list)
        st.subheader("📦 Status da Análise das Moedas")
        st.dataframe(status_df, use_container_width=True)

    if resultados:
        df = pd.DataFrame(resultados)

        filtro_rsi = st.multiselect(
            "📌 Filtrar por classificação RSI",
            options=["Sobrevendida", "Neutra", "Sobrecomprada"],
            default=["Sobrevendida", "Neutra", "Sobrecomprada"]
        )
        df_filtrado = df[df["Classificação RSI"].isin(filtro_rsi)]

        st.subheader("📋 Resultado Geral")
        st.dataframe(df_filtrado, use_container_width=True)

        alertas = df_filtrado[df_filtrado["Alerta"] != ""]
        if not alertas.empty:
            st.subheader("🚨 Alertas Encontrados")
            st.dataframe(alertas, use_container_width=True)
        else:
            st.success("Nenhuma moeda com RSI ≤ 30 e tendência de alta no momento.")
    else:
        st.warning("⚠️ Nenhuma moeda retornou dados de análise.")
