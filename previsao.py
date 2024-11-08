import requests
import pandas as pd
import streamlit as st
import datetime
import time

# Função para obter os dados da previsão do tempo da API
def get_weather_data():
    # Defina a chave de API e o ID da cidade
    api_key = '680e436df2f7321be79cef2383e624a8'
    city_id = '3466537'  # Caxias do Sul
    base_url = 'http://api.openweathermap.org/data/2.5/forecast'

    # Crie a URL completa para a solicitação
    url = f"{base_url}?id={city_id}&appid={api_key}&units=metric&lang=pt_br"

    # Faça a solicitação para a API do OpenWeatherMap
    response = requests.get(url)

    # Verifique se a solicitação foi bem-sucedida
    if response.status_code == 200:
        weather_data = response.json()
        
        # Estruturar em um DataFrame
        forecast_list = weather_data['list']
        df = pd.json_normalize(forecast_list)
        
        # Ajustar as colunas para um formato mais amigável
        df.columns = df.columns.str.replace('main.', 'main_', regex=False)
        df.columns = df.columns.str.replace('wind.', 'wind_', regex=False)
        df.columns = df.columns.str.replace('clouds.', 'clouds_', regex=False)
        df.columns = df.columns.str.replace('sys.', 'sys_', regex=False)
        df.columns = df.columns.str.replace('weather.', 'weather_', regex=False)

        # Expandir a coluna 'weather'
        weather_expanded = df['weather'].apply(lambda x: x[0] if len(x) > 0 else {})

        # Criação de novas colunas a partir dos dicionários extraídos
        df['weather_id'] = weather_expanded.apply(lambda x: x.get('id', None))
        df['weather_main'] = weather_expanded.apply(lambda x: x.get('main', None))
        df['weather_description'] = weather_expanded.apply(lambda x: x.get('description', None))
        df['weather_icon'] = weather_expanded.apply(lambda x: x.get('icon', None))

        # Remover a coluna 'weather' original
        df.drop(columns=['weather'], inplace=True)

        # Converter dt_txt para datetime
        df['dt_txt'] = pd.to_datetime(df['dt_txt'])

        # Extrair apenas a data para agrupamento
        df['date'] = df['dt_txt'].dt.date

        # Agrupar por data e calcular os valores desejados
        daily_df_full = df.groupby('date').agg({
            'main_temp_min': 'min',
            'main_temp_max': 'max',
            'main_humidity': 'mean',
            'weather_description': lambda x: x.mode()[0] if not x.mode().empty else 'N/A'
        }).reset_index()

        # Arredondar a média da umidade para números inteiros
        daily_df_full['main_humidity'] = daily_df_full['main_humidity'].round().astype(int)

        # Renomear as colunas para melhor clareza
        daily_df_full.rename(columns={
            'main_temp_min': 'temp_min',
            'main_temp_max': 'temp_max',
            'main_humidity': 'humidity_avg',
            'weather_description': 'weather_main'
        }, inplace=True)

        # Garantindo que a coluna 'date' seja do tipo datetime
        daily_df_full['date'] = pd.to_datetime(daily_df_full['date'], errors='coerce')

        return daily_df_full
    else:
        st.error(f"Erro ao buscar os dados. Status: {response.status_code}")
        return pd.DataFrame()  # Retorna um DataFrame vazio se houver erro

# CSS para esconder o botão flutuante no mobile usando seletor mais específico
hide_streamlit_style = """
    <style>
    /* Esconde a barra de ferramentas no desktop */
    MainMenu {visibility: hidden;}
    
    /* Esconde o rodapé */
    footer {visibility: hidden;}
    
    /* Esconde o cabeçalho */
    header {visibility: hidden;}

    /* Esconde o botão flutuante no mobile com seletor CSS baseado no XPath */
    [data-testid="stSidebarNav"] {display: none;} /* Este deve funcionar para a versão mais recente do Streamlit */
    
    /* Seleção direta com base no XPath convertido */
    div[role="button"] > svg {display: none;} /* Seletor CSS para o botão flutuante do menu */
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# Função para mapear o clima para um ícone
def weather_icon(weather):
    icons = {
        'chuva leve': '🌧️',
        'algumas nuvens': '⛅',
        'céu limpo': '☀️',
        'nublado': '☁️',
        'chuva forte': '🌧️🌧️'
    }
    return icons.get(weather, '❓')

# Iniciando a interface do Streamlit
st.title('Tempo em Caxias do Sul')

try:
    # Botão de atualização
    if st.button("Atualizar previsão"):
        daily_df_full = fetch_weather_data()
    else:
        daily_df_full = fetch_weather_data()

    if daily_df_full is not None:
        st.subheader('Previsão para os próximos dias ↻')

        cols = st.columns(2)

        for i, (index, row) in enumerate(daily_df_full.iterrows()):
            icon = weather_icon(row['weather_main'])
            with cols[i % 2]:  # Alterna entre as duas colunas
                st.markdown(f"<h3>{row['date'].strftime('%Y-%m-%d')} {icon}</h3>", unsafe_allow_html=True)
                
                # Exibindo temperatura com barra visual
                temp_bar = f"""
                    <div style='display: flex; align-items: center;'>
                        <span style='width: 50px;'>{row['temp_min']}°C</span>
                        <div style='background: linear-gradient(to right, #00aaff, #ffaa00); 
                                    width: 100%; 
                                    height: 10px; 
                                    border-radius: 5px; 
                                    margin: 0 10px; 
                                    position: relative;'>
                            <div style='position: absolute; 
                                        left: {int((row['temp_min'] - row['temp_min']) / (row['temp_max'] - row['temp_min']) * 100)}%; 
                                        width: 2px; 
                                        height: 15px; 
                                        background: #005577;'></div>
                            <div style='position: absolute; 
                                        left: {int((row['temp_max'] - row['temp_min']) / (row['temp_max'] - row['temp_min']) * 100)}%; 
                                        width: 2px; 
                                        height: 15px; 
                                        background: #ff7700;'></div>
                        </div>
                        <span style='width: 50px;'>{row['temp_max']}°C</span>
                    </div>
                """
                st.markdown(temp_bar, unsafe_allow_html=True)

                st.markdown(f"**Umidade**: {row['humidity_avg']}%")
                st.markdown(f"**Condição**: {row['weather_main']}")
                st.write('---')
    else:
        st.write("Nenhuma previsão disponível no momento.")
except Exception as e:
    st.error(f"Ocorreu um erro: {e}")
