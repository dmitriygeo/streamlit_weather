import pandas as pd
import time
from joblib import Parallel, delayed
import requests
#from config import api_key

#api_key = api_key

df = pd.read_csv('temperature_data.csv', parse_dates=['timestamp'], sep=';')

# скользящее среднее, стандартное отклонение и расчет аномалий (последовательная функция)
def historical_data(df):
    moving_mean = df.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).mean())
    std = df.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).std())

    anomaly = (df['temperature'] > moving_mean + 2 * std) | (df['temperature'] < moving_mean - 2 * std)
    return moving_mean, std, anomaly

# сезонный профиль
def season(df):
    seasonal_profile = df.groupby(['city', 'season']).agg(
        mean_temp=('temperature', 'mean'),
        std_temp=('temperature', 'std')
    ).reset_index()
    return seasonal_profile

start_time = time.time()
consistent_func = historical_data(df)
end_time = time.time()
print(f"выполнено за {end_time- start_time:.2f} секунд")

# вызов функции для расчет профиля сезона
seasonal_profile = season(df)

# параллельная функция для расчета аномалий, скользящего среднего и стд
def parallel_historical_data(df):
    moving_mean = df.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).mean())
    std = df.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).std())

    anomaly = (df['temperature'] > moving_mean + 2 * std) | (df['temperature'] < moving_mean - 2 * std)
    return moving_mean, std, anomaly

start_time_par = time.time()
parallel_func = Parallel(n_jobs=1)(delayed(parallel_historical_data)(city_data) for city, city_data in df.groupby('city'))
end_time_par = time.time()
print(f"выполнено за {end_time_par - start_time_par:.2f} секунд")

# получение температуры через api
def get_current_temperature(city, api_key):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    response = requests.get(url)
    data = response.json()
    return data['main']['temp']

current_temp = get_current_temperature(city='Moscow', api_key=api_key)

# сравнение текущей температуры с историческими данными
def check_temperature_anomaly(city, current_temp, seasonal_profile, current_season):
    city_stat = seasonal_profile[(seasonal_profile['city'] == city) & (seasonal_profile['season'] == current_season)]
    mean_temp = city_stat['mean_temp'].values[0]
    std_temp = city_stat['std_temp'].values[0]
    lower_bound = mean_temp - 2 * std_temp
    upper_bound = mean_temp + 2 * std_temp
    return lower_bound <= current_temp <= upper_bound

print(f"Температура в норме:"
      f" {check_temperature_anomaly('Berlin', current_temp, seasonal_profile, 'winter')}")
print(f"Температура в норме:"
      f" {check_temperature_anomaly('Moscow', current_temp, seasonal_profile, 'winter')}")
