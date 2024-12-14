# backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from .database import init_db, close_db
from .models import User, Token
from .schemas import UserRegister, UserLogin as UserLoginSchema
from .auth import verify_password, get_password_hash, create_access_token, oauth2_scheme
from jose import JWTError, jwt
from datetime import timedelta
import logging
import os

app = FastAPI(title="Система Управления Антикафе")

# Настройка логирования
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(name)

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
        #logger.error("Пул соединений не инициализирован.")
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
            #logger.error(f"Ошибка при регистрации: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка при регистрации: {e}")
        
        # Получение имени роли
        role_name = await conn.fetchval("SELECT role_name FROM Roles WHERE role_id = $1", role_id)
        
        #logger.info(f"Пользователь {user.email} успешно зарегистрирован.")
        
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
        #logger.error("Пул соединений не инициализирован.")
        raise HTTPException(status_code=500, detail="Пул соединений не инициализирован.")
    
    async with pool.acquire() as conn:
        db_user = await conn.fetchrow("SELECT * FROM Users WHERE email = $1", user.email)
        if not db_user:
            raise HTTPException(status_code=400, detail="Неверный email или пароль.")
        if not verify_password(user.password, db_user['password_hash']):
            raise HTTPException(status_code=400, detail="Неверный email или пароль.")
        
        # Создание JWT токена
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": db_user['email'], "role": db_user['role_id']},
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
@app.get("/users/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")  # Важно: Используйте безопасный секретный ключ и храните его в переменных окружения
    ALGORITHM = "HS256"
    
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
    except JWTError:
        raise credentials_exception
    
    pool = app.state.pool
    if pool is None:
        #logger.error("Пул соединений не инициализирован.")
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
    # Логика проверки токена и роли пользователя
    # Реализуйте проверку роли на основе данных из JWT
    # Пример: role можно декодировать из токена
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    role = decoded_token.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

# --- Маршруты для администраторов ---
@app.get("/admin/users", dependencies=[Depends(admin_required)])
async def get_users():
    """Получение всех пользователей"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT user_id, first_name, last_name, email, role_id FROM Users")
    return users

@app.post("/admin/users", dependencies=[Depends(admin_required)])
async def add_user(user: UserRegister):
    """Добавление нового пользователя"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        hashed_pw = get_password_hash(user.password)
        await conn.execute("""
            INSERT INTO Users (first_name, last_name, email, password_hash, role_id)
            VALUES ($1, $2, $3, $4, (SELECT role_id FROM Roles WHERE role_name = 'client'))
        """, user.first_name, user.last_name, user.email, hashed_pw)
    return {"message": "Пользователь успешно добавлен"}

@app.delete("/admin/users/{user_id}", dependencies=[Depends(admin_required)])
async def delete_user(user_id: int):
    """Удаление пользователя"""
    pool = app.state.pool
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM Users WHERE user_id = $1", user_id)
    return {"message": "Пользователь удалён"}