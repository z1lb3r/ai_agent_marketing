# backend/app/scripts/generate_telegram_session.py
import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession

# Добавляем путь к приложению в PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings

async def generate_session():
    # Создаем клиент Telegram
    client = TelegramClient(
        StringSession(), 
        settings.TELEGRAM_API_ID, 
        settings.TELEGRAM_API_HASH
    )
    
    # Запускаем клиент
    await client.connect()
    
    # Запрашиваем номер телефона
    phone = input("Please enter your phone number (with country code, e.g. +12345678901): ")
    
    # Отправляем запрос на код подтверждения
    await client.send_code_request(phone)
    
    # Запрашиваем код подтверждения
    code = input("Please enter the code you received: ")
    
    # Пытаемся войти с полученным кодом
    try:
        await client.sign_in(phone, code)
    except Exception as e:
        # Если это двухфакторная аутентификация, запрашиваем пароль
        if "2FA" in str(e):
            password = input("Please enter your 2FA password: ")
            await client.sign_in(password=password)
    
    # Получаем строку сессии
    session_string = client.session.save()
    
    # Закрываем клиент
    await client.disconnect()
    
    # Выводим полученную строку
    print("\nYour session string (save this somewhere safe and add to .env file):")
    print(session_string)
    
    # Инструкции для использования
    print("\nAdd this to your .env file:")
    print(f"TELEGRAM_SESSION_STRING={session_string}")

# Запускаем функцию
if __name__ == "__main__":
    asyncio.run(generate_session())