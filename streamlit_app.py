import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime

st.title("☀️ Анализ погоды на основе исторических данных")
st.header("Загрузка данных")
uploaded_file = st.file_uploader("Загрузите CSV-файл с историческими погодными данными:", type=["csv"])

if uploaded_file is not None:
    try:
        data = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
        required_columns = {"timestamp", "city", "temperature"}
        if not required_columns.issubset(data.columns):
            st.error(f"Ошибка: в файле должны быть следующие поля: {', '.join(required_columns)}")
        else:
            st.sidebar.header("Настройки фильтра")
            city_list = data['city'].unique()
            selected_city = st.sidebar.selectbox("Выберите город:", city_list)
            city_data = data[data["city"] == selected_city]
            city_data = city_data.sort_values("timestamp")
            city_data.set_index("timestamp", inplace=True)

            st.success(f"Данные успешно загружены для города: {selected_city}")

            st.header("Описательная статистика")
            stats = city_data["temperature"].describe()
            st.write(stats)
            st.header("График температур с аномалиями")
            rolling_mean = city_data['temperature'].rolling(window=30, center=True).mean()
            rolling_std = city_data['temperature'].rolling(window=30, center=True).std()

            anomalies = city_data[
                (city_data['temperature'] > rolling_mean + 2 * rolling_std) |
                (city_data['temperature'] < rolling_mean - 2 * rolling_std)
            ]

            plt.figure(figsize=(10, 5))
            plt.plot(city_data.index, city_data['temperature'], label="Температура")
            if not anomalies.empty:
                plt.scatter(anomalies.index, anomalies['temperature'], color='red', label="Аномалии")
            plt.xlabel("Дата")
            plt.ylabel("Температура")
            plt.legend()
            st.pyplot(plt.gcf())
            st.header("Сезонный профиль температуры")
            city_data['month'] = city_data.index.month
            seasonal_stats = city_data.groupby('month')['temperature'].agg(['mean', 'std'])

            plt.figure(figsize=(10, 5))
            plt.errorbar(seasonal_stats.index, seasonal_stats['mean'], yerr=seasonal_stats['std'], fmt='o', capsize=5)
            plt.xticks(range(1, 13))
            plt.title("Среднемесячная температура с учетом отклонений")
            plt.xlabel("Месяц")
            plt.ylabel("Температура (°C)")
            st.pyplot(plt.gcf())

            st.header("API OpenWeatherMap")
            api_key = st.text_input("Введите API-ключ OpenWeatherMap (оставьте пустым, чтобы пропустить):", type='password')

            if api_key:

                try:
                    geocode_url = f"https://api.openweathermap.org/geo/1.0/direct"
                    geo_params = {"q": selected_city, "limit": 1, "appid": api_key}
                    geo_response = requests.get(geocode_url, params=geo_params)

                    if geo_response.status_code == 200:
                        geo_data = geo_response.json()
                        if len(geo_data) == 0:
                            st.warning("Город не найден в базе OpenWeatherMap.")
                        else:
                            latitude = geo_data[0]["lat"]
                            longitude = geo_data[0]["lon"]
                            weather_url = f"https://api.openweathermap.org/data/2.5/weather"

                            weather_params = {
                                "lat": latitude,
                                "lon": longitude,
                                "appid": api_key,
                                "units": "metric"
                            }
                            weather_response = requests.get(weather_url, params=weather_params)

                            if weather_response.status_code == 200:
                                weather_data = weather_response.json()
                                current_temp = weather_data['main']['temp']
                                st.success(f"Текущая температура в городе {selected_city}: {current_temp}°C")
                                current_month = datetime.datetime.now().month
                                if current_month in seasonal_stats.index:
                                    avg_temp = seasonal_stats.loc[current_month, 'mean']
                                    temp_std = seasonal_stats.loc[current_month, 'std']

                                    if abs(current_temp - avg_temp) > (2 * temp_std):
                                        st.warning(f"Температура {current_temp}°C отклоняется от сезонной нормы.")
                                    else:
                                        st.info(f"Температура {current_temp}°C соответствует сезонной норме.")
                                else:
                                    st.info("Данные для текущего месяца отсутствуют.")
                            else:
                                st.error(f"Ошибка при запросе текущей погоды. Сообщение: {weather_response.json()['message']}")
                    else:
                        st.error(f"Ошибка при запросе координат города. Сообщение: {geo_response.json()['message']}")
                except Exception as e:
                    st.error(f"Произошла ошибка: {e}")
    except Exception as e:
        st.error(f"Не удалось обработать файл. Убедитесь, что он корректного формата. Ошибка: {e}")
else:
    st.info("Пожалуйста, загрузите CSV-файл для анализа.")
