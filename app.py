import streamlit as st
import requests
import pandas as pd
import io

st.set_page_config(page_title="Análise Técnica Manual Cripto", layout="centered")
st.title("📊 Análise Técnica Manual - Criptomoedas")

# === Inicializar estado da sessão ===
if "historico" not in st.session_state:
    st.session_state["historico"] = []

# === Lista de moedas disponíveis ===
moedas_disponiveis = {
    "Bitcoin (BTC)": "bitcoin",
    "Ethereum (ETH)": "ethereum",
    "Solana (SOL)": "solana",
    "XRP (XRP)": "ripple",
    "Cardano (ADA)": "cardano",
}

# === Função para pegar preço ===
def get_price(moeda_id):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": moeda_id, "vs_currencies": "usd"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()[moeda_id]["usd"]
    except Exception as e:
        st.warning(f"Erro ao obter preço: {e}")
        return None

# === RESET ===
if st.button("🧹 Limpar / Resetar tudo"):
    st.session_state["historico"] = []
    st.experimental_rerun()

# === SELEÇÃO DA MOEDA ===
st.subheader("🪙 Selecione a moeda")
moeda_nome = st.selectbox("Escolha uma moeda", list(moedas_disponiveis.keys()))
moeda_id = moedas_disponiveis[moeda_nome]
preco = get_price(moeda_id)

if preco:
    st.markdown(f"💰 **Preço atual de {moeda_nome}:** ${preco:,.2f}")
else:
    st.warning("Não foi possível obter o preço da moeda.")

# === INSERÇÃO MANUAL ===
st.subheader("✍️ Dados técnicos manuais")

rsi = st.number_input("RSI atual", min_value=0.0, max_value=100.0, step=0.1)

num_emas = st.selectbox("Quantas EMAs?", [1, 2, 3])
ema_vals = []
for i in range(num_emas):
    val = st.number_input(f"Valor da EMA {i+1}", min_value=0.0, step=0.1)
    ema_vals.append(val)

# === PROCESSAMENTO ===
if rsi <= 30:
    rsi_class = "Sobrevendida"
elif rsi >= 70:
    rsi_class = "Sobrecomprada"
else:
    rsi_class = "Neutra"

tendencia = "Indefinida"
if len(ema_vals) >= 2:
    if ema_vals[0] > ema_vals[1]:
        tendencia = "Alta"
    elif ema_vals[0] < ema_vals[1]:
        tendencia = "Baixa"
    else:
        tendencia = "Neutra"
elif len(ema_vals) == 1:
    tendencia = "Indefinida (só 1 EMA)"

# === RECOMENDAÇÃO ===
if rsi <= 30 and tendencia == "Alta":
    recomendacao = "🟢 Bom sinal de entrada"
elif tendencia == "Alta" and rsi_class == "Neutra":
    recomendacao = "🟡 Tendência de alta, mas RSI neutro"
elif tendencia == "Baixa":
    recomendacao = "🔴 Tendência de baixa - cautela"
else:
    recomendacao = "⚪ Sem sinal claro no momento"

# === MONTAR RESULTADO ===
resultado = {
    "Moeda": moeda_nome,
    "Preço Atual (USD)": round(preco, 2) if preco else "N/A",
    "RSI": rsi,
    "Classificação RSI": rsi_class,
    "Tendência": tendencia,
    "Recomendação": recomendacao
}
for i, ema in enumerate(ema_vals):
    resultado[f"EMA {i+1}"] = ema

# === ADICIONAR AO HISTÓRICO ===
if st.button("📌 Adicionar Análise ao Histórico"):
    st.session_state["historico"].append(resultado)
    st.success("Análise adicionada ao histórico!")

# === EXIBIR ÚLTIMA ANÁLISE ===
if resultado:
    st.subheader("📋 Resultado da Análise Atual")
    df_result = pd.DataFrame([resultado])
    st.dataframe(df_result, use_container_width=True)

    # === Exportar CSV ===
    csv = df_result.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar Resultado como CSV", data=csv, file_name="analise_manual.csv", mime="text/csv")

# === EXIBIR HISTÓRICO COMPLETO ===
if st.session_state["historico"]:
    st.subheader("📚 Histórico de Análises na Sessão")
    df_hist = pd.DataFrame(st.session_state["historico"])
    st.dataframe(df_hist, use_container_width=True)

    # Exportar histórico
    csv_hist = df_hist.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar Histórico como CSV", data=csv_hist, file_name="historico_analises.csv", mime="text/csv")
