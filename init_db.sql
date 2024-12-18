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

-- Таблица для логирования сессий
CREATE TABLE session_logs (
    log_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL,
    user_id INT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('start', 'end')),
    event_time TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Таблица для логирования бронирований
CREATE TABLE booking_logs (
    log_id SERIAL PRIMARY KEY,
    booking_id INT NOT NULL,
    user_id INT NOT NULL,
    resource_id INT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('completed')),
    event_time TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Функция для логирования начала сессии
CREATE OR REPLACE FUNCTION log_session_start()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO session_logs (session_id, user_id, event_type, event_time)
    VALUES (NEW.session_id, NEW.user_id, 'start', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Функция для логирования конца сессии
CREATE OR REPLACE FUNCTION log_session_end()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_time IS NOT NULL AND OLD.end_time IS NULL THEN
        INSERT INTO session_logs (session_id, user_id, event_type, event_time)
        VALUES (NEW.session_id, NEW.user_id, 'end', NOW());
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер на INSERT для логирования начала сессии
CREATE TRIGGER trg_session_start
AFTER INSERT ON sessions
FOR EACH ROW
EXECUTE FUNCTION log_session_start();

-- Триггер на UPDATE для логирования окончания сессии
CREATE TRIGGER trg_session_end
AFTER UPDATE ON sessions
FOR EACH ROW
WHEN (OLD.end_time IS NULL AND NEW.end_time IS NOT NULL)
EXECUTE FUNCTION log_session_end();

CREATE TRIGGER trg_booking_completed
AFTER UPDATE ON bookings
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM 'completed' AND NEW.status = 'completed')
EXECUTE FUNCTION log_booking_completed();

