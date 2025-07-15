import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Radar RSI TAAPI", layout="wide")
st.title("📊 Radar RSI & EMA com TAAPI.IO")
st.markdown("Indicadores técnicos em tempo real com TAAPI.IO e CoinGecko para preços.")

API_KEY = st.secrets["TAAPI_KEY"]

# Filtros de entrada
intervalo = st.selectbox("⏱️ Intervalo", ["1h", "4h", "1d"], index=0)
limite_moedas = st.selectbox("🏆 Top moedas", [20, 50, 100], index=2)
atualizar = st.button("🔄 Atualizar agora")

# CoinGecko – preços e variação
def get_top_coins(limit=100):
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
        return res.json()
    except Exception as e:
        st.error(f"Erro ao obter moedas do CoinGecko: {e}")
        return []

# Consulta individual de indicadores (TAAPI)
def fetch_indicator(symbol, indicator):
    url = f"https://api.taapi.io/{indicator}"
    params = {
        "secret": API_KEY,
        "symbol": f"BINANCE:{symbol}USDT",
        "interval": intervalo
    }
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

# Lógica de análise
def analisar(symbol, preco, variacao):
    st.write(f"🔍 Analisando: {symbol}")
    rsi = fetch_indicator(symbol, "rsi")
    ema20 = fetch_indicator(symbol, "ema")
    ema50 = fetch_indicator(symbol, "ema50")

    if None in (rsi, ema20, ema50):
        return None

    tendencia = "Alta" if ema20 > ema50 else "Baixa" if ema20 < ema50 else "Neutra"
    alerta = "🔔" if rsi <= 30 and tendencia == "Alta" else ""
    rsi_class = "Sobrevendida" if rsi <= 30 else "Sobrecomprada" if rsi >= 70 else "Neutra"

    return {
        "Moeda": symbol,
        "Preço US$": round(preco, 4),
        "Variação (%)": round(variacao or 0, 2),
        "RSI": round(rsi, 2),
        "Classificação RSI": rsi_class,
        "EMA20": round(ema20, 2),
        "EMA50": round(ema50, 2),
        "Tendência": tendencia,
        "Alerta": alerta
    }

# Execução principal
if atualizar:
    with st.spinner("⏳ Analisando mercado..."):
        moedas = get_top_coins(limit=limite_moedas)
        tarefas = [(m["symbol"].upper(), m["current_price"], m["price_change_percentage_24h"]) for m in moedas]

        resultados = []
        status = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futuros = {executor.submit(analisar, *args): args[0] for args in tarefas}
            for futuro in futuros:
                simbolo = futuros[futuro]
                try:
                    resultado = futuro.result()
                    if resultado:
                        resultados.append(resultado)
                        status.append({"Moeda": simbolo, "Status": "✅ Sucesso"})
                    else:
                        status.append({"Moeda": simbolo, "Status": "❌ Falha"})
                except Exception as e:
                    status.append({"Moeda": simbolo, "Status": f"❌ Erro: {e}"})

    # Status
    st.subheader("📦 Status da Análise")
    st.dataframe(pd.DataFrame(status), use_container_width=True)

    # Resultados principais
    if resultados:
        df = pd.DataFrame(resultados)

        filtro_rsi = st.multiselect(
            "🎯 Filtrar por RSI",
            options=["Sobrevendida", "Neutra", "Sobrecomprada"],
            default=["Sobrevendida", "Neutra", "Sobrecomprada"]
        )
        df_filtrado = df[df["Classificação RSI"].isin(filtro_rsi)]

        st.subheader("📋 Resultados da Análise")
        st.dataframe(df_filtrado, use_container_width=True)

        alertas = df_filtrado[df_filtrado["Alerta"] != ""]
        if not alertas.empty:
            st.subheader("🚨 Alertas de Oportunidade")
            st.dataframe(alertas, use_container_width=True)
        else:
            st.success("Nenhuma moeda com RSI ≤ 30 e tendência de alta.")
    else:
        st.warning("⚠️ Nenhum dado válido retornado.")
