import streamlit as st
import pandas as pd
import requests

# Importar os módulos completos e depois acessar as classes
import ta.momentum as ta_momentum
import ta.trend as ta_trend

import plotly.graph_objects as go
from datetime import datetime, timedelta
from plotly.subplots import make_subplots # Importar aqui para uso no gráfico

st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")

# --- Estilo CSS para visual limpo e profissional ---
st.markdown("""
<style>
.main .block-container {
    max-width: 1200px; /* Aumentar um pouco a largura máxima */
    padding: 1rem 2rem;
}
h1 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-weight: 700;
    color: #1e293b;
    text-align: center; /* Centralizar o título principal */
    margin-bottom: 0.5rem;
}
h2 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #334155;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
}
h3 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #475569;
    margin-top: 1rem;
    margin-bottom: 0.8rem;
}
h4 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #475569;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}
.stMetric {
    border-radius: 10px;
    box-shadow: 0 2px 6px rgb(0 0 0 / 0.1);
    background: #f9fafb;
    padding: 15px 20px;
    margin-bottom: 15px;
    text-align: center; /* Centralizar o conteúdo das métricas */
}
.analysis-container {
    background: #f3f4f6;
    padding: 20px 25px;
    border-radius: 12px;
    box-shadow: 0 3px 8px rgb(0 0 0 / 0.08);
    margin-top: 15px;
    margin-bottom: 20px;
}
.recommendation-card {
    border-radius: 14px;
    padding: 25px 30px;
    font-weight: 700;
    font-size: 28px;
    max-width: 500px; /* Aumentar um pouco a largura do card */
    margin: 30px auto; /* Mais margem para destaque */
    box-shadow: 0 5px 20px rgb(0 0 0 / 0.15); /* Sombra mais pronunciada */
    text-align: center;
    color: white;
    transition: transform 0.2s ease-in-out; /* Efeito hover */
}
.recommendation-card:hover {
    transform: translateY(-5px);
}
.rec-compra { background-color: #28a745; } /* Verde mais vibrante */
.rec-acumular { background-color: #ffc107; color: #333; } /* Amarelo, texto escuro */
.rec-agardar { background-color: #fd7e14; } /* Laranja */
.rec-venda { background-color: #dc3545; } /* Vermelho mais vibrante */
.rec-observar { background-color: #007bff; } /* Azul */
.rec-espera { background-color: #6c757d; } /* Cinza */
.rec-vendaparcial { background-color: #6f42c1; } /* Roxo */
.rec-default { background-color: #343a40; } /* Cinza escuro */
.gauge-container {
    max-width: 500px;
    margin: 0 auto 35px auto;
}
.stExpander {
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.05);
    margin-bottom: 15px;
}
.stExpander > div:first-child {
    padding: 10px 15px;
    background-color: #f8fafc;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Análise Técnica de Criptomoedas")
st.markdown("<p style='text-align: center; color: #64748b;'>Ferramenta de suporte à decisão para o mercado de criptoativos.</p>", unsafe_allow_html=True)

# --- Funções auxiliares (mantidas as mesmas, apenas a chamada é diferente) ---

@st.cache_data(ttl=3600)
def get_top_100_cryptos():
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=100&tsym=USD"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["Data"]
        return [f"{c['CoinInfo']['FullName']} ({c['CoinInfo']['Name']})" for c in data]
    except Exception as e:
        st.error(f"Erro ao buscar lista de criptomoedas: {e}. Usando lista padrão.")
        return ["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"]

def extrair_simbolo(moeda_str):
    return moeda_str.split("(")[-1].replace(")", "").strip()

@st.cache_data(ttl=600)
def get_timeframe_endpoint(timeframe):
    if timeframe == "1h":
        return "histohour", 2000
    elif timeframe == "4h":
        return "histohour", 2000
    elif timeframe in ["1d", "1w", "1M"]:
        return "histoday", 730
    else:
        return "histoday", 730

@st.cache_data(ttl=600)
def get_crypto_data(symbol, endpoint="histoday", limit=200):
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}?fsym={symbol}&tsym=USD&limit={limit}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()["Data"]["Data"]
        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"], unit='s')
        df = df.set_index("time")
        for col in ['open', 'high', 'low', 'close', 'volumefrom', 'volumeto']:
            if col in df.columns:
                df[col] = df[col].astype(float)
        df = df.rename(columns={'volumeto': 'volume'})
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados de {symbol} ({endpoint}, limit={limit}): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        valor = int(r.json()["data"][0]["value"])
        return valor
    except Exception as e:
        st.warning(f"Não foi possível obter o índice de Medo e Ganância: {e}")
        return None

def agrupar_4h_otimizado(df_horas):
    if df_horas.empty:
        return pd.DataFrame()
    df_horas = df_horas.sort_index()
    grouped = df_horas.resample('4H', origin='start_day').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    return grouped

def classificar_rsi(rsi):
    if rsi < 30: return "Sobrevendido"
    elif rsi > 70: return "Sobrecomprado"
    else: return "Neutro"

def classificar_tendencia(ema_fast, ema_medium, ema_slow, ema_long):
    if ema_fast is None or ema_medium is None or ema_slow is None or ema_long is None:
        return "Dados insuficientes para EMAs"
    if ema_fast > ema_medium > ema_slow > ema_long:
        return "Alta consolidada"
    elif ema_fast < ema_medium < ema_slow < ema_long:
        return "Baixa consolidada"
    return "Neutra/Transição"

def classificar_volume(v_atual, v_medio):
    return "Subindo" if v_atual >= v_medio else "Caindo"

def obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal):
    recomendacao = "Aguardar"

    # --- Cenários de Compra ---
    if tendencia == "Alta consolidada":
        if rsi_class == "Sobrevendido" and volume_class == "Subindo" and macd_signal == "Compra":
            recomendacao = "Compra Forte"
        elif rsi_class == "Neutro" and volume_class == "Subindo" and macd_signal == "Compra":
            recomendacao = "Compra"
        elif rsi_class == "Sobrevendido" and macd_signal == "Compra":
            recomendacao = "Acumular"

    elif tendencia == "Neutra/Transição":
        if rsi_class == "Sobrevendido" and volume_class == "Subindo" and macd_signal == "Compra":
            recomendacao = "Observar Reversão (Compra)"
        elif rsi_class == "Sobrevendido" and macd_signal == "Compra":
            recomendacao = "Observar"

    # --- Cenários de Venda ---
    if tendencia == "Baixa consolidada":
        if rsi_class == "Sobrecomprado" and volume_class == "Caindo" and macd_signal == "Venda":
            recomendacao = "Venda Forte"
        elif rsi_class == "Neutro" and volume_class == "Caindo" and macd_signal == "Venda":
            recomendacao = "Venda"
        elif rsi_class == "Sobrecomprado" and macd_signal == "Venda":
            recomendacao = "Venda Parcial / Evitar"

    elif tendencia == "Neutra/Transição":
        if rsi_class == "Sobrecomprado" and volume_class == "Caindo" and macd_signal == "Venda":
            recomendacao = "Observar Reversão (Venda)"
        elif rsi_class == "Sobrecomprado" and macd_signal == "Venda":
            recomendacao = "Observar"

    # --- Cenários de Consolidação / Indecisão ---
    if tendencia == "Neutra/Transição":
        if rsi_class == "Neutro" and volume_class == "Caindo":
            recomendacao = "Espera"
        elif rsi_class == "Neutro" and macd_signal == "Neutro":
            recomendacao = "Aguardar"

    # --- Cenários de Alerta / Evitar ---
    if tendencia == "Baixa consolidada":
        if volume_class == "Caindo" and macd_signal == "Venda":
            recomendacao = "Evitar"
        elif rsi_class == "Neutro" and volume_class == "Caindo":
            recomendacao = "Evitar"

    # --- Ajustes Finais para Casos Específicos ---
    if recomendacao == "Aguardar":
        if macd_signal == "Compra":
            recomendacao = "Aguardar Confirmação (MACD Compra)"
        elif macd_signal == "Venda":
            recomendacao = "Aguardar Confirmação (MACD Venda)"
        elif rsi_class == "Sobrevendido":
            recomendacao = "Aguardar Confirmação (RSI Sobrevendido)"
        elif rsi_class == "Sobrecomprado":
            recomendacao = "Aguardar Confirmação (RSI Sobrecomprado)"

    return recomendacao

def style_recomendacao_card(text):
    styles = {
        "Compra Forte": ("Compra Forte", "rec-compra"),
        "Compra": ("Compra", "rec-compra"),
        "Acumular": ("Acumular", "rec-acumular"),
        "Aguardar correção": ("Aguardar", "rec-agardar"),
        "Venda Forte": ("Venda Forte", "rec-venda"),
        "Venda": ("Venda", "rec-venda"),
        "Venda Parcial / Evitar": ("Venda Parcial", "rec-vendaparcial"),
        "Observar Reversão (Compra)": ("Observar Reversão", "rec-observar"),
        "Observar Reversão (Venda)": ("Observar Reversão", "rec-observar"),
        "Observar": ("Observar", "rec-observar"),
        "Espera": ("Espera", "rec-espera"),
        "Evitar": ("Evitar", "rec-venda"),
        "Aguardar": ("Aguardar", "rec-default"),
        "Aguardar Confirmação (MACD Compra)": ("Aguardar Confirmação", "rec-acumular"),
        "Aguardar Confirmação (MACD Venda)": ("Aguardar Confirmação", "rec-agardar"),
        "Aguardar Confirmação (RSI Sobrevendido)": ("Aguardar Confirmação", "rec-acumular"),
        "Aguardar Confirmação (RSI Sobrecomprado)": ("Aguardar Confirmação", "rec-agardar"),
    }
    return styles.get(text, ("Desconhecido", "rec-default"))

# --- Interface ---

# Controles de seleção no topo
col_select_moeda, col_select_timeframe = st.columns([2, 1])
with col_select_moeda:
    moeda_selecionada = st.selectbox("Selecione a Moeda", get_top_100_cryptos(), help="Escolha a criptomoeda para análise técnica.")
    simbolo = extrair_simbolo(moeda_selecionada)
with col_select_timeframe:
    timeframe_analise = st.selectbox("Timeframe de Análise", ["1h", "4h", "1d", "1w"], index=2, help="Define o período de cada vela para os indicadores e gráficos.")

# Expander para configurações de EMAs
with st.expander("⚙️ Configurações Avançadas de EMAs"):
    st.markdown("Ajuste os períodos das Médias Móveis Exponenciais (EMAs) para personalizar a análise de tendência.")
    col_ema1, col_ema2, col_ema3, col_ema4 = st.columns(4)
    with col_ema1:
        ema_fast_period = st.number_input("EMA Rápida", min_value=5, max_value=20, value=8, step=1, help="Período da EMA mais sensível ao preço.")
    with col_ema2:
        ema_medium_period = st.number_input("EMA Média", min_value=15, max_value=30, value=21, step=1, help="Período da EMA intermediária.")
    with col_ema3:
        ema_slow_period = st.number_input("EMA Lenta", min_value=40, max_value=70, value=56, step=1, help="Período da EMA que indica tendência de médio prazo.")
    with col_ema4:
        ema_long_period = st.number_input("EMA Longa", min_value=150, max_value=250, value=200, step=1, help="Período da EMA que indica tendência de longo prazo.")

st.divider()

st.subheader(f"Sumário da Análise para {moeda_selecionada}")

with st.spinner("Carregando dados e calculando indicadores..."):
    endpoint_analise, limit_analise = get_timeframe_endpoint(timeframe_analise)
    df_analise_raw = get_crypto_data(simbolo, endpoint_analise, limit_analise)

    if df_analise_raw.empty:
        st.error("Dados insuficientes para análise. Tente novamente mais tarde ou selecione outro timeframe/moeda.")
        st.stop()

    if timeframe_analise == "4h":
        df_analise = agrupar_4h_otimizado(df_analise_raw)
    elif timeframe_analise == "1w":
        df_analise = df_analise_raw.resample('W-MON').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
        }).dropna()
    else:
        df_analise = df_analise_raw.copy()

    # --- Cálculo de Indicadores ---
    # Inicialização de variáveis para evitar NameError em caso de dados insuficientes
    preco_atual, variacao_periodo, volume_atual, volume_medio = 0.0, 0.0, 0.0, 0.0
    rsi_valor, rsi_class = 50.0, "Neutro"
    macd_line, macd_signal_line, macd_diff, macd_signal = 0.0, 0.0, 0.0, "Neutro"
    ema_fast, ema_medium, ema_slow, ema_long = None, None, None, None
    tendencia = "Dados insuficientes para EMAs"
    volume_class = "Neutro"
    recomendacao = "Aguardar"
    texto_card, classe_card = style_recomendacao_card(recomendacao)

    if df_analise.empty or len(df_analise) < max(ema_long_period, 200):
        st.warning(f"Dados insuficientes para o timeframe '{timeframe_analise}' ou para calcular todas as EMAs. Tente um timeframe maior ou outra moeda.")
        # A execução continua com os valores padrão inicializados acima
    else:
        preco_atual = df_analise["close"].iloc[-1]
        if len(df_analise) > 1:
            preco_anterior = df_analise["close"].iloc[-2]
            variacao_periodo = (preco_atual - preco_anterior) / preco_anterior * 100
        
        volume_atual = df_analise["volume"].iloc[-1]
        volume_medio = df_analise["volume"].mean()

        rsi_valor = ta_momentum.RSIIndicator(close=df_analise["close"], window=14).rsi().iloc[-1]
        rsi_class = classificar_rsi(rsi_valor)

        macd_indicator = ta_trend.MACD(close=df_analise["close"])
        macd_line = macd_indicator.macd().iloc[-1]
        macd_signal_line = macd_indicator.macd_signal().iloc[-1]
        macd_diff = macd_indicator.macd_diff().iloc[-1]
        if macd_line > macd_signal_line and macd_diff > 0:
            macd_signal = "Compra"
        elif macd_line < macd_signal_line and macd_diff < 0:
            macd_signal = "Venda"

        ema_fast = ta_trend.EMAIndicator(close=df_analise["close"], window=ema_fast_period).ema_indicator().iloc[-1]
        ema_medium = ta_trend.EMAIndicator(close=df_analise["close"], window=ema_medium_period).ema_indicator().iloc[-1]
        ema_slow = ta_trend.EMAIndicator(close=df_analise["close"], window=ema_slow_period).ema_indicator().iloc[-1]
        ema_long = ta_trend.EMAIndicator(close=df_analise["close"], window=ema_long_period).ema_indicator().iloc[-1]
        tendencia = classificar_tendencia(ema_fast, ema_medium, ema_slow, ema_long)

        volume_class = classificar_volume(volume_atual, volume_medio)
        recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal)
        texto_card, classe_card = style_recomendacao_card(recomendacao)

# --- Exibição de Métricas Principais ---
col_preco, col_volume_atual, col_volume_medio = st.columns(3)
with col_preco:
    st.metric("💵 Preço Atual (USD)", f"${preco_atual:,.2f}", f"{variacao_periodo:.2f}% ({timeframe_analise})")
with col_volume_atual:
    st.metric("📊 Volume Atual", f"${volume_atual:,.2f}")
with col_volume_medio:
    st.metric("📉 Volume Médio", f"${volume_medio:,.2f}")

st.markdown(f"""
<div class="recommendation-card {classe_card}">
    {texto_card}
</div>
""", unsafe_allow_html=True)

# Expander para Análise Técnica Detalhada
with st.expander("🔍 Análise Técnica Detalhada"):
    st.markdown(f"""
    <div class="analysis-container">
        <h4>Tendência (EMAs {ema_fast_period}/{ema_medium_period}/{ema_slow_period}/{ema_long_period} {timeframe_analise}): <strong>{tendencia}</strong></h4>
        <p style='font-size:0.9rem; color:#64748b;'>A tendência é determinada pela ordem das Médias Móveis Exponenciais. Uma sequência crescente (EMA Rápida > Média > Lenta > Longa) indica alta consolidada, e vice-versa para baixa.</p>
        <h4>RSI ({timeframe_analise}): <strong>{rsi_valor:.2f} – {rsi_class}</strong></h4>
        <p style='font-size:0.9rem; color:#64748b;'>O Índice de Força Relativa (RSI) mede a velocidade e a mudança dos movimentos de preço. Valores abaixo de 30 indicam sobrevenda, acima de 70 indicam sobrecompra.</p>
        <h4>MACD ({timeframe_analise}): <strong>Linha: {macd_line:.2f}, Sinal: {macd_signal_line:.2f}, Histograma: {macd_diff:.2f} – {macd_signal}</strong></h4>
        <p style='font-size:0.9rem; color:#64748b;'>O Moving Average Convergence Divergence (MACD) revela a relação entre duas médias móveis de preço. Cruzamentos da linha MACD com a linha de sinal e o histograma indicam momentum e possíveis reversões.</p>
        <h4>Volume Atual vs. Médio: <strong>{volume_class}</strong></h4>
        <p style='font-size:0.9rem; color:#64748b;'>O volume de negociação reflete a força por trás dos movimentos de preço. Um volume crescente em uma tendência confirma sua validade.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- Gráficos ---
st.subheader(f"Visualização Gráfica para {moeda_selecionada}")

if not df_analise.empty and len(df_analise) > 1:
    tab_candlestick, tab_indicators = st.tabs(["Gráfico de Velas e EMAs", "RSI e MACD"])

    with tab_candlestick:
        fig_chart = go.Figure(data=[go.Candlestick(
            x=df_analise.index,
            open=df_analise['open'],
            high=df_analise['high'],
            low=df_analise['low'],
            close=df_analise['close'],
            name='Preço'
        )])

        if ema_fast is not None:
            fig_chart.add_trace(go.Scatter(x=df_analise.index, y=ta_trend.EMAIndicator(close=df_analise["close"], window=ema_fast_period).ema_indicator(),
                                       mode='lines', name=f'EMA {ema_fast_period}', line=dict(color='orange', width=1)))
            fig_chart.add_trace(go.Scatter(x=df_analise.index, y=ta_trend.EMAIndicator(close=df_analise["close"], window=ema_medium_period).ema_indicator(),
                                       mode='lines', name=f'EMA {ema_medium_period}', line=dict(color='purple', width=1)))
            fig_chart.add_trace(go.Scatter(x=df_analise.index, y=ta_trend.EMAIndicator(close=df_analise["close"], window=ema_slow_period).ema_indicator(),
                                       mode='lines', name=f'EMA {ema_slow_period}', line=dict(color='brown', width=1)))
            fig_chart.add_trace(go.Scatter(x=df_analise.index, y=ta_trend.EMAIndicator(close=df_analise["close"], window=ema_long_period).ema_indicator(),
                                       mode='lines', name=f'EMA {ema_long_period}', line=dict(color='blue', width=1)))

        fig_chart.update_layout(
            xaxis_rangeslider_visible=False,
            title=f'Gráfico de Velas e EMAs ({timeframe_analise})',
            height=500,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_chart, use_container_width=True)

    with tab_indicators:
        fig_subplots = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                     vertical_spacing=0.1,
                                     row_heights=[0.5, 0.5],
                                     subplot_titles=("RSI (Relative Strength Index)", "MACD (Moving Average Convergence Divergence)"))

        fig_subplots.add_trace(go.Scatter(x=df_analise.index, y=ta_momentum.RSIIndicator(close=df_analise["close"], window=14).rsi(),
                                          mode='lines', name='RSI', line=dict(color='green')), row=1, col=1)
        fig_subplots.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecomprado", annotation_position="top right", row=1, col=1)
        fig_subplots.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobrevendido", annotation_position="bottom right", row=1, col=1)
        fig_subplots.update_yaxes(range=[0, 100], title_text="RSI", row=1, col=1)

        fig_subplots.add_trace(go.Scatter(x=df_analise.index, y=ta_trend.MACD(close=df_analise["close"]).macd(),
                                          mode='lines', name='MACD Linha', line=dict(color='blue')), row=2, col=1)
        fig_subplots.add_trace(go.Scatter(x=df_analise.index, y=ta_trend.MACD(close=df_analise["close"]).macd_signal(),
                                          mode='lines', name='MACD Sinal', line=dict(color='red')), row=2, col=1)
        fig_subplots.add_trace(go.Bar(x=df_analise.index, y=ta_trend.MACD(close=df_analise["close"]).macd_diff(),
                                       name='MACD Histograma', marker_color='gray'), row=2, col=1)
        fig_subplots.update_yaxes(title_text="MACD", row=2, col=1)

        fig_subplots.update_layout(
            height=600, # Aumentar altura para melhor visualização dos subplots
            showlegend=True,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_subplots, use_container_width=True)
else:
    st.info("Não há dados suficientes para exibir os gráficos.")

st.divider()

# --- Gráfico Gauge Fear & Greed Index ---
st.subheader("Sentimento de Mercado: Índice de Medo e Ganância")
fng_valor = get_fear_greed_index()

if fng_valor is not None:
    fig_fng = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = fng_valor,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Índice de Medo e Ganância"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"},
            'steps' : [
                {'range': [0, 25], 'color': "#d62728"}, # Extreme Fear
                {'range': [25, 50], 'color': "#ff7f0e"}, # Fear
                {'range': [50, 75], 'color': "#bcbd22"}, # Greed
                {'range': [75, 100], 'color': "#2ca02c"}], # Extreme Greed
            'threshold' : {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': fng_valor}}))

    st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_fng, use_container_width=True)
    st.markdown("""
    <div style="text-align:center; font-size: 14px; color: #64748b; margin-bottom: 35px;">
        <p>Este índice mede o sentimento atual do mercado de criptomoedas. Valores mais baixos indicam medo (oportunidade de compra), enquanto valores mais altos indicam ganância (oportunidade de venda).</p>
        <strong>0-25: Medo Extremo | 25-50: Medo | 50-75: Ganância | 75-100: Ganância Extrema</strong>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Não foi possível obter o índice de Medo e Ganância no momento. Verifique sua conexão ou tente novamente mais tarde.")
        # Calcular indicadores
        rsi_valor = ta_momentum.RSIIndicator(close=df_analise_raw["close"], window=14).rsi().iloc[-1]
        rsi_class = classificar_rsi(rsi_valor)
        # Calcular EMAs
        ema_fast = ta_trend.EMAIndicator(close=df_analise_raw["close"], window=ema_fast_period).ema_indicator().iloc[-1]
        ema_medium = ta_trend.EMAIndicator(close=df_analise_raw["close"], window=ema_medium_period).ema_indicator().iloc[-1]
        ema_slow = ta_trend.EMAIndicator(close=df_analise_raw["close"], window=ema_slow_period).ema_indicator().iloc[-1]
        ema_long = ta_trend.EMAIndicator(close=df_analise_raw["close"], window=ema_long_period).ema_indicator().iloc[-1]
        tendencia = classificar_tendencia(ema_fast, ema_medium, ema_slow, ema_long)
        # Calcular volume
        volume_atual = df_analise_raw["volume"].iloc[-1]
        volume_medio = df_analise_raw["volume"].mean()
        volume_class = classificar_volume(volume_atual, volume_medio)
        # Verificar se a moeda atende aos critérios de filtragem
        if (not tendencia_opcoes or tendencia in tendencia_opcoes) and \
           (not rsi_opcoes or rsi_class in rsi_opcoes) and \
           (not volume_opcoes or volume_class in volume_opcoes):
            moedas_filtradas.append(moeda)
    # Exibir resultados
    if moedas_filtradas:
        st.success(f"Moedas que atendem aos critérios: {', '.join(moedas_filtradas)}")
    else:
        st.warning("Nenhuma moeda atende aos critérios selecionados.")
