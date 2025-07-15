<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise Técnica de Criptomoedas</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #1a2980, #26d0ce);
            color: white;
            padding: 30px 0;
            text-align: center;
            border-radius: 0 0 15px 15px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        h1 {
            margin: 0;
            font-size: 2.2rem;
        }
        
        .control-panel {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .control-row {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 15px;
        }
        
        .control-group {
            flex: 1;
            min-width: 200px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        
        select, input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
        }
        
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            transition: background-color 0.3s;
            margin-right: 10px;
        }
        
        button:hover {
            background-color: #45a049;
        }
        
        button.secondary {
            background-color: #2196F3;
        }
        
        button.secondary:hover {
            background-color: #0b7dda;
        }
        
        .results {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .chart-container {
            flex: 2;
            min-width: 400px;
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .info-container {
            flex: 1;
            min-width: 300px;
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .indicator-box {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        
        .indicator-title {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .indicator-value {
            font-size: 1.2rem;
        }
        
        .rsi-overbought {
            color: #FF5722;
        }
        
        .rsi-oversold {
            color: #4CAF50;
        }
        
        .rsi-neutral {
            color: #2196F3;
        }
        
        .table-container {
            margin-top: 20px;
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: 600;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        @media (max-width: 768px) {
            .control-row {
                flex-direction: column;
            }
            
            .chart-container, .info-container {
                min-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Análise Técnica de Criptomoedas</h1>
            <p>Visualização de EMAs semanais e análise do RSI</p>
        </header>
        
        <div class="control-panel">
            <div class="control-row">
                <div class="control-group">
                    <label for="coin-select">Moeda:</label>
                    <select id="coin-select">
                        <option value="BTC">Bitcoin (BTC)</option>
                        <option value="ETH">Ethereum (ETH)</option>
                        <option value="SOL">Solana (SOL)</option>
                        <option value="BNB">BNB (BNB)</option>
                        <option value="ADA">Cardano (ADA)</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label for="timeframe-select">Timeframe do RSI:</label>
                    <select id="timeframe-select">
                        <option value="1h">1 Hora</option>
                        <option value="4h">4 Horas</option>
                        <option value="1d">1 Dia</option>
                        <option value="1w">1 Semana</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label for="period-select">Período de Análise:</label>
                    <select id="period-select">
                        <option value="1m">1 Mês</option>
                        <option value="3m" selected>3 Meses</option>
                        <option value="6m">6 Meses</option>
                        <option value="1y">1 Ano</option>
                    </select>
                </div>
            </div>
            
            <div class="control-row">
                <button onclick="updateCharts()" class="secondary">Atualizar Gráficos</button>
                <button onclick="exportData()">Exportar Dados</button>
            </div>
        </div>
        
        <div class="results">
            <div class="chart-container">
                <h2>Gráfico de Preço e EMAs</h2>
                <div id="price-chart" style="height: 400px;"></div>
            </div>
            
            <div class="info-container">
                <h2>Indicadores Atuais</h2>
                
                <div class="indicator-box">
                    <div class="indicator-title">RSI (14 períodos)</div>
                    <div class="indicator-value" id="rsi-value">-</div>
                    <div id="rsi-classification">Carregando...</div>
                </div>
                
                <div class="indicator-box">
                    <div class="indicator-title">EMA 8 Semanas</div>
                    <div class="indicator-value" id="ema8-value">-</div>
                </div>
                
                <div class="indicator-box">
                    <div class="indicator-title">EMA 21 Semanas</div>
                    <div class="indicator-value" id="ema21-value">-</div>
                </div>
                
                <div class="indicator-box">
                    <div class="indicator-title">EMA 56 Semanas</div>
                    <div class="indicator-value" id="ema56-value">-</div>
                </div>
                
                <div class="indicator-box">
                    <div class="indicator-title">EMA 200 Semanas</div>
                    <div class="indicator-value" id="ema200-value">-</div>
                </div>
            </div>
        </div>
        
        <div class="chart-container" style="margin-top: 20px;">
            <h2>Gráfico do RSI</h2>
            <div id="rsi-chart" style="height: 300px;"></div>
        </div>
        
        <div class="info-container" style="margin-top: 20px;">
            <h2>Recomendação</h2>
            <div id="recommendation-text" style="padding: 15px; background-color: #f0f8ff; border-radius: 5px;">
                Aguardando análise...
            </div>
        </div>
        
        <div class="table-container">
            <h2>Dados Históricos</h2>
            <div style="overflow-x: auto;">
                <table id="history-table">
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Preço</th>
                            <th>EMA 8</th>
                            <th>EMA 21</th>
                            <th>EMA 56</th>
                            <th>EMA 200</th>
                            <th>RSI</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Dados serão preenchidos dinamicamente -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Dados de exemplo (em uma aplicação real, você buscaria esses dados de uma API)
        const sampleData = {
            dates: ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01', 
                   '2023-06-01', '2023-07-01', '2023-08-01', '2023-09-01', '2023-10-01'],
            prices: [28000, 32000, 37000, 40000, 38000, 35000, 33000, 31000, 29000, 30000],
            ema8: [27500, 30500, 34500, 38000, 37500, 35500, 33500, 31500, 29500, 29500],
            ema21: [27000, 29000, 33000, 36000, 37000, 36000, 34000, 32500, 30000, 30500],
            ema56: [26000, 28000, 31000, 34000, 35000, 34500, 33500, 33000, 31500, 31000],
            ema200: [25000, 25500, 26500, 28000, 30000, 31000, 31500, 32000, 32000, 31500],
            rsi: [65, 70, 75, 80, 60, 45, 40, 35, 30, 40],
            latest: {
                price: 30000,
                ema8: 29500,
                ema21: 30500,
                ema56: 31000,
                ema200: 31500,
                rsi: 40
            }
        };

        // Inicializar gráficos
        function initCharts() {
            createPriceChart();
            createRsiChart();
            updateIndicatorValues();
            updateRecommendation();
            populateHistoryTable();
        }
        
        // Criar gráfico de preço e EMAs
        function createPriceChart() {
            const trace1 = {
                x: sampleData.dates,
                y: sampleData.prices,
                name: 'Preço',
                line: {color: '#1f77b4', width: 2}
            };
            
            const trace2 = {
                x: sampleData.dates,
                y: sampleData.ema8,
                name: 'EMA 8',
                line: {color: '#ff7f0e', width: 1.5}
            };
            
            const trace3 = {
                x: sampleData.dates,
                y: sampleData.ema21,
                name: 'EMA 21',
                line: {color: '#2ca02c', width: 1.5}
            };
            
            const trace4 = {
                x: sampleData.dates,
                y: sampleData.ema56,
                name: 'EMA 56',
                line: {color: '#d62728', width: 1.5}
            };
            
            const trace5 = {
                x: sampleData.dates,
                y: sampleData.ema200,
                name: 'EMA 200',
                line: {color: '#9467bd', width: 1.5}
            };
            
            const layout = {
                title: 'Preço e Médias Móveis Exponenciais',
                xaxis: {
                    title: 'Data',
                    gridcolor: '#f0f0f0'
                },
                yaxis: {
                    title: 'Preço (USD)',
                    gridcolor: '#f0f0f0'
                },
                plot_bgcolor: 'rgba(255, 255, 255, 1)',
                paper_bgcolor: 'rgba(255, 255, 255, 1)',
                showlegend: true,
                hovermode: 'closest'
            };
            
            Plotly.newPlot('price-chart', [trace1, trace2, trace3, trace4, trace5], layout);
        }
        
        // Criar gráfico de RSI
        function createRsiChart() {
            const trace = {
                x: sampleData.dates,
                y: sampleData.rsi,
                name: 'RSI',
                line: {color: '#17becf', width: 2}
            };
            
            // Linhas de sobrecompra e sobrevenda
            const overboughtLine = {
                type: 'line',
                x0: sampleData.dates[0],
                y0: 70,
                x1: sampleData.dates[sampleData.dates.length-1],
                y1: 70,
                line: {
                    color: 'red',
                    width: 1,
                    dash: 'dot'
                }
            };
            
            const oversoldLine = {
                type: 'line',
                x0: sampleData.dates[0],
                y0: 30,
                x1: sampleData.dates[sampleData.dates.length-1],
                y1: 30,
                line: {
                    color: 'green',
                    width: 1,
                    dash: 'dot'
                }
            };
            
            const layout = {
                title: 'Índice de Força Relativa (RSI)',
                xaxis: {
                    title: 'Data',
                    gridcolor: '#f0f0f0'
                },
                yaxis: {
                    title: 'RSI',
                    gridcolor: '#f0f0f0',
                    range: [0, 100]
                },
                shapes: [overboughtLine, oversoldLine],
                plot_bgcolor: 'rgba(255, 255, 255, 1)',
                paper_bgcolor: 'rgba(255, 255, 255, 1)',
                showlegend: true,
                hovermode: 'closest'
            };
            
            Plotly.newPlot('rsi-chart', [trace], layout);
        }
        
        // Atualizar valores dos indicadores
        function updateIndicatorValues() {
            document.getElementById('rsi-value').textContent = sampleData.latest.rsi.toFixed(2);
            
            // Classificação do RSI
            const rsiElem = document.getElementById('rsi-classification');
            rsiElem.className = '';
            
            if (sampleData.latest.rsi < 30) {
                rsiElem.textContent = 'Sobrevendida';
                rsiElem.className = 'rsi-oversold';
            } else if (sampleData.latest.rsi > 70) {
                rsiElem.textContent = 'Sobrecomprada';
                rsiElem.className = 'rsi-overbought';
            } else {
                rsiElem.textContent = 'Neutra';
                rsiElem.className = 'rsi-neutral';
            }
            
            document.getElementById('ema8-value').textContent = '$' + sampleData.latest.ema8.toLocaleString();
            document.getElementById('ema21-value').textContent = '$' + sampleData.latest.ema21.toLocaleString();
            document.getElementById('ema56-value').textContent = '$' + sampleData.latest.ema56.toLocaleString();
            document.getElementById('ema200-value').textContent = '$' + sampleData.latest.ema200.toLocaleString();
        }
        
        // Atualizar recomendação
        function updateRecommendation() {
            const recommendationElem = document.getElementById('recommendation-text');
            const price = sampleData.latest.price;
            const rsi = sampleData.latest.rsi;
            
            let recommendation = '';
            
            if (price > sampleData.latest.ema200 && rsi < 30) {
                recommendation = '💡 Forte sinal de compra: Preço acima da EMA 200 e RSI sobrevendido.';
            } else if (price > sampleData.latest.ema200 && rsi < 50) {
                recommendation = '📈 Potencial de compra: Tendência de alta com preço acima da EMA 200 e RSI neutro.';
            } else if (price < sampleData.latest.ema200 && rsi < 30) {
                recommendation = '⚠️ Cautela: Tendência de baixa mas RSI sobrevendido. Podem haver oportunidades de curto prazo.';
            } else if (price > sampleData.latest.ema200 && rsi > 70) {
                recommendation = '💰 Tomar lucro: Tendência de alta mas RSI sobrecomprado. Considere realizar lucros parciais.';
            } else if (price < sampleData.latest.ema200 && rsi > 70) {
                recommendation = '🔻 Sinal de venda: Tendência de baixa e RSI sobrecomprado.';
            } else {
                recommendation = '🔄 Neutral: Aguarde por sinais mais claros.';
            }
            
            recommendationElem.innerHTML = `
                <p><strong>Análise:</strong></p>
                <p>${recommendation}</p>
                <p><small>Baseado na relação entre preço, EMAs semanais e RSI do timeframe selecionado.</small></p>
            `;
        }
        
        // Preencher tabela de histórico
        function populateHistoryTable() {
            const tableBody = document.querySelector('#history-table tbody');
            tableBody.innerHTML = '';
            
            for (let i = 0; i < sampleData.dates.length; i++) {
                const row = document.createElement('tr');
                
                row.innerHTML = `
                    <td>${sampleData.dates[i]}</td>
                    <td>$${sampleData.prices[i].toLocaleString()}</td>
                    <td>$${sampleData.ema8[i].toLocaleString()}</td>
                    <td>$${sampleData.ema21[i].toLocaleString()}</td>
                    <td>$${sampleData.ema56[i].toLocaleString()}</td>
                    <td>$${sampleData.ema200[i].toLocaleString()}</td>
                    <td>${sampleData.rsi[i].toFixed(2)}</td>
                `;
                
                tableBody.appendChild(row);
            }
        }
        
        // Atualizar gráficos (simulado - em uma aplicação real buscaria novos dados)
        function updateCharts() {
            const coin = document.getElementById('coin-select').value;
            const timeframe = document.getElementById('timeframe-select').value;
            const period = document.getElementById('period-select').value;
            
            // Simular carregamento de novos dados
            document.getElementById('rsi-value').textContent = 'Carregando...';
            
            // Aqui você faria uma chamada à API para buscar novos dados
            // Para este exemplo, vamos apenas atualizar com os mesmos dados após um delay
            setTimeout(() => {
                // Atualiza os valores (em um caso real, aqui atualizaria com os novos dados)
                updateIndicatorValues();
                updateRecommendation();
                
                // Alertar usuário que os dados foram atualizados
                alert(`Dados atualizados para ${coin} no timeframe de ${timeframe}`);
            }, 1000);
        }
        
        // Exportar dados
        function exportData() {
            // Criar CSV a partir da tabela
            let csv = 'Data,Preço,EMA 8,EMA 21,EMA 56,EMA 200,RSI\n';
            
            for (let i = 0; i < sampleData.dates.length; i++) {
                csv += `${sampleData.dates[i]},${sampleData.prices[i]},${sampleData.ema8[i]},${sampleData.ema21[i]},${sampleData.ema56[i]},${sampleData.ema200[i]},${sampleData.rsi[i].toFixed(2)}\n`;
            }
            
            // Criar link de download
            const blob = new Blob([csv], {type: 'text/csv'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.setAttribute('hidden', '');
            a.setAttribute('href', url);
            a.setAttribute('download', 'analise_cripto.csv');
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            alert('Dados exportados com sucesso!');
        }
        
        // Inicializar a aplicação quando a página carregar
        window.onload = initCharts;
    </script>
</body>
</html>
