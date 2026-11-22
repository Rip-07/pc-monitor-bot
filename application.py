import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Optional

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', 'BOT_TOKEN')
API_URL = os.getenv('API_URL', 'http://localhost:5000')
API_KEY = os.getenv('API_KEY', 'API_KEY')
CHAT_ID = os.getenv('CHAT_ID', 'CHAT_ID')
AUTHORIZED_USER_ID = os.getenv('AUTHORIZED_USER_ID', 'USER_ID')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
# Список ID компьютеров через запятую, например: main_pc,laptop
COMPUTERS = [c.strip() for c in os.getenv('COMPUTERS', 'main_pc').split(',') if c.strip()]

# Словарь для хранения последнего статуса каждого компьютера
last_status: Dict[str, Optional[str]] = {}


def check_authorization(func):
    """Декоратор для проверки авторизации пользователя"""
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if user_id != AUTHORIZED_USER_ID:
            logger.warning(f"Неавторизованная попытка доступа от пользователя {user_id}")
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        return await func(self, update, context)
    return wrapper


class ComputerMonitor:
    def __init__(self, bot_token: str, api_url: str, api_key: str):
        self.bot_token = bot_token
        self.api_url = api_url
        self.api_key = api_key
        self.application = Application.builder().token(bot_token).build()
        
    def get_computer_status(self, computer_id: str) -> Dict:
        """Получает статус компьютера через API"""
        try:
            headers = {'X-API-Key': self.api_key}
            response = requests.get(
                f"{self.api_url}/api/status/{computer_id}", 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return {'error': f'API error: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Ошибка сети: {e}")
            return {'error': f'Network error: {str(e)}'}
    
    async def check_and_notify(self, context: ContextTypes.DEFAULT_TYPE):
        """Проверяет статус всех компьютеров и отправляет уведомления при изменениях"""
        computers = COMPUTERS
        
        for computer_id in computers:
            try:
                status_data = self.get_computer_status(computer_id)
                
                if 'error' in status_data:
                    logger.error(f"Ошибка при получении статуса {computer_id}: {status_data['error']}")
                    continue
                
                current_status = status_data.get('status')
                computer_name = status_data.get('name', computer_id)
                response_time = status_data.get('response_time')
                
                # Проверяем, изменился ли статус
                if computer_id not in last_status:
                    # Первая проверка - сохраняем статус без уведомления
                    last_status[computer_id] = current_status
                    logger.info(f"Начальный статус {computer_name}: {current_status}")
                elif last_status[computer_id] != current_status:
                    # Статус изменился - отправляем уведомление
                    old_status = last_status[computer_id]
                    last_status[computer_id] = current_status
                    
                    # Формируем сообщение
                    timestamp = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
                    
                    if current_status == 'online':
                        status_emoji = "🟢"
                        status_text = "ОНЛАЙН"
                        extra_info = f" (время отклика: {response_time:.2f}мс)" if response_time else ""
                    elif current_status == 'offline':
                        status_emoji = "🔴"
                        status_text = "ОФЛАЙН"
                        extra_info = ""
                    else:
                        status_emoji = "⚠️"
                        status_text = f"ОШИБКА ({current_status})"
                        extra_info = ""
                    
                    message = (
                        f"{status_emoji} <b>Изменение статуса компьютера</b>\n\n"
                        f"💻 <b>Компьютер:</b> {computer_name}\n"
                        f"📊 <b>Статус:</b> {old_status.upper()} → {status_text}\n"
                        f"🕒 <b>Время:</b> {timestamp}{extra_info}"
                    )
                    
                    await context.bot.send_message(
                        chat_id=CHAT_ID, 
                        text=message, 
                        parse_mode='HTML'
                    )
                    
                    logger.info(f"Отправлено уведомление: {computer_name} {old_status} → {current_status}")
                    
            except Exception as e:
                logger.error(f"Ошибка при проверке {computer_id}: {e}")

    @check_authorization
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "🤖 Бот мониторинга компьютеров запущен!\n\n"
            "Доступные команды:\n"
            "/start - показать это сообщение\n"
            "/status - проверить текущий статус всех компьютеров\n"
            "/info - информация о боте"
        )

    @check_authorization
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        computers = COMPUTERS
        message_parts = ["📊 <b>Текущий статус компьютеров:</b>\n"]
        
        for computer_id in computers:
            status_data = self.get_computer_status(computer_id)
            
            if 'error' in status_data:
                message_parts.append(f"❌ {computer_id}: Ошибка получения данных")
                continue
            
            computer_name = status_data.get('name', computer_id)
            current_status = status_data.get('status')
            response_time = status_data.get('response_time')
            
            if current_status == 'online':
                status_emoji = "🟢"
                extra_info = f" ({response_time:.2f}мс)" if response_time else ""
            elif current_status == 'offline':
                status_emoji = "🔴"
                extra_info = ""
            else:
                status_emoji = "⚠️"
                extra_info = f" ({current_status})"
            
            message_parts.append(
                f"{status_emoji} <b>{computer_name}:</b> {current_status.upper()}{extra_info}"
            )
        
        await update.message.reply_text(
            "\n".join(message_parts), 
            parse_mode='HTML'
        )

    @check_authorization
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /info"""
        await update.message.reply_text(
            "ℹ️ <b>Информация о боте</b>\n\n"
            f"🔄 Интервал проверки: {CHECK_INTERVAL} секунд\n"
            f"🌐 API URL: {self.api_url}\n"
            f"📱 Chat ID: {CHAT_ID}\n"
            f"👤 Авторизованный пользователь: {AUTHORIZED_USER_ID}\n\n"
            "Бот автоматически отслеживает изменения статуса компьютеров "
            "и отправляет уведомления при переключении между онлайн/офлайн.",
            parse_mode='HTML'
        )

    def run_bot(self):
        """Запуск бота"""
        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("info", self.info_command))

        # Запускаем задачу мониторинга
        job_queue = self.application.job_queue
        if job_queue is None:
            raise RuntimeError(
                'JobQueue is not available. Install dependency: python-telegram-bot[job-queue]'
            )

        job_queue.run_repeating(
            self.check_and_notify,
            interval=CHECK_INTERVAL,
            first=5
        )

        logger.info("🤖 Telegram бот запущен...")
        logger.info(f"🔄 Интервал мониторинга: {CHECK_INTERVAL} секунд")
        logger.info(f"👤 Авторизованный пользователь: {AUTHORIZED_USER_ID}")

        # run_polling сам управляет asyncio event loop
        self.application.run_polling(drop_pending_updates=True)


def main():
    # Проверяем наличие необходимых переменных окружения
    if BOT_TOKEN in ('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE', ''):
        logger.error("❌ Необходимо установить BOT_TOKEN в переменных окружения!")
        return

    if API_KEY in ('API_KEY', 'YOUR_API_KEY_HERE', ''):
        logger.error("❌ Необходимо установить API_KEY в переменных окружения!")
        return

    if CHAT_ID in ('CHAT_ID', 'YOUR_CHAT_ID_HERE', ''):
        logger.error("❌ Необходимо установить CHAT_ID в переменных окружения!")
        return

    if AUTHORIZED_USER_ID in ('USER_ID', 'YOUR_USER_ID_HERE', ''):
        logger.error("❌ Необходимо установить AUTHORIZED_USER_ID в переменных окружения!")
        return

    # Создаем и запускаем бота
    monitor = ComputerMonitor(BOT_TOKEN, API_URL, API_KEY)
    monitor.run_bot()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")
