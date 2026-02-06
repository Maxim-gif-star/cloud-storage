# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# Создаем приложение
app = FastAPI(title="Мой первый API")

# Модель данных (что мы будем принимать/отдавать)
class User(BaseModel):
    name: str
    age: int
    email: Optional[str] = None

# База данных "в памяти"
fake_db = []

# Маршрут 1: Главная страница
@app.get("/")  # GET запрос на корневой URL
def read_root():
    return {"message": "Привет! Это мой API"}

# Маршрут 2: Получить всех пользователей
@app.get("/users")
def get_users():
    return {"users": fake_db}

# Маршрут 3: Получить одного пользователя по ID
@app.get("/users/{user_id}")  # {user_id} - путь параметр
def get_user(user_id: int):
    if 0 <= user_id < len(fake_db):
        return fake_db[user_id]
    return {"error": "Пользователь не найден"}

# Маршрут 4: Создать нового пользователя
@app.post("/users")
def create_user(user: User):  # User автоматически парсится из JSON
    fake_db.append(user)
    return {"message": "Пользователь создан", "user": user}

# Маршрут 5: Обновить пользователя
@app.put("/users/{user_id}")
def update_user(user_id: int, updated_user: User):
    if 0 <= user_id < len(fake_db):
        fake_db[user_id] = updated_user
        return {"message": "Пользователь обновлен"}
    return {"error": "Пользователь не найден"}

# Маршрут 6: Удалить пользователя
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    if 0 <= user_id < len(fake_db):
        deleted_user = fake_db.pop(user_id)
        return {"message": "Пользователь удален", "user": deleted_user}
    return {"error": "Пользователь не найден"}