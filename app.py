import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Radar RSI TAAPI", layout="wide")
st.title("📊 Radar RSI & EMA via TAAPI.IO")
st.markdown("Use TAAPI.IO para obter dados: preço, variação, RSI, EMA20 e EMA50 em um único call.")

API_KEY = st.secrets["TAAPI_KEY"]

intervalo = st.selectbox("⏱️ Intervalo", ["1h", "4h", "1d"], index=0)
limite_moedas = st.selectbox("🏆 Top moedas", [20, 50, 100], index=2)
atualizar = st.button("🔄 Atualizar agora")

def fetch_indicator(symbol, indicator):
    url = f"https://api.taapi.io/{indicator}"
    params = {"secret": API_KEY, "exchange": "binance", "symbol": symbol+"USDT", "interval": intervalo}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code == 200:
        return r.json().get("value")
    else:
        st.error(f"Erro TAAPI {indicator} em {symbol}: {r.status_code}")
        return None

def analisar(symbol, price, change):
    rsi = fetch_indicator(symbol, "rsi")
    ema20 = fetch_indicator(symbol, "ema",)
    ema50 = fetch_indicator(symbol, "ema50")
    if None in (rsi, ema20, ema50):
        return None
    trend = "Alta" if ema20>ema50 else "Baixa" if ema20<ema50 else "Neutra"
    alert = "🔔" if rsi<=30 and trend=="Alta" else ""
    return {
        "Moeda": symbol,
        "Preço US$": round(price,4),
        "Variação (%)": round(change,2),
        "RSI": round(rsi,2),
        "EMA20": round(ema20,2),
        "EMA50": round(ema50,2),
        "Tendência": trend,
        "Alerta": alert
    }

if atualizar:
    coins = requests.get("https://api.coingecko.com/api/v3/coins/markets",
                         params={"vs_currency":"usd","order":"market_cap_desc","per_page":limite_moedas,"page":1}).json()
    tasks = [(c["symbol"].upper(), c["current_price"], c["price_change_percentage_24h"]) for c in coins]

    results, status = [], []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(analisar, *t): t[0] for t in tasks}
        for f in futures:
            sym = futures[f]
            res = f.result()
            if res:
                results.append(res)
                status.append({"Moeda": sym, "Status": "✅ Sucesso"})
            else:
                status.append({"Moeda": sym, "Status": "❌ Erro"})

    st.subheader("📦 Status da Análise")
    st.dataframe(pd.DataFrame(status), use_container_width=True)

    if results:
        df = pd.DataFrame(results)
        filtro = st.multiselect("📌 Filtrar RSI", ["Sobrevendida","Neutra","Sobrecomprada"],
                                default=["Sobrevendida","Neutra","Sobrecomprada"])
        df["Classificação RSI"] = df["RSI"].apply(lambda x: "Sobrevendida" if x<=30 else "Sobrecomprada" if x>=70 else "Neutra")
        df = df[df["Classificação RSI"].isin(filtro)]
        st.subheader("📋 Resultados")
        st.dataframe(df, use_container_width=True)
        alert = df[df["Alerta"]!=""]
        if not alert.empty:
            st.subheader("🚨 Alertas")
            st.dataframe(alert, use_container_width=True)
        else:
            st.success("Nenhuma oportunidade no momento.")
    else:
        st.warning("Nenhum dado válido retornado!")
