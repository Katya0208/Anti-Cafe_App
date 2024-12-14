import bcrypt
import psycopg2

# Настройки подключения к базе данных
DATABASE_CONFIG = {
    'dbname': 'anticafe',
    'user': 'katushka',
    'password': 'rfneirf2004',
    'host': '127.0.0.1',
    'port': 5432
}

def hash_password(password: str) -> str:
    """Генерация соли и хеширование пароля."""
    salt = bcrypt.gensalt()  # Генерация уникальной соли
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  # Сохраняем в виде строки

def add_admin(first_name: str, last_name: str, email: str, password: str):
    """Добавление администратора в базу данных."""
    hashed_pw = hash_password(password)
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(**DATABASE_CONFIG)
        with conn.cursor() as cur:
            # Получение role_id для роли 'admin'
            cur.execute("SELECT role_id FROM Roles WHERE role_name = 'admin'")
            role_id = cur.fetchone()
            if not role_id:
                raise Exception("Роль 'admin' не найдена в базе данных.")
            role_id = role_id[0]

            # Вставка нового администратора
            cur.execute("""
                INSERT INTO Users (first_name, last_name, email, password_hash, role_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, email, hashed_pw, role_id))
            conn.commit()
            print(f"Администратор {email} успешно добавлен!")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

# Использование функции
if __name__ == "__main__":
    first_name = input("Введите имя администратора: ")
    last_name = input("Введите фамилию администратора: ")
    email = input("Введите email администратора: ")
    password = input("Введите пароль администратора: ")
    add_admin(first_name, last_name, email, password)