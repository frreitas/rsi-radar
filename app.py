import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Radar RSI Cripto", layout="wide")
st.title("📊 Radar RSI com Tendência de Alta")
st.markdown("Análise das principais criptos com fallback da Binance para CoinGecko.")

# ===== Configurações =====
intervalo = st.selectbox("⏱️ Intervalo", ["1h", "4h", "1d"], index=0)
limite_velas = 100
limite_moedas = st.selectbox("🏆 Top moedas", [20, 50, 100], index=2)
atualizar = st.button("🔄 Atualizar agora")

# ===== APIs =====
@st.cache_data(ttl=600)
def get_top_coins(limit=limite_moedas):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": limit, "page":1}
    return requests.get(url, params=params, timeout=10).json()

def get_binance_klines(symbol):
    try:
        res = requests.get("https://api.binance.com/api/v3/klines",
                           params={"symbol":symbol,"interval":intervalo,"limit":limite_velas}, timeout=10)
        data = res.json()
        df = pd.DataFrame(data, columns=["timestamp","open","high","low","close","volume","close_time",
                                         "quote_asset_volume","number_of_trades","taker_buy_base","taker_buy_quote","ignore"])
        df["close"]=df["close"].astype(float)
        return df
    except:
        return None

def get_coingecko_ohlc(cg_id):
    days_map={"1h":1,"4h":7,"1d":14}
    try:
        res = requests.get(f"https://api.coingecko.com/api/v3/coins/{cg_id}/ohlc",
                           params={"vs_currency":"usd","days":days_map[intervalo]}, timeout=10)
        df = pd.DataFrame(res.json(), columns=["timestamp","open","high","low","close"])
        df["close"]=df["close"].astype(float)
        return df
    except:
        return None

def analisar(symbol, cg_id, current_price, price_change):
    df = get_binance_klines(symbol) or get_coingecko_ohlc(cg_id)
    if df is None or len(df)<50: return None
    rsi = RSIIndicator(df["close"]).rsi().iloc[-1]
    ema20 = EMAIndicator(df["close"],window=20).ema_indicator().iloc[-1]
    ema50 = EMAIndicator(df["close"],window=50).ema_indicator().iloc[-1]
    trend = "Alta" if ema20>ema50 else "Baixa" if ema20<ema50 else "Neutra"
    alert = "🔔" if rsi<=30 and trend=="Alta" else ""
    return {"Moeda":cg_id.upper(), "Preço US$":round(current_price,4),
            "Variação (%)":round(price_change,2),
            "RSI":round(rsi,2), "Tendência":trend, "Alerta":alert}

# ===== Execução =====
if atualizar:
    coins = get_top_coins()
    symbols = [(c["symbol"].upper()+"USDT",c["id"],c["current_price"],c["price_change_percentage_24h"]) for c in coins]

    results,status=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(analisar,*s):s for s in symbols}
        for f in futures:
            sym,id_,price,change=futures[f]
            res=f.result()
            status.append({"Moeda":id_.upper(),"Status":"✅OK" if res else "❌Erro"})
            if res: results.append(res)

    st.subheader("📦 Status da Análise")
    st.dataframe(pd.DataFrame(status),use_container_width=True)

    if results:
        df = pd.DataFrame(results)
        filt = st.multiselect("Filtrar RSI",["Sobrevendida","Neutra","Sobrecomprada"],default=["Sobrevendida","Neutra","Sobrecomprada"])
        df = df[(df["RSI"]<=30)&(filt and "Sobrevendida" in filt) |
                (df["RSI"]>=70)&(filt and "Sobrecomprada" in filt) |
                ((df["RSI"]>30)&(df["RSI"]<70)&(filt and "Neutra" in filt))]
        st.subheader("📋 Resultados")
        st.dataframe(df,use_container_width=True)
        alert=df[df["Alerta"]!=""]
        if not alert.empty:
            st.subheader("🚨 Alertas")
            st.dataframe(alert,use_container_width=True)
        else:
            st.success("Nenhuma moeda com RSI ≤30 e tendência de alta.")
    else:
        st.warning("⚠️ Nenhuma análise disponível.")
