import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Radar RSI Corrigido", layout="wide")
st.title("📊 Análise Simplificada TAAPI + CoinGecko")
st.markdown("RSI e EMAs via TAAPI.IO; Preço e variação via CoinGecko")

API_KEY = st.secrets["TAAPI_KEY"]
intervalo = st.selectbox("⏱️ Intervalo", ["1h", "4h", "1d"], index=0)
atualizar = st.button("🔄 Atualizar análise")

PAIRS = ["BTC/USDT", "ETH/USDT", "XRP/USDT", "LTC/USDT", "XMR/USDT"]

def fetch_indicator(symbol, indicator, optInTimePeriod=None):
    url = f"https://api.taapi.io/{indicator}"
    params = {
        "secret": API_KEY,
        "exchange": "binance",
        "symbol": f"BINANCE:{symbol}",
        "interval": intervalo
    }
    if optInTimePeriod:
        params["optInTimePeriod"] = optInTimePeriod
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json().get("value")
        else:
            st.error(f"Erro {indicator} para {symbol}: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        st.error(f"Exceção em {indicator} - {symbol}: {e}")
        return None

# Mapear pares para ids do CoinGecko (sem /USDT)
mapping_cg = {
    "BTC/USDT": "bitcoin",
    "ETH/USDT": "ethereum",
    "XRP/USDT": "ripple",
    "LTC/USDT": "litecoin",
    "XMR/USDT": "monero"
}

def get_prices(symbols):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(symbols),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro ao obter preços do CoinGecko: {e}")
        return {}

def analisar(symbol, price_data):
    preco = price_data.get(mapping_cg[symbol], {}).get("usd")
    variacao = price_data.get(mapping_cg[symbol], {}).get("usd_24h_change")

    rsi = fetch_indicator(symbol, "rsi")
    ema20 = fetch_indicator(symbol, "ema", optInTimePeriod=20)
    ema50 = fetch_indicator(symbol, "ema", optInTimePeriod=50)

    if None in (preco, variacao, rsi, ema20, ema50):
        return None

    tendencia = "Alta" if ema20 > ema50 else "Baixa" if ema20 < ema50 else "Neutra"
    alerta = "🔔" if rsi <= 30 and tendencia == "Alta" else ""
    rsi_class = "Sobrevendida" if rsi <= 30 else "Sobrecomprada" if rsi >= 70 else "Neutra"

    return {
        "Moeda": symbol,
        "Preço US$": round(preco, 4),
        "Variação (%)": round(variacao, 2),
        "RSI": round(rsi, 2),
        "Classificação RSI": rsi_class,
        "EMA20": round(ema20, 2),
        "EMA50": round(ema50, 2),
        "Tendência": tendencia,
        "Alerta": alerta
    }

if atualizar:
    with st.spinner("⏳ Executando análise..."):
        price_data = get_prices(list(mapping_cg.values()))
        resultados = []
        for symbol in PAIRS:
            res = analisar(symbol, price_data)
            if res:
                resultados.append(res)
            else:
                st.warning(f"Não foi possível analisar {symbol}")

    if resultados:
        df = pd.DataFrame(resultados)
        filtro_rsi = st.multiselect(
            "🎯 Filtrar RSI",
            options=["Sobrevendida", "Neutra", "Sobrecomprada"],
            default=["Sobrevendida", "Neutra", "Sobrecomprada"]
        )
        df_filtrado = df[df["Classificação RSI"].isin(filtro_rsi)]

        st.subheader("📋 Resultados")
        st.dataframe(df_filtrado, use_container_width=True)

        alertas = df_filtrado[df_filtrado["Alerta"] != ""]
        if not alertas.empty:
            st.subheader("🚨 Alertas")
            st.dataframe(alertas, use_container_width=True)
        else:
            st.success("Nenhuma moeda com RSI ≤ 30 e tendência de alta no momento.")
    else:
        st.warning("Nenhum resultado válido retornado.")
