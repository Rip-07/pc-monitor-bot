FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Команда по умолчанию
CMD ["python", "application.py"]