FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей для кэширования
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта
COPY . .

# Команда запуска
CMD ["python", "aiogram_bot.py"]