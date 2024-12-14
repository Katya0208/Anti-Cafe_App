# frontend/app.py

import streamlit as st
import httpx
import asyncio

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

# async def login_user(email, password):
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.post(f"{API_URL}/login", data={
#                 "username": email,
#                 "password": password
#             })
#             if response.status_code == 200:
#                 token = response.json()["access_token"]
#                 return True, token
#             else:
#                 return False, response.json().get("detail", "Ошибка входа.")
#         except Exception as e:
#             return False, str(e)

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

import streamlit as st
import httpx
import asyncio

API_URL = "http://127.0.0.1:8000"

def admin_page():
    st.title("Страница администратора")
    menu = ["Пользователи", "Бронирования", "Сессии", "Платежи", "Ресурсы", "Резервные копии"]
    choice = st.sidebar.selectbox("Меню администратора", menu)

    if choice == "Пользователи":
        manage_users()
    # Добавьте остальные функции (Бронирования, Сессии и т.д.)

async def fetch_users():
    """Получение списка пользователей с сервера"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/admin/users", headers={
            "Authorization": f"Bearer {st.session_state['token']}"
        })
        return response.json()

async def add_user(user_data):
    """Добавление нового пользователя через сервер"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/admin/users", json=user_data, headers={
            "Authorization": f"Bearer {st.session_state['token']}"
        })
        return response.json()

def manage_users():
    st.subheader("Управление пользователями")

    # Отображение списка пользователей
    if st.button("Показать всех пользователей"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        users = loop.run_until_complete(fetch_users())
        loop.close()

        if users:
            st.dataframe(users)
        else:
            st.error("Не удалось получить список пользователей")

    # Форма для добавления пользователя
    st.write("Добавить нового пользователя")
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
                st.success(response["message"])
            else:
                st.error("Ошибка при добавлении пользователя")
        else:
            st.error("Заполните все поля!")

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