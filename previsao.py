import requests
import pandas as pd
import streamlit as st
import datetime

# Defina a chave de API e o ID da cidade
api_key = '680e436df2f7321be79cef2383e624a8'
city_id = '3466537'  # ID de Caxias do Sul
base_url = 'http://api.openweathermap.org/data/2.5/forecast'

# Função para buscar os dados da previsão do tempo
def fetch_weather_data():
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
        
        # Expande a coluna 'weather'
        weather_expanded = df['weather'].apply(lambda x: x[0] if len(x) > 0 else {})
        df['weather_id'] = weather_expanded.apply(lambda x: x.get('id', None))
        df['weather_main'] = weather_expanded.apply(lambda x: x.get('main', None))
        df['weather_description'] = weather_expanded.apply(lambda x: x.get('description', None))
        df['weather_icon'] = weather_expanded.apply(lambda x: x.get('icon', None))
        df.drop(columns=['weather'], inplace=True)
        
        # Converter dt_txt para datetime
        df['dt_txt'] = pd.to_datetime(df['dt_txt'])
        df['date'] = df['dt_txt'].dt.date
        
        # Agrupar por data e calcular os valores desejados incluindo a coluna weather_main
        daily_df = df.groupby('date').agg({
            'main_temp_min': 'min',
            'main_temp_max': 'max',
            'main_humidity': 'mean',
            'weather_description': lambda x: x.mode()[0] if not x.mode().empty else 'N/A'
        }).reset_index()
        
        # Ajustar os valores
        daily_df['main_humidity'] = daily_df['main_humidity'].round().astype(int)
        daily_df.rename(columns={
            'main_temp_min': 'temp_min',
            'main_temp_max': 'temp_max',
            'main_humidity': 'humidity_avg',
            'weather_description': 'weather_main'
        }, inplace=True)
        
        return daily_df
    else:
        st.error("Falha ao obter dados da previsão do tempo.")
        return pd.DataFrame()

# CSS para esconder elementos desnecessários, incluindo o rodapé e créditos do criador do aplicativo
hide_streamlit_style = """
    <style>
    MainMenu {visibility: hidden;}
    footer {visibility: hidden;}  /* Esconde o rodapé */
    header {visibility: hidden;}  /* Esconde o cabeçalho */
    [data-testid="stSidebarNav"] {display: none;}  /* Esconde a barra lateral */
    div[role="button"] > svg {display: none;}  /* Esconde o botão flutuante no mobile */

    /* Oculta o ícone e texto de créditos do Streamlit e do criador do app */
    ._profilePreview_51w34_63 {display: none;}  /* Esconde o contêiner de perfil do criador */
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Inicia o DataFrame
daily_df_full = fetch_weather_data()

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
    
# Título da interface
st.title('Tempo em Caxias do Sul 🌤️')

# Botão para atualizar os dados
if st.button('Atualizar Previsão'):
    daily_df_full = fetch_weather_data()

# Exibe a previsão em duas colunas
st.subheader('Previsão para os próximos dias')
cols = st.columns(2)
for i, (index, row) in enumerate(daily_df_full.iterrows()):
    icon = weather_icon(row['weather_main'])
    with cols[i % 2]:  # Alterna entre as duas colunas
        st.markdown(f"<h3>{row['date']} {icon}</h3>", unsafe_allow_html=True)
        
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
                                left: 0%; 
                                width: 2px; 
                                height: 15px; 
                                background: #005577;'></div>
                    <div style='position: absolute; 
                                left: 100%; 
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

# CSS para esconder o rodapé do Streamlit
hide_streamlit_footer = """
    <style>
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_streamlit_footer, unsafe_allow_html=True)
