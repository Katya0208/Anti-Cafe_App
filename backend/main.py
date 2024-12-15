from typing import List  # Убедитесь, что импортировали List
from fastapi import FastAPI, Depends, HTTPException, status
from .database import init_db, close_db
from .models import User, Token
from .schemas import UserRegister, UserLogin as UserLoginSchema
from .auth import verify_password, get_password_hash, create_access_token, oauth2_scheme
from .models import User, Token, Booking, BookingCreate, Resource, ResourceCreate
from jose import JWTError, jwt
from datetime import timedelta
import logging
import os
from datetime import datetime
from dotenv import load_dotenv  # Для загрузки переменных окружения

# Загрузка переменных окружения из .env файла
load_dotenv()

# Глобальные переменные
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ALGORITHM = "HS256"

app = FastAPI(title="Система Управления Антикафе")

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Запуск и остановка соединения с базой данных при старте и завершении приложения
@app.on_event("startup")
async def startup_event():
    await init_db(app)

@app.on_event("shutdown")
async def shutdown_event():
    await close_db(app)

@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    pool = app.state.pool
    if pool is None:
        raise HTTPException(status_code=500, detail="Пул соединений не инициализирован.")
    
    async with pool.acquire() as conn:
        # Проверка наличия пользователя с таким email
        existing_user = await conn.fetchrow("SELECT * FROM Users WHERE email = $1", user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует.")
        
        # Получение role_id для роли 'client'
        client_role = await conn.fetchrow("SELECT role_id FROM Roles WHERE role_name = 'client'")
        if not client_role:
            raise HTTPException(status_code=500, detail="Роль 'client' не найдена в базе данных.")
        role_id = client_role['role_id']
        
        hashed_pw = get_password_hash(user.password)
        
        # Вставка нового пользователя
        try:
            user_id = await conn.fetchval("""
                INSERT INTO Users (first_name, last_name, email, password_hash, role_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING user_id
            """, user.first_name, user.last_name, user.email, hashed_pw, role_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при регистрации: {e}")
        
        # Получение имени роли
        role_name = await conn.fetchval("SELECT role_name FROM Roles WHERE role_id = $1", role_id)
        
        return User(
            user_id=user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role_id=role_id,
            role_name=role_name
        )

@app.post("/login", response_model=Token)
async def login(user: UserLoginSchema):
    pool = app.state.pool
    if pool is None:
        raise HTTPException(status_code=500, detail="Пул соединений не инициализирован.")
    
    async with pool.acquire() as conn:
        db_user = await conn.fetchrow("SELECT * FROM Users WHERE email = $1", user.email)
        if not db_user:
            raise HTTPException(status_code=400, detail="Неверный email или пароль.")
        if not verify_password(user.password, db_user['password_hash']):
            raise HTTPException(status_code=400, detail="Неверный email или пароль.")
        
        # Получение имени роли
        role_name = await conn.fetchval("SELECT role_name FROM Roles WHERE role_id = $1", db_user['role_id'])
        
        # Создание JWT токена
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": db_user['email'], "role": role_name},  # Передаём role_name вместо role_id
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
@app.get("/users/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверный токен.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        role: str = payload.get("role")
        if role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    pool = app.state.pool
    if pool is None:
        raise HTTPException(status_code=500, detail="Пул соединений не инициализирован.")
    
    async with pool.acquire() as conn:
        db_user = await conn.fetchrow("SELECT * FROM Users WHERE email = $1", email)
        if db_user is None:
            raise credentials_exception
        role_name = await conn.fetchval("SELECT role_name FROM Roles WHERE role_id = $1", db_user['role_id'])
        return User(
            user_id=db_user['user_id'],
            first_name=db_user['first_name'],
            last_name=db_user['last_name'],
            email=db_user['email'],
            role_id=db_user['role_id'],
            role_name=role_name
        )

# Проверка роли администратора
def admin_required(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Доступ запрещён")
    except JWTError:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

# --- Маршруты для администраторов ---
@app.get("/admin/users", dependencies=[Depends(admin_required)], response_model=List[User])
async def get_users():
    """Получение всех пользователей"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        users = await conn.fetch("""
            SELECT u.user_id, u.first_name, u.last_name, u.email, u.role_id, r.role_name
            FROM Users u
            JOIN Roles r ON u.role_id = r.role_id
        """)
    # Преобразуем записи в модели User
    return [
        User(
            user_id=user['user_id'],
            first_name=user['first_name'],
            last_name=user['last_name'],
            email=user['email'],
            role_id=user['role_id'],
            role_name=user['role_name']
        )
        for user in users
    ]

@app.post("/admin/users", dependencies=[Depends(admin_required)])
async def add_user(user: UserRegister):
    """Добавление нового пользователя"""
    try:
        logger.info(f"Добавление нового пользователя {user.email}")
        pool = app.state.pool
        async with pool.acquire() as conn:
            # Проверка, существует ли пользователь с таким email
            existing_user = await conn.fetchrow("SELECT * FROM Users WHERE email = $1", user.email)
            if existing_user:
                raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует.")
            
            hashed_pw = get_password_hash(user.password)
            # Вставка нового пользователя с ролью 'client'
            await conn.execute("""
                INSERT INTO Users (first_name, last_name, email, password_hash, role_id)
                VALUES ($1, $2, $3, $4, (SELECT role_id FROM Roles WHERE role_name = 'client'))
            """, user.first_name, user.last_name, user.email, hashed_pw)
        return {"message": "Пользователь успешно добавлен"}
    except HTTPException as he:
        logger.error(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Ошибка при добавлении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
@app.delete("/admin/users/{user_id}", dependencies=[Depends(admin_required)])
async def delete_user(user_id: int):
    """Удаление пользователя"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM Users WHERE user_id = $1", user_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Пользователь не найден.")
    return {"message": "Пользователь удалён"}

# --- Новые маршруты для бронирований ---

# Получение всех бронирований
@app.get("/admin/bookings", dependencies=[Depends(admin_required)], response_model=List[Booking])
async def get_bookings():
    """Получение всех бронирований"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        bookings = await conn.fetch("""
            SELECT b.booking_id, b.user_id, b.resource_id, b.start_time, b.end_time, b.status
            FROM Bookings b
        """)
    # Преобразуем записи в модели Booking
    return [
        Booking(
            booking_id=booking['booking_id'],
            user_id=booking['user_id'],
            resource_id=booking['resource_id'],
            start_time=booking['start_time'],
            end_time=booking['end_time'],
            status=booking['status']
        )
        for booking in bookings
    ]

# Добавление нового бронирования
@app.post("/admin/bookings", dependencies=[Depends(admin_required)], response_model=Booking, status_code=status.HTTP_201_CREATED)
async def add_booking(booking: BookingCreate):
    """Добавление нового бронирования"""
    try:
        logger.info(f"Добавление нового бронирования для пользователя {booking.user_id}")
        pool = app.state.pool
        async with pool.acquire() as conn:
            # Проверка существования пользователя
            user = await conn.fetchrow("SELECT * FROM Users WHERE user_id = $1", booking.user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Пользователь не найден.")
            
            # Проверка существования ресурса
            resource = await conn.fetchrow("SELECT * FROM Resources WHERE resource_id = $1", booking.resource_id)
            if not resource:
                raise HTTPException(status_code=404, detail="Ресурс не найден.")
            
            # Проверка доступности ресурса на заданное время
            overlapping_booking = await conn.fetchrow("""
                SELECT * FROM Bookings
                WHERE resource_id = $1
                AND status = 'active'
                AND ($2 < end_time AND $3 > start_time)
            """, booking.resource_id, booking.start_time, booking.end_time)
            
            if overlapping_booking:
                raise HTTPException(status_code=400, detail="Ресурс уже забронирован на указанное время.")
            
            # Вставка нового бронирования
            booking_id = await conn.fetchval("""
                INSERT INTO Bookings (user_id, resource_id, start_time, end_time, status)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING booking_id
            """, booking.user_id, booking.resource_id, booking.start_time, booking.end_time, booking.status)
            
            return Booking(
                booking_id=booking_id,
                user_id=booking.user_id,
                resource_id=booking.resource_id,
                start_time=booking.start_time,
                end_time=booking.end_time,
                status=booking.status
            )
    except HTTPException as he:
        logger.error(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Ошибка при добавлении бронирования: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Удаление бронирования
@app.delete("/admin/bookings/{booking_id}", dependencies=[Depends(admin_required)])
async def delete_booking(booking_id: int):
    """Удаление бронирования"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        # Проверка существования бронирования
        booking = await conn.fetchrow("SELECT * FROM Bookings WHERE booking_id = $1", booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Бронирование не найдено.")
        
        # Удаление бронирования
        result = await conn.execute("DELETE FROM Bookings WHERE booking_id = $1", booking_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=500, detail="Ошибка при удалении бронирования.")
    return {"message": "Бронирование успешно удалено"}

@app.get("/admin/resources", response_model=List[Resource])
async def get_resources(token: str = Depends(oauth2_scheme)):
    """Получение списка ресурсов"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        resources = await conn.fetch("SELECT resource_id, name, description FROM Resources")
    return [{"resource_id": resource["resource_id"], "name": resource["name"], "description": resource["description"]} for resource in resources]



@app.post("/admin/resources", response_model=dict)
async def add_resource(resource: ResourceCreate, token: str = Depends(oauth2_scheme)):
    """Добавление нового ресурса"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO Resources (name, description)
            VALUES ($1, $2)
        """, resource.name, resource.description)
    return {"message": "Ресурс успешно добавлен"}

@app.delete("/admin/resources/{resource_id}", response_model=dict)
async def delete_resource(resource_id: int, token: str = Depends(oauth2_scheme)):
    """Удаление ресурса"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM Resources WHERE resource_id = $1", resource_id)
    return {"message": "Ресурс успешно удалён"}

@app.get("/admin/sessions", response_model=List[dict])
async def fetch_sessions(token: str = Depends(oauth2_scheme)):
    pool = app.state.pool
    async with pool.acquire() as conn:
        sessions = await conn.fetch("""
            SELECT session_id, user_id, start_time, end_time 
            FROM Sessions
        """)
    return [
        {
            "session_id": session["session_id"],
            "user_id": session["user_id"],
            "start_time": session["start_time"],
            "end_time": session["end_time"],
        }
        for session in sessions
    ]

@app.post("/admin/sessions", dependencies=[Depends(admin_required)])
async def add_session(session: dict):
    """Добавление новой сессии"""
    pool = app.state.pool
    try:
        # Конвертация времени из строки в datetime
        start_time = datetime.fromisoformat(session["start_time"])
        end_time = datetime.fromisoformat(session["end_time"])

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO Sessions (user_id, start_time, end_time)
                VALUES ($1, $2, $3)
            """, session["user_id"], start_time, end_time)

        return {"message": "Сессия успешно добавлена"}
    except KeyError as e:
        return {"error": f"Отсутствует обязательное поле: {e}"}
    except ValueError as e:
        return {"error": f"Ошибка формата времени: {e}"}
    except Exception as e:
        return {"error": f"Ошибка сервера: {str(e)}"}

@app.delete("/admin/sessions/{session_id}", response_model=dict)
async def delete_session(session_id: int, token: str = Depends(oauth2_scheme)):
    pool = app.state.pool
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM Sessions WHERE session_id = $1", session_id)
        if result == "DELETE 1":
            return {"message": "Сессия успешно удалена"}
        else:
            raise HTTPException(status_code=404, detail="Сессия не найдена")

@app.get("/admin/payments", dependencies=[Depends(admin_required)])
async def get_payments():
    pool = app.state.pool
    async with pool.acquire() as conn:
        payments = await conn.fetch("SELECT payment_id, user_id, amount FROM Payments")
    return payments

@app.post("/admin/payments", dependencies=[Depends(admin_required)])
async def add_payment(payment: dict):
    pool = app.state.pool
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO Payments (user_id, amount)
            VALUES ($1, $2)
        """, payment["user_id"], payment["amount"])
    return {"message": "Платеж успешно добавлен"}

@app.delete("/admin/payments/{payment_id}", dependencies=[Depends(admin_required)])
async def delete_payment(payment_id: int):
    pool = app.state.pool
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM Payments WHERE payment_id = $1", payment_id)
    return {"message": "Платеж успешно удалён"}