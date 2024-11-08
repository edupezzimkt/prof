import requests
import pandas as pd
import streamlit as st
import datetime

# CSS para esconder elementos indesejados na interface do Streamlit
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

# Função para obter a previsão do tempo
def fetch_weather_data():
    api_key = '680e436df2f7321be79cef2383e624a8'
    city_id = '3466537'  # Caxias do Sul
    base_url = 'http://api.openweathermap.org/data/2.5/forecast'
    url = f"{base_url}?id={city_id}&appid={api_key}&units=metric&lang=pt_br"

    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        forecast_list = weather_data['list']
        df = pd.json_normalize(forecast_list)
        
        # Ajustar as colunas para um formato mais amigável
        df.columns = df.columns.str.replace('main.', 'main_', regex=False)
        df.columns = df.columns.str.replace('wind.', 'wind_', regex=False)
        df.columns = df.columns.str.replace('clouds.', 'clouds_', regex=False)
        df.columns = df.columns.str.replace('sys.', 'sys_', regex=False)
        df.columns = df.columns.str.replace('weather.', 'weather_', regex=False)
        
        weather_expanded = df['weather'].apply(lambda x: x[0] if len(x) > 0 else {})
        df['weather_id'] = weather_expanded.apply(lambda x: x.get('id', None))
        df['weather_main'] = weather_expanded.apply(lambda x: x.get('main', None))
        df['weather_description'] = weather_expanded.apply(lambda x: x.get('description', None))
        df['weather_icon'] = weather_expanded.apply(lambda x: x.get('icon', None))
        df.drop(columns=['weather'], inplace=True)
        
        df['dt_txt'] = pd.to_datetime(df['dt_txt'])
        df['date'] = df['dt_txt'].dt.date
        
        daily_df_full = df.groupby('date').agg({
            'main_temp_min': 'min',
            'main_temp_max': 'max',
            'main_humidity': 'mean',
            'weather_description': lambda x: x.mode()[0] if not x.mode().empty else 'N/A'
        }).reset_index()
        
        daily_df_full['main_humidity'] = daily_df_full['main_humidity'].round().astype(int)
        
        daily_df_full.rename(columns={
            'main_temp_min': 'temp_min',
            'main_temp_max': 'temp_max',
            'main_humidity': 'humidity_avg',
            'weather_description': 'weather_main'
        }, inplace=True)
        
        return daily_df_full
    else:
        st.error("Não foi possível obter os dados da API.")
        return None

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

# Executando a função para obter os dados de previsão
daily_df_full = fetch_weather_data()

# Exibindo a previsão se os dados foram obtidos com sucesso
if daily_df_full is not None:
    st.subheader('Previsão para os próximos dias')

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
else:
    st.write("Nenhuma previsão disponível no momento.")
