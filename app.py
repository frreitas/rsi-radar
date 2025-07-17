import streamlit as st
import pandas as pd
import requests
import ta.momentum as ta_momentum
import ta.trend as ta_trend
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Crypto Analyst Pro",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado para um Layout Profissional ---
st.markdown("""
<style>
/* Variáveis de Cores */
:root {
    --primary-color: #4f46e5; /* Indigo */
    --secondary-color: #06b6d4; /* Cyan */
    --text-dark: #1e293b; /* Dark Slate */
    --text-light: #f8fafc; /* Light Gray */
    --bg-light: #f1f5f9; /* Light Blue-Gray */
    --bg-card: #ffffff; /* White */
    --border-color: #e2e8f0; /* Light Grayish Blue */
    --success-color: #10b981; /* Emerald */
    --warning-color: #f59e0b; /* Amber */
    --danger-color: #ef4444; /* Red */
}

/* Layout Principal */
.main .block-container {
    max-width: 1200px;
    padding: 2rem 3rem;
}

/* Cabeçalhos */
h1 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-weight: 800;
    color: var(--text-dark);
    text-align: center;
    margin-bottom: 0.5rem;
    font-size: 2.5em;
}
h2 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: var(--primary-color);
    border-bottom: 2px solid var(--primary-color);
    padding-bottom: 0.5rem;
    margin-top: 2.5rem;
    font-size: 1.8em;
}
h3 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: var(--text-dark);
    font-weight: 600;
    font-size: 1.4em;
}
h4 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: var(--primary-color);
    font-weight: 600;
    font-size: 1.1em;
    margin-top: 1em;
    margin-bottom: 0.5em;
}

/* Cards e Contêineres */
.card {
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    background: var(--bg-card);
    transition: transform 0.2s, box-shadow 0.2s;
    border: 1px solid var(--border-color);
}
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
}

/* Seção de Seleção/Filtro */
.selection-section {
    background: var(--bg-light);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
}
.filter-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
}

/* Métricas */
.stMetric {
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    background: var(--bg-card);
    padding: 15px 20px;
    margin-bottom: 15px;
    border: 1px solid var(--border-color);
}

/* Card de Recomendação */
.recommendation-card {
    border-radius: 16px;
    padding: 15px 20px;
    font-weight: 700;
    font-size: 24px;
    max-width: 550px;
    margin: 20px auto;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    text-align: center;
    color: var(--text-light);
    background-image: linear-gradient(45deg, var(--primary-color), #6d28d9);
    border: none;
}
.recommendation-card .main-text {
    font-size: 1em;
    margin-bottom: 0.5em;
}
.recommendation-card .sub-text {
    font-size: 0.7em;
    font-weight: 400;
    opacity: 0.9;
    line-height: 1.3;
}
.rec-compra { background-color: var(--success-color); }
.rec-acumular { background-color: var(--warning-color); color: var(--text-dark); }
.rec-agardar { background-color: #fd7e14; }
.rec-venda { background-color: var(--danger-color); }
.rec-observar { background-color: #007bff; }
.rec-espera { background-color: #6c757d; }
.rec-vendaparcial { background-color: #6f42c1; }

/* Detalhes da Análise */
.analysis-details-section {
    background: var(--bg-card);
    padding: 20px 25px;
    border-radius: 12px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    margin-top: 15px;
    border: 1px solid var(--border-color);
}
.analysis-details-item {
    margin-bottom: 1.2em;
    line-height: 1.5;
}
.analysis-details-item h4 {
    margin-top: 0;
    margin-bottom: 0.3em;
    color: var(--primary-color);
    font-size: 1.1em;
}
.analysis-details-item p {
    margin: 0.2em 0;
    font-size: 0.95em;
    color: #475569;
}
.analysis-details-item strong {
    color: var(--text-dark);
}

/* Estilos para ícones e cores condicionais */
.positive-change { color: var(--success-color); font-weight: 600; }
.negative-change { color: var(--danger-color); font-weight: 600; }
.neutral-change { color: #64748b; }

.trend-up { color: var(--success-color); }
.trend-down { color: var(--danger-color); }
.trend-neutral { color: #64748b; }

.volume-up { color: var(--success-color); }
.volume-down { color: var(--danger-color); }
.volume-normal { color: #64748b; }

.rsi-overbought { color: var(--danger-color); }
.rsi-oversold { color: var(--success-color); }
.rsi-neutral { color: #64748b; }

.status-check { color: var(--success-color); }
.status-x { color: var(--danger-color); }
.status-info { color: #007bff; }

/* Estilo para sparklines */
.sparkline-img {
    height: 25px;
    vertical-align: middle;
    margin-left: 5px;
}

/* Estilo para barras de progresso */
.progress-bar-container {
    width: 100%;
    background-color: #e0e0e0;
    border-radius: 5px;
    overflow: hidden;
    margin-top: 5px;
}
.progress-bar {
    height: 10px;
    background-color: var(--primary-color);
    border-radius: 5px;
    text-align: center;
    color: white;
    font-size: 8px;
    line-height: 10px;
}
.progress-bar.rsi-oversold { background-color: var(--success-color); }
.progress-bar.rsi-overbought { background-color: var(--danger-color); }
.progress-bar.rsi-neutral { background-color: var(--warning-color); }

/* Botões */
.stButton>button {
    border-radius: 8px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease-in-out;
}
.stButton>button.primary {
    background-color: var(--primary-color) !important;
    color: var(--text-light) !important;
    border: none !important;
}
.stButton>button.primary:hover {
    background-color: #6d28d9 !important;
    transform: translateY(-1px);
}

/* Abas */
.stTabs [role="tablist"] {
    gap: 0.5rem !important;
}
.stTabs [role="tab"] {
    border-radius: 8px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 500 !important;
    background: var(--bg-light) !important;
    color: var(--text-dark) !important;
    transition: all 0.2s ease-in-out;
}
.stTabs [aria-selected="true"] {
    background: var(--primary-color) !important;
    color: var(--text-light) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.stTabs [role="tab"]:hover {
    background: #e2e8f0 !important;
}

/* Rodapé */
.footer {
    text-align: center;
    color: #64748b;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
}
.footer small {
    font-size: 0.85em;
}

/* Responsividade */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem;
    }
    h1 {
        font-size: 2em;
    }
    h2 {
        font-size: 1.5em;
    }
    .filter-grid {
        grid-template-columns: 1fr;
    }
    .recommendation-card {
        font-size: 20px;
        padding: 15px;
    }
    .recommendation-card .main-text {
        font-size: 1em;
    }
    .recommendation-card .sub-text {
        font-size: 0.6em;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
@st.cache_data(ttl=3600)
def get_top_100_cryptos():
    """Busca as 100 principais criptomoedas"""
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=100&tsym=USD"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["Data"]
        return sorted([f"{c['CoinInfo']['FullName']} ({c['CoinInfo']['Name']})" for c in data])
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
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.rename(columns={'volumeto': 'volume'}).dropna()
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados de {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_market_cap_data(symbols):
    """Busca dados de market cap para os símbolos fornecidos."""
    url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={','.join(symbols)}&tsyms=USD"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["RAW"]
        market_caps = {s: data[s]['USD']['MKTCAP'] for s in symbols if s in data and 'USD' in data[s]}
        return market_caps
    except Exception as e:
        st.warning(f"Erro ao buscar dados de market cap: {e}")
        return {}

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
    if any(ema is None for ema in [ema_fast, ema_medium, ema_slow, ema_long]):
        return "Dados insuficientes"
    
    if ema_fast > ema_medium > ema_slow > ema_long:
        return "Alta consolidada"
    elif ema_fast < ema_medium < ema_slow < ema_long:
        return "Baixa consolidada"
    return "Neutra/Transição"

def classificar_volume(v_atual, v_medio):
    """Compara volume atual com médio"""
    if v_medio == 0:
        return "Indefinido"
    if v_atual >= v_medio * 1.2:
        return "Subindo (Alto)"
    elif v_atual <= v_medio * 0.8:
        return "Caindo (Baixo)"
    else:
        return "Normal"

def obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal):
    """Gera recomendação com base nos indicadores"""
    rec_principal = "Aguardar"
    rec_detalhe = "Condições atuais não indicam um ponto claro de entrada ou saída. Observe o mercado."

    if tendencia == "Alta consolidada":
        if rsi_class == "Sobrevendido" and "Subindo" in volume_class and macd_signal == "Compra":
            rec_principal = "Compra Forte"
            rec_detalhe = "Forte tendência de alta, ativo sobrevendido com volume crescente e sinal de compra MACD. Excelente oportunidade."
        elif rsi_class == "Neutro" and "Subindo" in volume_class and macd_signal == "Compra":
            rec_principal = "Compra"
            rec_detalhe = "Tendência de alta confirmada, RSI neutro e sinal de compra MACD. Bom ponto de entrada."
        elif rsi_class == "Sobrecomprado":
            rec_principal = "Aguardar correção"
            rec_detalhe = "Ativo sobrecomprado em tendência de alta. Risco de correção iminente. Aguarde um recuo para nova entrada."
    elif tendencia == "Baixa consolidada":
        if rsi_class == "Sobrevendido" and macd_signal == "Compra":
            rec_principal = "Observar reversão"
            rec_detalhe = "Ativo sobrevendido em tendência de baixa, com possível sinal de reversão. Monitore de perto para confirmação."
        elif "Caindo" in volume_class or macd_signal == "Venda":
            rec_principal = "Venda / Evitar"
            rec_detalhe = "Tendência de baixa confirmada, volume em queda ou sinal de venda MACD. Evite posições ou considere vender."
            
    if rec_principal == "Aguardar":
        if tendencia == "Neutra/Transição":
            rec_detalhe = "O ativo está em fase de consolidação ou transição de tendência. Aguarde uma definição clara."
        elif rsi_class == "Neutro" and "Normal" in volume_class and macd_signal == "Venda":
            rec_detalhe = "RSI neutro, volume normal e sinal de venda MACD. Não há clareza para compra, aguarde."
        elif rsi_class == "Neutro" and "Normal" in volume_class and macd_signal == "Compra":
            rec_detalhe = "RSI neutro, volume normal e sinal de compra MACD. Aguarde mais confirmações para uma entrada segura."

    return rec_principal, rec_detalhe

def style_recomendacao_card(text, detail_text):
    """Estiliza o card de recomendação"""
    styles = {
        "Compra Forte": ("Compra Forte", "rec-compra"),
        "Compra": ("Compra", "rec-compra"),
        "Aguardar correção": ("Aguardar correção", "rec-agardar"),
        "Venda / Evitar": ("Venda / Evitar", "rec-venda"),
        "Observar reversão": ("Observar reversão", "rec-observar"),
        "Aguardar": ("Aguardar", "rec-espera"),
    }
    main_text, class_name = styles.get(text, (text, "rec-espera"))
    return main_text, detail_text, class_name

def generate_sparkline(data):
    """Gera uma imagem base64 da sparkline"""
    if len(data) < 2:
        return ""
    fig, ax = plt.subplots(1, 1, figsize=(2, 0.2))
    ax.plot(data, color='blue', linewidth=0.8)
    ax.set_axis_off()
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- Seção de Filtragem ---
def mostrar_filtros():
    """Exibe os controles de filtragem"""
    with st.expander("🔍 FILTRAR MOEDAS POR INDICADORES", expanded=False):
        with st.container(border=True):
            st.markdown('<div class="filter-grid">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                timeframe_filter = st.selectbox("Timeframe", ["1h", "4h", "1d", "1w"], index=2, key="filter_timeframe_main")
                trend_filter = st.multiselect("Tendência", ["Alta consolidada", "Baixa consolidada", "Neutra/Transição"], key="filter_trend_main")
                
            with col2:
                rsi_filter = st.multiselect("RSI", ["Sobrevendido", "Neutro", "Sobrecomprado"], key="filter_rsi_main")
                volume_filter = st.multiselect("Volume", ["Subindo (Alto)", "Normal", "Caindo (Baixo)"], key="filter_volume_main")
            
            with col3:
                recommendation_filter = st.multiselect(
                    "Recomendação", 
                    ["Compra Forte", "Compra", "Aguardar correção", "Venda / Evitar", "Observar reversão", "Aguardar"], 
                    key="filter_recommendation_main"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🔎 APLICAR FILTROS", type="primary", use_container_width=True, key="apply_filters_button"):
            return {
                'timeframe': timeframe_filter,
                'trend': trend_filter,
                'rsi': rsi_filter,
                'volume': volume_filter,
                'recommendation': recommendation_filter,
            }
    return None

def filtrar_moedas(filters):
    """Filtra as moedas com base nos critérios"""
    st.subheader("Resultados da Filtragem")
    with st.spinner(f"Processando {len(get_top_100_cryptos())} moedas..."):
        resultados = []
        progress_bar = st.progress(0)
        
        for i, moeda in enumerate(get_top_100_cryptos()):
            simbolo = extrair_simbolo(moeda)
            endpoint, limit = get_timeframe_endpoint(filters['timeframe'])
            df = get_crypto_data(simbolo, endpoint, limit)
            
            if df.empty or len(df) < 50:
                progress_bar.progress((i + 1) / len(get_top_100_cryptos()))
                continue
                
            if filters['timeframe'] == "4h":
                df = agrupar_4h_otimizado(df)
                if df.empty or len(df) < 50:
                    progress_bar.progress((i + 1) / len(get_top_100_cryptos()))
                    continue
                
            # Calcular indicadores
            preco = df['close'].iloc[-1]
            variacao = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100 if len(df) > 1 else 0
            volume_atual = df['volume'].iloc[-1]
            volume_medio = df['volume'].mean()
            rsi = ta_momentum.RSIIndicator(df['close'], 14).rsi().iloc[-1]
            rsi_class = classificar_rsi(rsi)
            
            macd = ta_trend.MACD(df['close'])
            macd_line = macd.macd().iloc[-1]
            macd_signal_line = macd.macd_signal().iloc[-1]
            macd_signal = "Compra" if macd_line > macd_signal_line else "Venda"
            
            # EMAs para tendência
            ema_fast = ta_trend.EMAIndicator(df['close'], 8).ema_indicator().iloc[-1] if len(df) >= 8 else None
            ema_medium = ta_trend.EMAIndicator(df['close'], 21).ema_indicator().iloc[-1] if len(df) >= 21 else None
            ema_slow = ta_trend.EMAIndicator(df['close'], 50).ema_indicator().iloc[-1] if len(df) >= 50 else None
            ema_long = ta_trend.EMAIndicator(df['close'], 200).ema_indicator().iloc[-1] if len(df) >= 200 else None
            
            tendencia = classificar_tendencia(ema_fast, ema_medium, ema_slow, ema_long)
            volume_class = classificar_volume(volume_atual, volume_medio)

            # Gerar recomendação e sparkline
            rec_principal, _ = obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal)
            sparkline_html = ""
            if filters['timeframe'] == "1d" and len(df) >= 7:
                sparkline_data = df['close'].tail(7).tolist()
                sparkline_base64 = generate_sparkline(sparkline_data)
                sparkline_html = f'<img src="data:image/png;base64,{sparkline_base64}" class="sparkline-img">'
            
            # Aplicar filtros
            conditions_met = True
            if filters['trend'] and tendencia not in filters['trend']:
                conditions_met = False
            if filters['rsi'] and rsi_class not in filters['rsi']:
                conditions_met = False
            if filters['volume'] and volume_class not in filters['volume']:
                conditions_met = False
            if filters['recommendation'] and rec_principal not in filters['recommendation']:
                conditions_met = False
            
            if conditions_met:
                resultados.append({
                    'Moeda': moeda,
                    'Símbolo': simbolo,
                    'Preço': preco,
                    'Variação': variacao,
                    'RSI': rsi,
                    'RSI_Class': rsi_class,
                    'Tendência': tendencia,
                    'Volume': volume_class,
                    'Recomendação': rec_principal,
                    'Sparkline': sparkline_html,
                    'Data': df
                })
            
            progress_bar.progress((i + 1) / len(get_top_100_cryptos()))
        
        progress_bar.empty()
        return resultados

# --- Interface Principal ---
def main():
    st.title("📊 Análise Técnica de Criptomoedas")
    st.markdown("""
    <p style='text-align: center; color: #64748b; margin-bottom: 2rem;'>
    Ferramenta completa para análise e filtragem de criptoativos
    </p>
    """, unsafe_allow_html=True)
    
    # Seção de dados do mercado no topo da página
    col1, col2 = st.columns(2)
    
    with col1:
        # Índice de Medo e Ganância
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
                        {'range': [0, 25], 'color': "#ef4444"},
                        {'range': [25, 50], 'color': "#f59e0b"},
                        {'range': [50, 75], 'color': "#84cc16"},
                        {'range': [75, 100], 'color': "#10b981"}],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': fng}}))
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("""
            <div style='text-align: center; color: #64748b; font-size: 0.9em;'>
                0-25: Medo Extremo | 25-50: Medo | 50-75: Ganância | 75-100: Ganância Extrema
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Não foi possível obter o índice no momento")

    with col2:
        # Dominância de Mercado
        st.subheader("🌍 Dominância de Mercado")
        market_caps = get_market_cap_data(["BTC", "ETH"])
        if market_caps:
            total_market_cap = sum(market_caps.values())
            if total_market_cap > 0:
                btc_dominance = (market_caps.get("BTC", 0) / total_market_cap) * 100
                eth_dominance = (market_caps.get("ETH", 0) / total_market_cap) * 100
                other_dominance = 100 - btc_dominance - eth_dominance
                
                dominance_df = pd.DataFrame({
                    'Cripto': ['Bitcoin', 'Ethereum', 'Outras'],
                    'Dominância (%)': [btc_dominance, eth_dominance, other_dominance]
                })
                
                fig_dominance = go.Figure(data=[go.Pie(
                    labels=dominance_df['Cripto'], 
                    values=dominance_df['Dominância (%)'],
                    hole=.3,
                    textinfo='label+percent',
                    marker=dict(colors=['#FF9500', '#627EEA', '#888'])
                )])
                fig_dominance.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=30, b=20),
                    showlegend=False
                )
                st.plotly_chart(fig_dominance, use_container_width=True)
                
                st.markdown(f"""
                <div style='text-align: center; color: #64748b; font-size: 0.9em;'>
                    BTC: {btc_dominance:.1f}% | ETH: {eth_dominance:.1f}% | Outras: {other_dominance:.1f}%
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Dados de Market Cap indisponíveis para cálculo de dominância.")
        else:
            st.info("Não foi possível obter dados de Market Cap para dominância.")

    st.divider()

    # Seção de Filtragem
    filtros = mostrar_filtros()
    
    if filtros:
        resultados_filtro = filtrar_moedas(filtros)
        if resultados_filtro:
            st.success(f"✅ {len(resultados_filtro)} moedas atendem aos critérios")
            
            # Exibir resultados em uma tabela
            df_resultados = pd.DataFrame([{
                'Moeda': r['Moeda'],
                'Preço': f"${r['Preço']:.8f}" if r['Preço'] < 1 else f"${r['Preço']:,.2f}",
                'Variação': f'<span class="{"positive-change" if r["Variação"] >= 0 else "negative-change"}">{r["Variação"]:+.2f}%</span> {r["Sparkline"]}',
                'RSI': f'<span class="rsi-{r["RSI_Class"].lower()}">{r["RSI"]:.1f} ({r["RSI_Class"]})</span>',
                'Tendência': f'<span class="trend-{r["Tendência"].split("/")[0].lower().replace(" ", "")}">{r["Tendência"]} {"⬆️" if "Alta" in r["Tendência"] else ("⬇️" if "Baixa" in r["Tendência"] else "↔️")}</span>',
                'Volume': f'<span class="volume-{r["Volume"].split(" ")[0].lower()}">{r["Volume"]} {"⬆️" if "Subindo" in r["Volume"] else ("⬇️" if "Caindo" in r["Volume"] else "↔️")}</span>',
                'Recomendação': r['Recomendação']
            } for r in resultados_filtro])
            
            st.markdown(df_resultados.to_html(escape=False), unsafe_allow_html=True)
            st.divider()
        else:
            st.warning("Nenhuma moeda atende aos critérios selecionados")
            st.divider()

    # Seção de Análise Individual
    st.subheader("📈 Análise Individual")
    
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            moeda_selecionada = st.selectbox(
                "Selecione a Moeda",
                get_top_100_cryptos(),
                key="main_coin_select",
                help="Escolha uma criptomoeda para análise detalhada"
            )
            simbolo = extrair_simbolo(moeda_selecionada)
        
        with col2:
            timeframe_analise = st.selectbox(
                "Timeframe Análise",
                ["1h", "4h", "1d", "1w"],
                index=2,
                key="main_timeframe",
                help="Selecione o período de tempo para o gráfico e indicadores."
            )
    
    with st.spinner(f"Carregando dados de {moeda_selecionada}..."):
        endpoint_analise, limit_analise = get_timeframe_endpoint(timeframe_analise)
        df_analise_raw = get_crypto_data(simbolo, endpoint_analise, limit_analise)
        
        if df_analise_raw.empty:
            st.error("Dados insuficientes para análise")
            st.stop()
            
        if timeframe_analise == "4h":
            df_analise = agrupar_4h_otimizado(df_analise_raw)
            if df_analise.empty:
                st.error("Dados insuficientes após agrupamento para 4h.")
                st.stop()
        else:
            df_analise = df_analise_raw.copy()
            
        # Cálculo de indicadores
        preco_atual = df_analise["close"].iloc[-1]
        variacao = ((df_analise["close"].iloc[-1] - df_analise["close"].iloc[-2]) / df_analise["close"].iloc[-2] * 100) if len(df_analise) > 1 else 0
        volume_atual = df_analise["volume"].iloc[-1]
        volume_medio = df_analise["volume"].mean()
        rsi = ta_momentum.RSIIndicator(df_analise["close"], 14).rsi().iloc[-1]
        rsi_class = classificar_rsi(rsi)
        
        macd = ta_trend.MACD(df_analise["close"])
        macd_line = macd.macd().iloc[-1]
        macd_signal_line = macd.macd_signal().iloc[-1]
        macd_diff = macd.macd_diff().iloc[-1]
        macd_signal = "Compra" if macd_line > macd_signal_line else "Venda"
        
        # Cálculo EMAs
        ema_periods = [8, 21, 50, 200]
        emas = {}
        for period in ema_periods:
            if len(df_analise) >= period:
                emas[f"ema_{period}"] = ta_trend.EMAIndicator(df_analise["close"], period).ema_indicator().iloc[-1]
            else:
                emas[f"ema_{period}"] = None
        
        tendencia = classificar_tendencia(emas.get("ema_8"), emas.get("ema_21"), emas.get("ema_50"), emas.get("ema_200"))
        volume_class = classificar_volume(volume_atual, volume_medio)
        
        # Obter recomendação
        rec_principal, rec_detalhe = obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal)
        texto_card, texto_detalhe_card, classe_card = style_recomendacao_card(rec_principal, rec_detalhe)

    # Exibição dos resultados principais
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Preço Atual", f"${preco_atual:.8f}" if preco_atual < 1 else f"${preco_atual:,.2f}", f"{variacao:+.2f}%")
    col2.metric("📊 Volume 24h", f"${volume_atual:,.0f}", 
               f"{'↑' if 'Subindo' in volume_class else '↓'} {abs((volume_atual/volume_medio-1)*100):.1f}% vs média" 
               if volume_medio > 0 else "")
    col3.metric("📉 RSI (14)", f"{rsi:.1f}", rsi_class)

    # Análise detalhada
    with st.expander("🔍 Detalhes da Análise", expanded=True):
        with st.container(border=True):
            st.markdown(f"""
            <div class="analysis-details-item">
                <h4>Tendência {"⬆️" if "Alta" in tendencia else ("⬇️" if "Baixa" in tendencia else "↔️")}</h4>
                <p><strong>{tendencia}</strong></p>
                <p>EMA (8): <strong>${emas.get('ema_8', 0.0):,.2f}</strong> | EMA (21): <strong>${emas.get('ema_21', 0.0):,.2f}</strong></p>
                <p>EMA (50): <strong>${emas.get('ema_50', 0.0):,.2f}</strong> | EMA (200): <strong>${emas.get('ema_200', 0.0):,.2f}</strong></p>
                <p>Status: <span class="status-{"check" if tendencia == "Alta consolidada" else ("x" if tendencia == "Baixa consolidada" else "info")}">
                {"✅ Forte Alta" if tendencia == "Alta consolidada" else ("❌ Forte Baixa" if tendencia == "Baixa consolidada" else "ℹ️ Neutra/Transição")}
                </span></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="analysis-details-item">
                <h4>Momentum</h4>
                <p>RSI: <strong>{rsi:.1f}</strong> ({rsi_class})</p>
                <div class="progress-bar-container">
                    <div class="progress-bar rsi-{rsi_class.lower()}" style="width: {rsi}%;"></div>
                </div>
                <p>MACD: <strong>{macd_line:,.2f}</strong> | Sinal: <strong>{macd_signal_line:,.2f}</strong></p>
                <p>Histograma: <strong>{macd_diff:,.2f}</strong> | Sinal: <strong>{macd_signal}</strong></p>
                <p>Status: <span class="status-{"check" if macd_signal == "Compra" else ("x" if macd_signal == "Venda" else "info")}">
                {"✅ Sinal de Compra" if macd_signal == "Compra" else ("❌ Sinal de Venda" if macd_signal == "Venda" else "ℹ️ Sinal Neutro")}
                </span></p>
            </div>
            """, unsafe_allow_html=True)
            
            volume_progress = min(100, max(0, (volume_atual / volume_medio) * 100)) if volume_medio > 0 else 0
            st.markdown(f"""
            <div class="analysis-details-item">
                <h4>Volume {"⬆️" if "Subindo" in volume_class else ("⬇️" if "Caindo" in volume_class else "↔️")}</h4>
                <p>Atual: <strong>${volume_atual:,.0f}</strong></p>
                <p>Média: <strong>${volume_medio:,.0f}</strong></p>
                <p>Tendência: <strong>{volume_class}</strong></p>
                <div class="progress-bar-container">
                    <div class="progress-bar volume-{volume_class.split(" ")[0].lower()}" style="width: {volume_progress}%;"></div>
                </div>
                <p>Status: <span class="status-{"check" if "Subindo" in volume_class else ("x" if "Caindo" in volume_class else "info")}">
                {"✅ Volume Alto" if "Subindo" in volume_class else ("❌ Volume Baixo" if "Caindo" in volume_class else "ℹ️ Volume Normal")}
                </span></p>
            </div>
            """, unsafe_allow_html=True)

    # Card de recomendação
    st.markdown(f"""
    <div class="recommendation-card {classe_card}">
        <div class="main-text">{texto_card}</div>
        <div class="sub-text">{texto_detalhe_card}</div>
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
            increasing_line_color=st.get_option("theme.primaryColor") if st.get_option("theme.primaryColor") else '#10b981',
            decreasing_line_color='#ef4444'
        ))
        
        for period, color in zip([8, 21, 50, 200], ['orange', 'purple', 'blue', 'red']):
            if emas.get(f"ema_{period}") is not None:
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
            hovermode="x unified",
            template="plotly_white"
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
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Rodapé
    st.markdown("""
    <div class="footer">
        <small>Crypto Analyst Pro v1.0 - Ferramenta de análise técnica para criptomoedas</small><br>
        <small>© 2023 - Dados fornecidos por CryptoCompare API</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
