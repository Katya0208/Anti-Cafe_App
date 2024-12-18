# frontend/app.py

import streamlit as st
import httpx
from typing import Dict
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import List
from typing import Optional

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
                json={  # json для передачи данных
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
    menu = ["Пользователи", "Бронирования", "Сессии", "Платежи", "Ресурсы", "Логи"]
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
    elif choice == "Логи":
        manage_logs()

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

async def fetch_session_logs() -> List[Dict]:
    """Получение логов сессий."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/logs/sessions",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

def manage_logs():
    st.write("Логи системы")
    if st.button("Показать логи сессий"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        session_logs = loop.run_until_complete(fetch_session_logs())
        loop.close()

        if isinstance(session_logs, dict) and "error" in session_logs:
            st.error(session_logs["error"])
        else:
            # Преобразуем логи в DataFrame
            df_logs = pd.DataFrame(session_logs)
            if not df_logs.empty:
                # Преобразуем колонку event_time в читаемый формат
                if 'event_time' in df_logs.columns:
                    df_logs['event_time'] = pd.to_datetime(df_logs['event_time'])
                st.dataframe(df_logs)
            else:
                st.info("Логи сессий отсутствуют.")

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

async def fetch_roles():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/roles", headers={
            "Authorization": f"Bearer {st.session_state['token']}"
        })
        return response.json()

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

    # Получение списка ролей
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    roles = loop.run_until_complete(fetch_roles())
    loop.close()

    if "error" in roles:
        st.error(roles["error"])
        roles = []
    else:
        role_options = {role["role_name"]: role["role_id"] for role in roles}
        selected_role = st.selectbox("Выберите роль пользователя", list(role_options.keys()))
        selected_role_id = role_options[selected_role] if roles else None

    if st.button("Добавить пользователя", key="add_user_button"):
        if first_name and last_name and email and password and selected_role_id:
            user_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password,
                "role_id": selected_role_id
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
    resource_description = st.text_area("Описание ресурса", key="add_resource_description")
    hourly_rate = st.number_input("Стоимость за час", min_value=0.0, step=0.1, key="add_resource_hourly_rate")

    if st.button("Добавить ресурс"):
        if resource_name:
            resource_data = {
                "name": resource_name,
                "description": resource_description,
                "hourly_rate": hourly_rate
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

def calculate_free_windows(bookings, start_hour=10, end_hour=1):
    """
    Рассчитать свободные окна для ресурса с учётом рабочего времени (10:00 до 01:00 следующего дня).
    Если end_hour <= start_hour, считаем, что конец рабочего дня наступает на следующий день.
    """

    # Базовая дата для расчётов (можно любую дату, важны только время)
    base_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    # Начало
    work_start = base_date + timedelta(hours=start_hour)

    # Конец
    if end_hour <= start_hour:
        hours_to_end = 24 - (start_hour - end_hour)
        work_end = work_start + timedelta(hours=hours_to_end)
    else:
        
        work_end = base_date + timedelta(hours=end_hour)
        if work_end <= work_start:
            work_end += timedelta(days=1)

    # Преобразуем бронирования в datetime и сортируем
    reserved_windows = []
    for booking in bookings:
        try:
            reserved_start = datetime.fromisoformat(booking["start_time"])
            reserved_end = datetime.fromisoformat(booking["end_time"])
            reserved_windows.append((reserved_start, reserved_end))
        except Exception:
            continue

    reserved_windows.sort()

    free_windows = []
    current_start = work_start

    for reserved_start, reserved_end in reserved_windows:
        # Если начало брони позже current_start — есть свободный промежуток
        if reserved_start > current_start:
            free_windows.append({
                "start": current_start.strftime("%H:%M"),
                "end": reserved_start.strftime("%H:%M")
            })
        current_start = max(current_start, reserved_end)

    # Проверка свободного времени после последнего бронирования до конца рабочего дня
    if current_start < work_end:
        free_windows.append({
            "start": current_start.strftime("%H:%M"),
            "end": work_end.strftime("%H:%M")
        })

    return free_windows
async def fetch_resource_bookings(resource_id: int, date: str) -> List[Dict]:
    """Получение информации о бронированиях ресурса на определённую дату."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/resources/bookings",
            params={"resource_id": resource_id, "date": date},
            headers={"Authorization": f"Bearer {st.session_state['token']}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}

async def fetch_user_bookings() -> List[Dict]:
    """Получение бронирований текущего пользователя."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/user/bookings",
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

async def fetch_user_bookings_staff(user_id: int) -> List[Dict]:
    """Получение бронирований конкретного пользователя (для staff)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/staff/users/{user_id}/bookings",
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

async def cancel_booking_staff(booking_id: int) -> Dict:
    """Отмена бронирования (для staff)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{API_URL}/staff/bookings/{booking_id}/cancel",
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

async def fetch_user_payments(user_id: int) -> List[Dict]:
    """Получение платежей пользователя (для staff)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/staff/users/{user_id}/payments",
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

async def add_user_payment(user_id: int, payment: Dict) -> Dict:
    """Добавление нового платежа для пользователя (для staff)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/staff/users/{user_id}/payments",
                json=payment,
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 201:
                return response.json()
            else:
                return {"error": response.text}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

async def start_session_staff(user_id: int, start_time: str) -> Dict:
    """Установка начала сессии для пользователя (для staff)."""
    try:
        async with httpx.AsyncClient() as client:
            session_data = {
                "user_id": user_id,
                "start_time": start_time
            }
            response = await client.post(
                f"{API_URL}/staff/sessions/start",
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

async def end_session_staff(session_id: int, end_time: str) -> Dict:
    """Установка конца сессии для пользователя (для staff)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/staff/sessions/end",
                params={"session_id": session_id, "end_time": end_time},
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

async def complete_booking_staff(booking_id: int) -> Dict:
    """Завершение бронирования (установка статуса 'completed')."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{API_URL}/staff/bookings/{booking_id}/complete",
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = "Неизвестная ошибка"
                return {"error": error_detail}
    except httpx.HTTPError as http_err:
        return {"error": f"Ошибка HTTP: {str(http_err)}"}
    except Exception as e:
        return {"error": f"Неизвестная ошибка: {str(e)}"}

async def fetch_all_users() -> List[Dict]:
    """Получение списка всех пользователей (для staff)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/admin/users",
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

# --- Страница Staff ---
def staff_page():
    st.title("Страница Сотрудника")
    
    # --- Выбор пользователя ---
    st.subheader("Выбор пользователя")
    
    # Загрузка списка пользователей
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    users = loop.run_until_complete(fetch_all_users())
    loop.close()
    
    if "error" in users:
        st.error(users["error"])
        users = []
    
    if users:
        user_options = {f"{user['first_name']} {user['last_name']} (ID: {user['user_id']})": user['user_id'] for user in users}
        selected_user_display = st.selectbox("Выберите пользователя", list(user_options.keys()))
        selected_user_id = user_options[selected_user_display]
    else:
        st.warning("Нет доступных пользователей.")
        return
    
    st.markdown("---")
    
    # --- Управление сессией ---
    st.subheader("Управление сессией пользователя")
    
    # Получение активных сессий пользователя
    async def fetch_active_session(user_id: int) -> Optional[Dict]:
        """Получение активной сессии пользователя."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_URL}/staff/sessions/active",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {st.session_state['token']}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data if data else None
                else:
                    return {"error": response.text}
        except httpx.HTTPError as http_err:
            return {"error": f"Ошибка HTTP: {str(http_err)}"}
        except Exception as e:
            return {"error": f"Неизвестная ошибка: {str(e)}"}
    

    # Проверяем наличие активной сессии
    # Здесь предполагается, что такой маршрут существует
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    active_session = loop.run_until_complete(fetch_active_session(selected_user_id))
    loop.close()
    
    if active_session and "error" not in active_session:
        st.info(f"Активная сессия: Начало - {active_session['start_time']}")
        if st.button("Установить конец сессии"):
            # Используйте st.date_input и st.time_input для выбора даты и времени
            end_date = st.date_input("Выберите дату окончания сессии", value=datetime.now().date())
            end_time = st.time_input("Выберите время окончания сессии", value=datetime.now().time())
            end_datetime = datetime.combine(end_date, end_time)
            end_time_iso = end_datetime.isoformat()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(end_session_staff(active_session['session_id'], end_time_iso))
            loop.close()
            if "error" in response:
                st.error(response["error"])
            else:
                st.success("Конец сессии успешно установлен.")
                st.rerun()
    else:
        st.warning("У пользователя нет активных сессий.")
        if st.button("Установить начало сессии"):
            start_date = st.date_input("Выберите дату начала сессии", value=datetime.now().date())
            start_time = st.time_input("Выберите время начала сессии", value=datetime.now().time())
            start_datetime = datetime.combine(start_date, start_time)
            start_time_iso = start_datetime.isoformat()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(start_session_staff(selected_user_id, start_time_iso))
            loop.close()
            if "error" in response:
                st.error(response["error"])
            else:
                st.success("Начало сессии успешно установлено.")
                st.rerun()
    
    st.markdown("---")
    
    # --- Просмотр и управление бронированиями ---
    st.subheader("Просмотр и управление бронированиями пользователя")
    
    if st.button("Показать бронирования пользователя"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        user_bookings = loop.run_until_complete(fetch_user_bookings_staff(selected_user_id))
        loop.close()
        
        if "error" in user_bookings:
            st.error(user_bookings["error"])
        else:
            if user_bookings:
                # Запрос ресурсов для сопоставления resource_id с именами
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resources = loop.run_until_complete(fetch_resources())
                loop.close()
        
                resource_dict = {resource['resource_id']: resource['name'] for resource in resources} if resources and "error" not in resources else {}
        
                # Преобразуем данные в DataFrame для удобного отображения
                df_user_bookings = pd.DataFrame(user_bookings)
                # Преобразуем столбцы с датой и временем в читаемый формат
                df_user_bookings['start_time'] = pd.to_datetime(df_user_bookings['start_time']).dt.strftime('%Y-%m-%d %H:%M')
                df_user_bookings['end_time'] = pd.to_datetime(df_user_bookings['end_time']).dt.strftime('%Y-%m-%d %H:%M')
                # Добавим название ресурса
                df_user_bookings['resource_name'] = df_user_bookings['resource_id'].map(resource_dict).fillna('Неизвестный ресурс')
                
                # Добавим колонку с кнопками для отмены бронирования
                for index, row in df_user_bookings.iterrows():
                    if row['status'] != 'cancelled':
                        if st.button(f"Отменить бронирование ID: {row['booking_id']}"):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            response = loop.run_until_complete(cancel_booking_staff(row['booking_id']))
                            loop.close()
                            if "error" in response:
                                st.error(response["error"])
                            else:
                                st.success(f"Бронирование ID: {row['booking_id']} отменено.")
                                st.rerun()
                
                st.dataframe(df_user_bookings[['booking_id', 'resource_name', 'start_time', 'end_time', 'status']])
            else:
                st.info("У пользователя нет бронирований.")
    
    st.markdown("---")
    
    # --- Управление платежами ---
    st.subheader("Просмотр и добавление платежей пользователя")
    
    if st.button("Показать платежи пользователя"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        user_payments = loop.run_until_complete(fetch_user_payments(selected_user_id))
        loop.close()
        
        if "error" in user_payments:
            st.error(user_payments["error"])
        else:
            if user_payments:
                df_user_payments = pd.DataFrame(user_payments)
                df_user_payments['payment_date'] = pd.to_datetime(df_user_payments['payment_date']).dt.strftime('%Y-%m-%d %H:%M')
                st.dataframe(df_user_payments[['payment_id', 'amount', 'payment_date']])
            else:
                st.info("У пользователя нет платежей.")
    
    st.markdown("---")
    
    st.subheader("Добавить платеж пользователя")
    
    with st.form("add_payment_form"):
        payment_amount = st.number_input("Сумма платежа (руб)", min_value=0.0, step=10.0)
        payment_date = st.date_input("Дата платежа", value=datetime.now().date())
        payment_time = st.time_input("Время платежа", value=datetime.now().time())
        payment_datetime = datetime.combine(payment_date, payment_time)
        submitted = st.form_submit_button("Добавить платеж")
        if submitted:
            if payment_amount <= 0:
                st.error("Сумма платежа должна быть положительной.")
            else:
                payment_data = {
                    "user_id": selected_user_id,
                    "amount": payment_amount,
                    "payment_date": payment_datetime.isoformat()
                }
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(add_user_payment(selected_user_id, payment_data))
                loop.close()
                if "error" in response:
                    st.error(response["error"])
                else:
                    st.success("Платеж успешно добавлен.")
                    st.rerun()
    
    st.markdown("---")
    
    # --- Расчет стоимости посещения ---
    st.subheader("Расчет стоимости посещения пользователя")
    
    if st.button("Рассчитать стоимость"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        active_session = loop.run_until_complete(fetch_active_session(selected_user_id))
        loop.close()

        if active_session and "error" not in active_session:
            session_start = datetime.fromisoformat(active_session['start_time'])
            session_duration = datetime.now() - session_start
            session_minutes = int(session_duration.total_seconds() // 60)
        else:
            session_minutes = 0

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        active_bookings = loop.run_until_complete(fetch_user_bookings_staff(selected_user_id))
        loop.close()

        if "error" in active_bookings:
            st.error(active_bookings["error"])
            active_bookings = []

        # Получаем ресурсы для определения hourly_rate
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resources_data = loop.run_until_complete(fetch_resources())
        loop.close()

        if "error" in resources_data:
            st.error(resources_data["error"])
            resources_data = []
        
        # Создаём словарь id ресурса -> hourly_rate
        resource_price = {}
        for r in resources_data:
            resource_price[r['resource_id']] = r['hourly_rate']

        # Рассчитываем стоимость бронирований
        active_booking_minutes = 0
        booking_cost = 0.0
        for booking in active_bookings:
            if booking['status'] == 'active':
                booking_start = datetime.fromisoformat(booking['start_time'])
                booking_end = datetime.fromisoformat(booking['end_time'])
                booking_duration = booking_end - booking_start
                b_minutes = int(booking_duration.total_seconds() // 60)
                active_booking_minutes += b_minutes

                # Получаем цену ресурса
                r_id = booking['resource_id']
                if r_id in resource_price:
                    hourly_rate = resource_price[r_id]
                else:
                    hourly_rate = 0.0
                
                # Цена за бронирование = (минуты / 60) * hourly_rate
                booking_cost += (b_minutes / 60) * hourly_rate

                # Завершаем бронирование, устанавливаем статус 'completed'
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                complete_response = loop.run_until_complete(complete_booking_staff(booking['booking_id']))
                loop.close()
                if "error" in complete_response:
                    st.error(complete_response["error"])

        # Стоимость сессии
        rate_per_minute = 5  # 5 руб/минута
        session_cost = session_minutes * rate_per_minute

        # Общая стоимость
        total_cost = booking_cost + session_cost

        # Проверка на стоп-чек
        stop_check_hours = 3
        stop_check_max = 900  # руб
        if (session_minutes + active_booking_minutes) > stop_check_hours * 60:
            total_cost = stop_check_max
            st.info(f"Общее время превышает {stop_check_hours} часов. Применен стоп-чек: {stop_check_max} рублей.")

        st.success(f"Общая стоимость пребывания: {total_cost} рублей.")

def user_page():

    st.title("Бронирование оборудования и помещений")

    # Запрос ресурсов с сервера
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    resources = loop.run_until_complete(fetch_resources())
    loop.close()

    if "error" in resources:
        st.error(resources["error"])
        return

    # Выпадающий список ресурсов
    if resources:
        resource_options = {f"{resource['name']} (Стоимость: {resource['hourly_rate']} руб/час)": resource['resource_id'] for resource in resources}
        selected_resource_name = st.selectbox("Выберите ресурс для бронирования", list(resource_options.keys()))
        selected_resource_id = resource_options[selected_resource_name]
    else:
        st.warning("Нет доступных ресурсов для бронирования.")
        return

    # Выбор даты
    selected_date = st.date_input("Выберите дату бронирования", min_value=datetime.today().date())
    
    if st.button("Показать занятые окна"):
        # Запрос информации о бронированиях
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bookings = loop.run_until_complete(fetch_resource_bookings(selected_resource_id, selected_date.isoformat()))
        loop.close()

        if "error" in bookings:
            st.error(bookings["error"])
        else:
            # Вывод занятых интервалов бронирования
            if bookings:
                st.write("Занятые интервалы бронирования:")
                bookings.sort(key=lambda x: x["start_time"])
                for booking in bookings:
                    start_time = datetime.fromisoformat(booking["start_time"]).strftime("%H:%M")
                    end_time = datetime.fromisoformat(booking["end_time"]).strftime("%H:%M")
                    st.write(f"{start_time} - {end_time}")
            else:
                st.warning("На выбранную дату ресурс не забронирован. Он свободен в течение всего рабочего дня (10:00 - 01:00).")

    st.markdown("---")

    # Форма для добавления бронирования
    st.subheader("Создать бронирование")

    # Проверим, что пользователь авторизован и есть его данные
    if 'user' not in st.session_state or st.session_state['user'] is None:
        st.error("Сначала войдите в систему, чтобы сделать бронирование.")
        return
    
    user_id = st.session_state['user']['user_id']
    # Выбор времени начала и конца бронирования
    start_time = st.time_input("Время начала бронирования", key="user_booking_start_time")
    end_time = st.time_input("Время окончания бронирования", key="user_booking_end_time")

    # Комбинируем выбранную дату и время
    start_datetime = datetime.combine(selected_date, start_time)
    end_datetime = datetime.combine(selected_date, end_time)
    
    if st.button("Забронировать"):
        if end_datetime <= start_datetime:
            st.error("Время окончания должно быть позже времени начала.")
        else:
            # Добавление бронирования
            booking_data = {
                "user_id": user_id,
                "resource_id": selected_resource_id,
                "start_time": start_datetime.isoformat(),
                "end_time": end_datetime.isoformat(),
                "status": "active"
            }
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(add_booking(booking_data))
            loop.close()

            if "message" in response:
                st.success(response["message"])
                st.rerun()  # Обновление страницы после добавления
            elif "error" in response:
                st.error(response["error"])
            else:
                st.error("Ошибка при добавлении бронирования.")

    st.markdown("---")
    st.subheader("Рассчитайте стоимость пребывания:")

    # Ввод часов и минут
    stay_hours = st.number_input("Часы пребывания", min_value=0, max_value=15, step=1)
    stay_minutes = st.number_input("Минуты пребывания", min_value=0, max_value=59, step=1)

    if st.button("Рассчитать стоимость"):
        total_minutes = stay_hours * 60 + stay_minutes
        rate_per_minute = 5  # 5 руб/минута
        stop_check_hours = 3
        stop_check_max = 900  # руб

        if total_minutes > stop_check_hours * 60:
            # Применяем стоп-чек
            total_cost = stop_check_max
            st.info(f"Вы провели более {stop_check_hours} часов. Применен стоп-чек: {stop_check_max} рублей.")
        else:
            total_cost = total_minutes * rate_per_minute
        
        st.success(f"Стоимость за {stay_hours} час(а/ов) и {stay_minutes} минут(ы): {total_cost} рублей.")


def main():
    # Проверяем, есть ли токен и данные пользователя
    if 'token' not in st.session_state:
        st.session_state['token'] = None
    
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Если пользователь вошёл в систему
    if st.session_state['user']:
        st.sidebar.success(f"Вы вошли как {st.session_state['user']['first_name']} ({st.session_state['user']['role_name']})")
        
        # Кнопка для выхода
        if st.sidebar.button("Выйти"):
            st.session_state['token'] = None
            st.session_state['user'] = None
            st.rerun()

        # Отображение страниц в зависимости от роли
        if st.session_state['user']['role_name'] == 'admin':
            admin_page()
        elif st.session_state['user']['role_name'] == 'staff':
            staff_page()
        else:
            user_page()

    else:
        # Главное меню для пользователей, которые ещё не вошли в систему
        menu = ["Вход", "Регистрация"]
        choice = st.sidebar.selectbox("Меню", menu)

        if choice == "Вход":
            st.title("Вход в систему")
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