-- init_db.sql

-- Таблица ролей
CREATE TABLE Roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);


-- Таблица пользователей
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT REFERENCES Roles(role_id)
);

-- Вставка стандартных ролей
INSERT INTO Roles (role_name, description) VALUES
('admin', 'Администратор системы'),
('staff', 'Сотрудник антикафе'),
('client', 'Клиент антикафе');


-- Создание новой таблицы Payments с изменённой структурой
CREATE TABLE Payments (
    payment_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0)
);

CREATE TABLE Sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL
);

-- Таблица ресурсов
CREATE TABLE Resources (
    resource_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50),
    description TEXT
);

-- Таблица бронирований
CREATE TABLE Bookings (
    booking_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    resource_id INT REFERENCES Resources(resource_id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'pending'
);

-- Таблица резервных копий
CREATE TABLE Backups (
    backup_id SERIAL PRIMARY KEY,
    backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(255) NOT NULL
);