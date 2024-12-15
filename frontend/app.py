# frontend/app.py

import streamlit as st
import httpx
from typing import Dict
import asyncio
import pandas as pd
from datetime import datetime
from typing import List

# Настройки Backend API
API_URL = "http://127.0.0.1:8000"

# Конфигурация Streamlit для использования с asyncio
st.set_page_config(page_title="Управление Антикафе", page_icon="☕️")

# Хелперы для отображения уведомлений
def show_success(message):
    st.success(message)

def show_error(message):
    st.error(message)

def show_info(message):
    st.info(message)

async def register_user(first_name, last_name, email, password):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_URL}/register", json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password
            })
            if response.status_code == 201:
                user = response.json()
                return True, user
            else:
                return False, response.json().get("detail", "Ошибка регистрации.")
        except Exception as e:
            return False, str(e)


async def login_user(email, password):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/login",
                json={  # Используем json для передачи данных
                    "email": email,
                    "password": password
                }
            )
            if response.status_code == 200:
                return True, response.json()["access_token"]
            else:
                return False, response.json().get("detail", "Ошибка входа.")
        except Exception as e:
            return False, str(e)

async def get_current_user(token):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/users/me", headers={
                "Authorization": f"Bearer {token}"
            })
            if response.status_code == 200:
                user = response.json()
                return True, user
            else:
                return False, response.json().get("detail", "Не удалось получить данные пользователя.")
        except Exception as e:
            return False, str(e)

def admin_page():
    st.title("Страница администратора")
    menu = ["Пользователи", "Бронирования", "Сессии", "Платежи", "Ресурсы", "Резервные копии"]
    choice = st.sidebar.selectbox("Меню администратора", menu)

    if choice == "Пользователи":
        manage_users()
    elif choice == "Бронирования":
        manage_bookings()
    elif choice == "Ресурсы":
        manage_resources()
    elif choice == "Сессии":
        manage_sessions()
    elif choice == "Платежи":
        manage_payments()
    # Добавьте остальные функции (Бронирования, Сессии и т.д.)

async def fetch_users() -> Dict:
    """Получение списка пользователей с сервера"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/admin/users",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

async def add_user(user_data: Dict) -> Dict:
    """Добавление нового пользователя через сервер"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/admin/users",
                json=user_data,
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200 or response.status_code == 201:
                return {"message": response.json().get("message", "Пользователь успешно добавлен")}
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

async def delete_user(user_id: int) -> Dict:
    """Удаление пользователя через сервер"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_URL}/admin/users/{user_id}",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return {"message": response.json().get("message", "Пользователь успешно удалён")}
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

def manage_users():
    st.subheader("База пользователей")

    # Отображение списка пользователей
    if st.button("Показать всех пользователей"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        users = loop.run_until_complete(fetch_users())
        loop.close()

        if "error" in users:
            st.error(users["error"])
        else:
            df = pd.DataFrame(users)
            st.dataframe(df)

    # Форма для добавления пользователя
    st.subheader("Добавить нового пользователя")
    first_name = st.text_input("Имя", key="add_user_first_name")
    last_name = st.text_input("Фамилия", key="add_user_last_name")
    email = st.text_input("Email", key="add_user_email")
    password = st.text_input("Пароль", type="password", key="add_user_password")
    
    if st.button("Добавить пользователя", key="add_user_button"):
        if first_name and last_name and email and password:
            user_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password
            }
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(add_user(user_data))
            loop.close()

            if "message" in response:
                st.session_state["add_message"] = response["message"]
                st.rerun()  # Обновление страницы после добавления
            elif "error" in response:
                st.error(response["error"])
            else:
                st.error("Ошибка при добавлении пользователя")
        else:
            st.error("Заполните все поля!")

    # Отображение сообщений об успешных операциях
    if "add_message" in st.session_state:
        st.success(st.session_state["add_message"])
        del st.session_state["add_message"]

    st.markdown("---")  # Разделитель между добавлением и удалением

    # Форма для удаления пользователя
    st.subheader("Удалить пользователя")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    users = loop.run_until_complete(fetch_users())
    loop.close()

    if "error" in users:
        st.error(users["error"])
    else:
        if users:
            # Создаём словарь для отображения в selectbox
            user_options = {f"{user['user_id']} - {user['email']}": user['user_id'] for user in users}
            selected_user = st.selectbox("Выберите пользователя для удаления", list(user_options.keys()))
    
            if st.button("Удалить пользователя"):
                user_id = user_options[selected_user]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(delete_user(user_id))
                loop.close()
    
                if "message" in response:
                    st.session_state["delete_message"] = response["message"]
                    st.rerun()  # Обновление страницы после удаления
                elif "error" in response:
                    st.error(response["error"])
                else:
                    st.error("Ошибка при удалении пользователя")
        else:
            st.info("Нет пользователей для удаления.")
    
    if "delete_message" in st.session_state:
        st.success(st.session_state["delete_message"])
        del st.session_state["delete_message"]

async def fetch_bookings() -> Dict:
    """Получение списка бронирований с сервера"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/admin/bookings",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}
        
async def add_booking(booking_data: Dict) -> Dict:
    """Добавление нового бронирования через сервер"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/admin/bookings",
                json=booking_data,
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 201:
                return {"message": "Бронирование успешно добавлено"}
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

async def delete_booking(booking_id: int) -> Dict:
    """Удаление бронирования через сервер"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_URL}/admin/bookings/{booking_id}",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return {"message": "Бронирование успешно удалено"}
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

def manage_bookings():
    st.subheader("Управление бронированиями")

    # Отображение сообщений об успешных операциях
    if "add_booking_message" in st.session_state:
        st.success(st.session_state["add_booking_message"])
        del st.session_state["add_booking_message"]

    if "delete_booking_message" in st.session_state:
        st.success(st.session_state["delete_booking_message"])
        del st.session_state["delete_booking_message"]

    # Отображение списка бронирований
    if st.button("Показать все бронирования"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bookings = loop.run_until_complete(fetch_bookings())
        loop.close()

        if "error" in bookings:
            st.error(bookings["error"])
        else:
            df = pd.DataFrame(bookings)
            st.dataframe(df)

    st.markdown("---")  # Разделитель между выводом и добавлением бронирования

    # Форма для добавления бронирования
    st.write("Добавить новое бронирование")
    # user_id = st.number_input("ID пользователя", min_value=1, step=1, key="booking_user_id")
    # resource_id = st.number_input("ID ресурса", min_value=1, step=1, key="booking_resource_id")
    # Запрос пользователей и ресурсов с сервера
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    users = loop.run_until_complete(fetch_users())
    resources = loop.run_until_complete(fetch_resources())
    loop.close()

    # Проверка и обработка полученных данных
    if "error" in users:
        st.error(users["error"])
        users = []
    if "error" in resources:
        st.error(resources["error"])
        resources = []

    # Выпадающий список пользователей по email
    if users:
        user_options = {f"{user['email']}": user['user_id'] for user in users}
        selected_user_email = st.selectbox("Выберите пользователя (email)", list(user_options.keys()))
        selected_user_id = user_options[selected_user_email]
    else:
        st.warning("Пользователи не найдены.")
        selected_user_id = None

    # Выпадающий список ресурсов по названию
    if resources:
        resource_options = {f"{resource['name']}": resource['resource_id'] for resource in resources}
        selected_resource_name = st.selectbox("Выберите ресурс (название)", list(resource_options.keys()))
        selected_resource_id = resource_options[selected_resource_name]
    else:
        st.warning("Ресурсы не найдены.")
        selected_resource_id = None
    # Выбор даты и времени начала бронирования
    start_date = st.date_input("Дата начала бронирования", key="booking_start_date")
    start_time = st.time_input("Время начала бронирования", key="booking_start_time")
    start_datetime = datetime.combine(start_date, start_time)  # Комбинация в один объект

# Выбор даты и времени окончания бронирования
    end_date = st.date_input("Дата окончания бронирования", key="booking_end_date")
    end_time = st.time_input("Время окончания бронирования", key="booking_end_time")
    end_datetime = datetime.combine(end_date, end_time)
    status = st.selectbox("Статус бронирования", ["active", "completed", "cancelled"], key="booking_status")

    if st.button("Добавить бронирование", key="add_booking_button"):
        if selected_user_id and selected_resource_id and start_time and end_time and status:
            if end_time <= start_time:
                st.error("Время окончания должно быть позже времени начала.")
            else:
                booking_data = {
                    "user_id": selected_user_id,
                    "resource_id": selected_resource_id,
                    "start_time": start_datetime.isoformat(),
                    "end_time": end_datetime.isoformat(),
                    "status": status
                }
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(add_booking(booking_data))
                loop.close()

                if "message" in response:
                    st.session_state["add_booking_message"] = response["message"]
                    st.rerun()  # Обновление страницы после добавления
                elif "error" in response:
                    st.error(response["error"])
                else:
                    st.error("Ошибка при добавлении бронирования")
        else:
            st.error("Пожалуйста, заполните все поля!")

    st.markdown("---")  # Разделитель между добавлением и удалением бронирования

    # Форма для удаления бронирования
    st.write("Удалить бронирование")

    # Получаем данные о бронированиях, пользователях и ресурсах
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bookings = loop.run_until_complete(fetch_bookings())
    users = loop.run_until_complete(fetch_users())
    resources = loop.run_until_complete(fetch_resources())
    loop.close()

    # Проверяем наличие ошибок
    if "error" in bookings:
        st.error(bookings["error"])
    if "error" in users:
        st.error(users["error"])
        users = []
    if "error" in resources:
        st.error(resources["error"])
        resources = []

    # Создаём словарь отображения email и названий ресурсов
    if bookings and users and resources:
        user_dict = {user["user_id"]: user["email"] for user in users}
        resource_dict = {resource["resource_id"]: resource["name"] for resource in resources}

        # Создаем отображение для selectbox
        booking_options = {
            f"{user_dict.get(booking['user_id'], 'Неизвестный пользователь')} - {resource_dict.get(booking['resource_id'], 'Неизвестный ресурс')}": booking['booking_id']
            for booking in bookings
        }
        selected_booking = st.selectbox("Выберите бронирование для удаления", list(booking_options.keys()))

        if st.button("Удалить бронирование"):
            booking_id = booking_options[selected_booking]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(delete_booking(booking_id))
            loop.close()

            if "message" in response:
                st.session_state["delete_booking_message"] = response["message"]
                st.rerun()  # Обновление страницы после удаления
            elif "error" in response:
                st.error(response["error"])
            else:
                st.error("Ошибка при удалении бронирования")
    else:
        st.info("Нет бронирований для удаления.")

async def fetch_resources() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/admin/resources", headers={
            "Authorization": f"Bearer {st.session_state['token']}"
        })
        return response.json() if response.status_code == 200 else {"error": response.text}

async def add_resource(resource_data: Dict) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/admin/resources", json=resource_data, headers={
            "Authorization": f"Bearer {st.session_state['token']}"
        })
        return response.json() if response.status_code == 200 else {"error": response.text}

async def delete_resource(resource_id: int) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{API_URL}/admin/resources/{resource_id}", headers={
            "Authorization": f"Bearer {st.session_state['token']}"
        })
        return response.json() if response.status_code == 200 else {"error": response.text}

def manage_resources():
    st.subheader("Управление ресурсами")

    # Отображение списка ресурсов
    if st.button("Показать все ресурсы"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resources = loop.run_until_complete(fetch_resources())
        loop.close()

        if "error" in resources:
            st.error(resources["error"])
        else:
            df = pd.DataFrame(resources)
            st.dataframe(df)

    # Форма для добавления ресурса
    st.write("Добавить новый ресурс")
    resource_name = st.text_input("Название ресурса", key="add_resource_name")
    # resource_type = st.text_input("Тип ресурса", key="add_resource_type")
    resource_description = st.text_area("Описание ресурса", key="add_resource_description")

    if st.button("Добавить ресурс"):
        if resource_name:
            resource_data = {
                "name": resource_name,
                "description": resource_description
            }
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(add_resource(resource_data))
            loop.close()

            if "message" in response:
                st.success(response["message"])
            elif "error" in response:
                st.error(response["error"])
            else:
                st.error("Ошибка при добавлении ресурса")
        else:
            st.error("Название ресурса обязательно!")

    # Форма для удаления ресурса
    st.write("Удалить ресурс")

    # Получение списка ресурсов с сервера
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    resources = loop.run_until_complete(fetch_resources())
    loop.close()

    if "error" in resources:
        st.error(resources["error"])
    else:
        if resources:
            # Создание выпадающего списка ресурсов по названию
            resource_options = {resource["name"]: resource["resource_id"] for resource in resources}
            selected_resource_name = st.selectbox("Выберите ресурс для удаления", list(resource_options.keys()))

            if st.button("Удалить ресурс"):
                resource_id = resource_options[selected_resource_name]  # Получение ID выбранного ресурса
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(delete_resource(resource_id))
                loop.close()

                if "message" in response:
                    st.success(response["message"])
                elif "error" in response:
                    st.error(response["error"])
                else:
                    st.error("Ошибка при удалении ресурса")
        else:
            st.info("Нет ресурсов для удаления.")
     
async def add_session(session_data: dict) -> dict:
    """Добавление новой сессии через сервер"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/admin/sessions",
                json=session_data,
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

async def fetch_sessions() -> list:
    """Получение списка сессий с сервера"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/admin/sessions",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

async def delete_session(session_id: int) -> dict:
    """Удаление сессии через сервер"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_URL}/admin/sessions/{session_id}",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

def manage_sessions():
    st.subheader("Управление сессиями")

    # --- Отображение списка сессий ---
    if st.button("Показать все сессии"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sessions = loop.run_until_complete(fetch_sessions())
        users = loop.run_until_complete(fetch_users())
        loop.close()

        if "error" in sessions:
            st.error(sessions["error"])
        elif "error" in users:
            st.error(users["error"])
        else:
            if sessions and users:
                # Преобразование данных для отображения
                user_dict = {user["user_id"]: user["email"] for user in users}
                session_data = [
                    {
                        "session_id": session["session_id"],
                        "email": user_dict.get(session["user_id"], "Неизвестный пользователь"),
                        "start_time": session["start_time"],
                        "end_time": session["end_time"],
                    }
                    for session in sessions
                ]
                # Отображение данных в виде таблицы
                df = pd.DataFrame(session_data)
                st.dataframe(df)
            else:
                st.info("Нет доступных сессий.")

    # --- Добавление новой сессии ---
    st.write("Добавить новую сессию")

    # Получение пользователей для выбора
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    users = loop.run_until_complete(fetch_users())
    loop.close()

    if "error" in users:
        st.error(users["error"])
        users = []

    if users:
        # Выпадающий список пользователей
        user_options = {f"{user['email']}": user["user_id"] for user in users}
        selected_user_email = st.selectbox("Выберите пользователя (email)", list(user_options.keys()))
        selected_user_id = user_options[selected_user_email]
    else:
        st.warning("Нет пользователей для выбора.")
        selected_user_id = None

    # Поля для выбора времени начала и окончания сессии
    start_date = st.date_input("Дата начала сессии", key="session_start_date")
    start_time = st.time_input("Время начала сессии", key="session_start_time")
    start_datetime = datetime.combine(start_date, start_time)

    end_date = st.date_input("Дата окончания сессии", key="session_end_date")
    end_time = st.time_input("Время окончания сессии", key="session_end_time")
    end_datetime = datetime.combine(end_date, end_time)

    if st.button("Добавить сессию"):
        if selected_user_id and start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                st.error("Время окончания должно быть позже времени начала.")
            else:
                session_data = {
                    "user_id": selected_user_id,
                    "start_time": start_datetime.isoformat(),
                    "end_time": end_datetime.isoformat(),
                }
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(add_session(session_data))
                loop.close()

                if "message" in response:
                    st.success(response["message"])
                elif "error" in response:
                    st.error(response["error"])
                else:
                    st.error("Ошибка при добавлении сессии.")
        else:
            st.error("Заполните все поля!")

    # --- Удаление сессии ---
    st.write("Удалить сессию")

    # Получение списка сессий и пользователей
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sessions = loop.run_until_complete(fetch_sessions())
    users = loop.run_until_complete(fetch_users())
    loop.close()

    if "error" in sessions:
        st.error(sessions["error"])
    elif "error" in users:
        st.error(users["error"])
    else:
        if sessions:
            # Создаем словарь для сопоставления user_id с email
            user_email_map = {user["user_id"]: user["email"] for user in users}

            # Создание выпадающего списка сессий с email
            session_options = {
                f"{session['start_time']} - {session['end_time']} ( {user_email_map.get(session['user_id'], 'Неизвестный пользователь')})": session["session_id"]
                for session in sessions
            }

            selected_session = st.selectbox("Выберите сессию для удаления", list(session_options.keys()))

            if st.button("Удалить сессию"):
                session_id = session_options[selected_session]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(delete_session(session_id))
                loop.close()

                if "message" in response:
                    st.success(response["message"])
                elif "error" in response:
                    st.error(response["error"])
                else:
                    st.error("Ошибка при удалении сессии.")
        else:
            st.info("Нет доступных сессий для удаления.")

# --- Получение списка платежей ---
async def fetch_payments():
    """
    Получение списка платежей с сервера.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/admin/payments",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

# --- Добавление платежа ---
async def add_payment(payment_data):
    """
    Добавление нового платежа через сервер.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/admin/payments",
                json=payment_data,
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

# --- Удаление платежа ---
async def delete_payment(payment_id):
    """
    Удаление платежа через сервер.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_URL}/admin/payments/{payment_id}",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Обработка ошибок от сервера
                try:
                    error_detail = response.json().get("detail", "Неизвестная ошибка")
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

def manage_payments():
    st.subheader("Управление платежами")

    # --- Отображение списка платежей ---
    if st.button("Показать все платежи"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        payments = loop.run_until_complete(fetch_payments())
        users = loop.run_until_complete(fetch_users())
        loop.close()

        if "error" in payments:
            st.error(payments["error"])
        elif "error" in users:
            st.error(users["error"])
        else:
            if payments and users:
                # Создаем словарь для сопоставления user_id с email
                user_email_map = {user["user_id"]: user["email"] for user in users}

                # Преобразование данных для отображения
                payment_data = [
                    {
                        "payment_id": payment["payment_id"],
                        "email": user_email_map.get(payment["user_id"], "Неизвестный пользователь"),
                        "amount": payment["amount"],
                    }
                    for payment in payments
                ]
                # Отображение данных в виде таблицы
                df = pd.DataFrame(payment_data)
                st.dataframe(df)
            else:
                st.info("Нет доступных платежей.")

    # --- Добавление нового платежа ---
    st.write("Добавить новый платеж")

    # Получение списка пользователей
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    users = loop.run_until_complete(fetch_users())
    loop.close()

    if "error" in users:
        st.error(users["error"])
        users = []

    if users:
        # Выпадающий список пользователей
        user_options = {f"{user['email']}": user["user_id"] for user in users}
        selected_user_email = st.selectbox("Выберите пользователя (email)", list(user_options.keys()))
        selected_user_id = user_options[selected_user_email]
    else:
        st.warning("Нет пользователей для выбора.")
        selected_user_id = None

    # Поле для ввода суммы платежа
    amount = st.number_input("Сумма платежа", min_value=0.01, step=0.01, key="payment_amount")

    if st.button("Добавить платеж"):
        if selected_user_id and amount > 0:
            payment_data = {
                "user_id": selected_user_id,
                "amount": amount,
            }
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(add_payment(payment_data))
            loop.close()

            if "message" in response:
                st.success(response["message"])
            elif "error" in response:
                st.error(response["error"])
            else:
                st.error("Ошибка при добавлении платежа.")
        else:
            st.error("Пожалуйста, заполните все поля!")

    # --- Удаление платежа ---
    st.write("Удалить платеж")

    # Получение списка платежей и пользователей
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    payments = loop.run_until_complete(fetch_payments())
    users = loop.run_until_complete(fetch_users())
    loop.close()

    if "error" in payments:
        st.error(payments["error"])
    elif "error" in users:
        st.error(users["error"])
    else:
        if payments:
            # Создаём словарь email пользователей
            user_emails = {user['user_id']: user['email'] for user in users}

            # Создание выпадающего списка платежей
            payment_options = {
                f"{payment['amount']} - {user_emails.get(payment['user_id'], 'Неизвестный')}": payment["payment_id"]
                for payment in payments
            }
            selected_payment = st.selectbox("Выберите платеж для удаления", list(payment_options.keys()))

            if st.button("Удалить платеж"):
                payment_id = payment_options[selected_payment]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(delete_payment(payment_id))
                loop.close()

                if "message" in response:
                    st.success(response["message"])
                elif "error" in response:
                    st.error(response["error"])
                else:
                    st.error("Ошибка при удалении платежа.")
        else:
            st.info("Нет доступных платежей для удаления.")


def main():
    # Проверяем, есть ли токен и данные пользователя
    if 'token' not in st.session_state:
        st.session_state['token'] = None
    
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Если администратор вошёл в систему
    if st.session_state['user'] and st.session_state['user']['role_name'] == 'admin':
        st.sidebar.success(f"Вы вошли как администратор: {st.session_state['user']['first_name']}")

        # Кнопка для выхода
        if st.sidebar.button("Выйти"):
            st.session_state['token'] = None
            st.session_state['user'] = None
            st.rerun()

        # Отображение страницы администратора
        admin_page()
    else:
        # Главное меню для пользователей, которые ещё не вошли в систему
        menu = ["Вход", "Регистрация"]
        choice = st.sidebar.selectbox("Меню", menu)

        if choice == "Вход":
            st.title("Вход в систему")
            # st.subheader("Форма")
            
            email = st.text_input("Email")
            password = st.text_input("Пароль", type='password')
            
            if st.button("Войти"):
                if email and password:
                    # Асинхронный вызов для входа
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success, result = loop.run_until_complete(login_user(email, password))
                    loop.close()
                    
                    if success:
                        st.session_state['token'] = result
                        # Получение данных пользователя
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success, user = loop.run_until_complete(get_current_user(result))
                        loop.close()
                        
                        if success:
                            st.session_state['user'] = user
                            show_success(f"Добро пожаловать, {user['first_name']}!")
                            st.rerun()
                        else:
                            show_error(user)
                    else:
                        show_error(result)
                else:
                    show_error("Пожалуйста, заполните все поля.")

        elif choice == "Регистрация":
            st.title("Регистрация нового пользователя")
            # st.subheader("Форма")
            
            first_name = st.text_input("Имя")
            last_name = st.text_input("Фамилия")
            email = st.text_input("Email")
            password = st.text_input("Пароль", type='password')
            password_confirm = st.text_input("Подтвердите пароль", type='password')
            
            if st.button("Зарегистрироваться"):
                if not all([first_name, last_name, email, password, password_confirm]):
                    show_error("Пожалуйста, заполните все поля.")
                elif password != password_confirm:
                    show_error("Пароли не совпадают.")
                else:
                    # Асинхронный вызов для регистрации
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success, result = loop.run_until_complete(register_user(first_name, last_name, email, password))
                    loop.close()
                    
                    if success:
                        show_success("Регистрация прошла успешно! Теперь вы можете войти.")
                        show_info("Переключитесь на вкладку 'Вход'.")
                    else:
                        show_error(result)



# Запуск приложения
if __name__ == '__main__':
    main()