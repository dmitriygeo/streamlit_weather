import streamlit as st
import pandas as pd
from config import api_key
import pydeck as pdk
from part1_analysis import get_current_temperature, check_temperature_anomaly, seasonal_profile

df = pd.read_csv('temperature_data.csv', parse_dates=['timestamp'], sep=';')

@st.cache_data
def plot_temperature_map(data):
    # Определяем начальный вид карты
    view_state = pdk.ViewState(
        latitude=data['lat'].mean(),
        longitude=data['lon'].mean(),
        zoom=4,
        pitch=50,
    )

    # Создаем слой с данными о температуре
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=data,
        get_position='[lon, lat]',
        get_fill_color='[255 - (temperature * 10), temperature * 10, 150]',
        get_radius=100000,
        pickable=True,
        auto_highlight=True,
    )

    # Создаем объект Deck
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Город: {city}\nТемпература: {temperature} °C"},
    )

    # Отображаем карту в Streamlit
    st.pydeck_chart(deck)


st.title('Анализ исторических данных по температуре в городах')

uploaded_file = st.file_uploader("Загрузите файл с данными", type=['csv'])
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file, sep=';')
    city = st.selectbox('Выберите город', data['city'].unique())
    api_key = st.text_input('Введите ваш API-ключ для OpenWeatherMap', type='password')

    if api_key:
        current_temp = get_current_temperature(city, api_key)
        current_season = st.selectbox('Выберите сезон', data['season'].unique())
        if current_temp:
            is_normal = check_temperature_anomaly(city, current_temp, seasonal_profile, current_season)
            st.write(f'Текущая температура в {city}: {current_temp}°C')
            st.write(f'Температура нормальная для {current_season}' if is_normal else f'Температура аномальная для {current_season}')
        else:
            st.error("Ошибка получения данных из OpenWeatherMap")

        city_data = data[data['city'] == city][['timestamp', 'temperature']]

        # Проверка и преобразование типов данных
        city_data['timestamp'] = pd.to_datetime(city_data['timestamp'], errors='coerce')
        city_data['temperature'] = pd.to_numeric(city_data['temperature'], errors='coerce')

        # Удаление строк с некорректными значениями
        city_data = city_data.dropna()

        # Визуализация
        st.line_chart(city_data.set_index('timestamp'))

        st.write('Дни с аномальными температурами в таблице ниже:')

        moving_mean = df.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).mean())
        std = df.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).std())

        data['anomaly'] = (df['temperature'] > moving_mean + 2 * std) | (df['temperature'] < moving_mean - 2 * std)

        st.dataframe(data[(data['city'] == city) & (data['anomaly'])])


        st.write('Карта температур по городам')

        plot_temperature_map(data)
