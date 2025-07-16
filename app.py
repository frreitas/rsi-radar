import streamlit as st
import pandas as pd
import requests
import ta.momentum as ta_momentum
import ta.trend as ta_trend
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")

# --- Estilo CSS ---
css = """
<style>
.main .block-container {
    max-width: 1200px;
    padding: 1rem 2rem;
}
h1 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-weight: 700;
    color: #1e293b;
    text-align: center;
}
.stMetric {
    border-radius: 10px;
    box-shadow: 0 2px 6px rgb(0 0 0 / 0.1);
    background: #f9fafb;
    padding: 15px 20px;
    margin-bottom: 15px;
}
.analysis-container {
    background: #f3f4f6;
    padding: 20px 25px;
    border-radius: 12px;
    box-shadow: 0 3px 8px rgb(0 0 0 / 0.08);
    margin-top: 15px;
}
.recommendation-card {
    border-radius: 14px;
    padding: 25px 30px;
    font-weight: 700;
    font-size: 28px;
    max-width: 500px;
    margin: 30px auto;
    box-shadow: 0 5px 20px rgb(0 0 0 / 0.12);
    text-align: center;
    color: white;
}
.rec-compra { background-color: #28a745; }
.rec-acumular { background-color: #ffc107; color: #333; }
.rec-agardar { background-color: #fd7e14; }
.rec-venda { background-color: #dc3545; }
.rec-observar { background-color: #007bff; }
.rec-espera { background-color: #6c757d; }
.rec-vendaparcial { background-color: #6f42c1; }
.gauge-container {
    max-width: 500px;
    margin: 0 auto 35px auto;
}
.selection-section {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 25px;
}
.analysis-details {
    margin: 15px 0;
    line-height: 1.6;
}
.analysis-details h4 {
    margin: 10px 0 5px 0;
    font-size: 16px;
    color: #2F4F4F;
    font-weight: 600;
}
.analysis-details p {
    margin: 5px 0;
    font-size: 14px;
    color: #555;
}
.analysis-details strong {
    color: #1e293b;
}
@media (max-width: 768px) {
    .filter-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- Funções Auxiliares ---
@st.cache_data(ttl=3600)
def get_top_100_cryptos():
    """Busca as 100 principais criptomoedas"""
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=100&tsym=USD"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["Data"]
        return [f"{c['CoinInfo']['FullName']} ({c['CoinInfo']['Name']})" for c in data]
    except Exception as e:
        st.error(f"Erro ao buscar lista de criptomoedas: {e}")
        return ["Bitcoin (BTC)", "Ethereum (ETH)", "Binance Coin (BNB)"]

def extrair_simbolo(moeda_str):
    """Extrai o símbolo da criptomoeda"""
    return moeda_str.split("(")[-1].replace(")", "").strip()

@st.cache_data(ttl=600)
def get_timeframe_endpoint(timeframe):
    """Mapeia timeframe para endpoint da API"""
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
    """Busca dados históricos de criptomoedas"""
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
        st.error(f"Erro ao buscar dados de {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_fear_greed_index():
    """Obtém o índice de Medo e Ganância"""
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return int(r.json()["data"][0]["value"])
    except Exception as e:
        st.warning(f"Erro ao buscar índice: {e}")
        return None

def agrupar_4h_otimizado(df_horas):
    """Agrupa dados de 1h em 4h"""
    if df_horas.empty:
        return pd.DataFrame()
    return df_horas.resample('4H', origin='start_day').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

def classificar_rsi(rsi):
    """Classifica o valor do RSI"""
    if rsi < 30: return "Sobrevendido"
    elif rsi > 70: return "Sobrecomprado"
    else: return "Neutro"

def classificar_tendencia(ema_fast, ema_medium, ema_slow, ema_long):
    """Classifica a tendência com base nas EMAs"""
    if None in [ema_fast, ema_medium, ema_slow, ema_long]:
        return "Dados insuficientes"
    if ema_fast > ema_medium > ema_slow > ema_long:
        return "Alta consolidada"
    elif ema_fast < ema_medium < ema_slow < ema_long:
        return "Baixa consolidada"
    return "Neutra/Transição"

def classificar_volume(v_atual, v_medio):
    """Compara volume atual com médio"""
    return "Subindo" if v_atual >= v_medio else "Caindo"

def obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal):
    """Gera recomendação com base nos indicadores"""
    if tendencia == "Alta consolidada":
        if rsi_class == "Sobrevendido" and volume_class == "Subindo" and macd_signal == "Compra":
            return "Compra Forte"
        elif rsi_class == "Neutro" and volume_class == "Subindo" and macd_signal == "Compra":
            return "Compra"
        elif rsi_class == "Sobrecomprado" and volume_class == "Subindo":
            return "Aguardar correção"
    elif tendencia == "Baixa consolidada":
        if rsi_class == "Sobrevendido" and volume_class == "Subindo" and macd_signal == "Compra":
            return "Observar reversão"
        elif volume_class == "Caindo" or macd_signal == "Venda":
            return "Venda / Evitar"
    return "Aguardar"

def style_recomendacao_card(text):
    """Estiliza o card de recomendação"""
    styles = {
        "Compra Forte": ("Compra Forte", "rec-compra"),
        "Compra": ("Compra", "rec-compra"),
        "Aguardar correção": ("Aguardar correção", "rec-agardar"),
        "Venda / Evitar": ("Venda", "rec-venda"),
        "Observar reversão": ("Observar", "rec-observar"),
        "Aguardar": ("Aguardar", "rec-espera"),
    }
    return styles.get(text, (text, "rec-default"))

# --- Interface Principal ---
def main():
    st.title("📊 Análise Técnica de Criptomoedas")
    
    # Seção de moeda e timeframe
    with st.container():
        st.markdown('<div class="selection-section">', unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            moeda_selecionada = st.selectbox(
                "Selecione a Moeda",
                get_top_100_cryptos(),
                key="main_coin_select"
            )
            simbolo = extrair_simbolo(moeda_selecionada)
        
        with col2:
            timeframe_analise = st.selectbox(
                "Timeframe Análise",
                ["1h", "4h", "1d", "1w"],
                index=2,
                key="main_timeframe"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Processamento dos dados
    with st.spinner(f"Carregando dados de {moeda_selecionada}..."):
        endpoint_analise, limit_analise = get_timeframe_endpoint(timeframe_analise)
        df_analise_raw = get_crypto_data(simbolo, endpoint_analise, limit_analise)
        
        if df_analise_raw.empty:
            st.error("Dados insuficientes para análise")
            st.stop()
            
        if timeframe_analise == "4h":
            df_analise = agrupar_4h_otimizado(df_analise_raw)
        else:
            df_analise = df_analise_raw
            
        # Calcular indicadores
        preco_atual = df_analise["close"].iloc[-1]
        variacao = ((df_analise["close"].iloc[-1] - df_analise["close"].iloc[-2]) / 
                   df_analise["close"].iloc[-2] * 100) if len(df_analise) > 1 else 0
        volume_atual = df_analise["volume"].iloc[-1]
        volume_medio = df_analise["volume"].mean()
        rsi = ta_momentum.RSIIndicator(df_analise["close"], 14).rsi().iloc[-1]
        rsi_class = classificar_rsi(rsi)
        
        macd = ta_trend.MACD(df_analise["close"])
        macd_line = macd.macd().iloc[-1]
        macd_signal_line = macd.macd_signal().iloc[-1]
        macd_diff = macd.macd_diff().iloc[-1]
        macd_signal = "Compra" if macd_line > macd_signal_line else "Venda"
        
        ema_periods = [8, 21, 50, 200]
        emas = {
            f"ema_{period}": ta_trend.EMAIndicator(df_analise["close"], period).ema_indicator().iloc[-1]
            if len(df_analise) > period else None
            for period in ema_periods
        }
        
        tendencia = classificar_tendencia(emas["ema_8"], emas["ema_21"], emas["ema_50"], emas["ema_200"])
        volume_class = classificar_volume(volume_atual, volume_medio)
        recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal)
        texto_card, classe_card = style_recomendacao_card(recomendacao)

    # Métricas principais
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Preço Atual", f"${preco_atual:,.2f}", f"{variacao:+.2f}%")
    col2.metric("📊 Volume 24h", f"${volume_atual:,.0f}", 
               f"{'↑' if volume_class == 'Subindo' else '↓'} {abs((volume_atual/volume_medio-1)*100):.1f}% vs média" 
               if volume_medio > 0 else "")
    col3.metric("📉 RSI (14)", f"{rsi:.1f}", rsi_class)

    # Card de recomendação
    st.markdown(f"""
    <div class="recommendation-card {classe_card}">
        {texto_card}
    </div>
    """, unsafe_allow_html=True)

    # Análise detalhada
    with st.expander("🔍 Detalhes da Análise", expanded=True):
        st.markdown(f"""
        <div class="analysis-container">
            <div class="analysis-details">
                <h4>Tendência</h4>
                <p><strong>{tendencia}</strong></p>
                <p>EMA (8): <strong>${emas['ema_8']:,.2f}</strong> | EMA (21): <strong>${emas['ema_21']:,.2f}</strong></p>
                <p>EMA (50): <strong>${emas['ema_50']:,.2f}</strong> | EMA (200): <strong>${emas['ema_200']:,.2f}</strong></p>
            </div>
            
            <div class="analysis-details">
                <h4>Momentum</h4>
                <p>RSI: <strong>{rsi:.1f}</strong> ({rsi_class})</p>
                <p>MACD: <strong>{macd_line:,.2f}</strong> | Sinal: <strong>{macd_signal_line:,.2f}</strong></p>
                <p>Histograma: <strong>{macd_diff:,.2f}</strong> | Sinal: <strong>{macd_signal}</strong></p>
            </div>
            
            <div class="analysis-details">
                <h4>Volume</h4>
                <p>Atual: <strong>${volume_atual:,.0f}</strong></p>
                <p>Média: <strong>${volume_medio:,.0f}</strong></p>
                <p>Tendência: <strong>{volume_class}</strong></p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Gráficos
    tab1, tab2 = st.tabs(["📊 Gráfico de Velas", "📈 Indicadores Técnicos"])
    
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_analise.index,
            open=df_analise['open'],
            high=df_analise['high'],
            low=df_analise['low'],
            close=df_analise['close'],
            name='Preço',
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444'
        ))
        
        for period, color in zip([8, 21, 50, 200], ['orange', 'purple', 'blue', 'red']):
            if emas[f"ema_{period}"] is not None:
                ema_values = ta_trend.EMAIndicator(df_analise["close"], period).ema_indicator()
                fig.add_trace(go.Scatter(
                    x=df_analise.index,
                    y=ema_values,
                    name=f'EMA {period}',
                    line=dict(color=color, width=1),
                    opacity=0.8
                ))
        
        fig.update_layout(
            title=f"{moeda_selecionada} - Gráfico de Velas ({timeframe_analise})",
            xaxis_rangeslider_visible=False,
            height=500,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        
        # RSI
        fig.add_trace(go.Scatter(
            x=df_analise.index,
            y=ta_momentum.RSIIndicator(df_analise["close"], 14).rsi(),
            name='RSI',
            line=dict(color='#4f46e5')
        ), row=1, col=1)
        
        fig.add_hline(y=30, line_dash="dash", line_color="#10b981", 
                     annotation_text="Sobrevendido", row=1, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", 
                     annotation_text="Sobrecomprado", row=1, col=1)
        
        # MACD
        macd = ta_trend.MACD(df_analise["close"])
        fig.add_trace(go.Scatter(
            x=df_analise.index,
            y=macd.macd(),
            name='MACD',
            line=dict(color='#2563eb')
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=df_analise.index,
            y=macd.macd_signal(),
            name='Sinal',
            line=dict(color='#f59e0b')
        ), row=2, col=1)
        
        fig.add_trace(go.Bar(
            x=df_analise.index,
            y=macd.macd_diff(),
            name='Histograma',
            marker_color='#d1d5db'
        ), row=2, col=1)
        
        fig.update_layout(
            height=600,
            showlegend=True,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Índice de Medo e Ganância
    st.divider()
    st.subheader("🌡️ Índice de Medo e Ganância do Mercado")
    
    fng = get_fear_greed_index()
    if fng is not None:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=fng,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Medo e Ganância (hoje)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "#ef4444"},  # Medo extremo
                    {'range': [25, 50], 'color': "#f59e0b"}, # Medo
                    {'range': [50, 75], 'color': "#84cc16"}, # Ganância
                    {'range': [75, 100], 'color': "#10b981"}], # Ganância extrema
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': fng}}))
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
        <div style="text-align: center; color: #64748b;">
            <small>0-25: Medo Extremo | 25-50: Medo | 50-75: Ganância | 75-100: Ganância Extrema</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Não foi possível obter o índice no momento")

if __name__ == "__main__":
    main()
