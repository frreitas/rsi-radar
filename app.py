import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Radar RSI Simplificado", layout="wide")
st.title("📊 Análise Simplificada - TAAPI.IO")
st.markdown("Analisando pares fixos via TAAPI.IO: preço, RSI, EMA20 e EMA50")

API_KEY = st.secrets["TAAPI_KEY"]
intervalo = st.selectbox("⏱️ Intervalo", ["1h", "4h", "1d"], index=0)
atualizar = st.button("🔄 Atualizar análise")

PAIRS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "LTCUSDT", "XMRUSDT"]

def fetch_indicator(symbol, indicator):
    url = f"https://api.taapi.io/{indicator}"
    params = {
        "secret": API_KEY,
        "symbol": f"BINANCE:{symbol}",
        "interval": intervalo
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json().get("value")
        else:
            st.error(f"Erro {indicator} em {symbol}: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        st.error(f"Exceção em {indicator} - {symbol}: {e}")
        return None

def analisar(symbol):
    preco = fetch_indicator(symbol, "close")
    rsi = fetch_indicator(symbol, "rsi")
    ema20 = fetch_indicator(symbol, "ema")
    ema50 = fetch_indicator(symbol, "ema50")

    if None in (preco, rsi, ema20, ema50):
        return None

    tendencia = "Alta" if ema20 > ema50 else "Baixa" if ema20 < ema50 else "Neutra"
    alerta = "🔔" if rsi <= 30 and tendencia == "Alta" else ""
    rsi_class = "Sobrevendida" if rsi <= 30 else "Sobrecomprada" if rsi >= 70 else "Neutra"

    return {
        "Moeda": symbol.replace("USDT", ""),
        "Preço US$": round(preco, 4),
        "RSI": round(rsi, 2),
        "Classificação RSI": rsi_class,
        "EMA20": round(ema20, 2),
        "EMA50": round(ema50, 2),
        "Tendência": tendencia,
        "Alerta": alerta
    }

if atualizar:
    with st.spinner("⏳ Executando análise..."):
        resultados = []
        for symbol in PAIRS:
            res = analisar(symbol)
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
