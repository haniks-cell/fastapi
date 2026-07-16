# 1. Базовый образ
FROM python:3.12.8-slim

# 2. Установка рабочей директории внутри контейнера
WORKDIR /app

# 3. Копирование файла с зависимостями
#    Убедитесь, что файл requirements.txt сохранен в кодировке UTF-8
COPY ./fastapi/requirements.txt .

# 4. Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt 

# 5. Копирование всего кода приложения в рабочую директорию
COPY ./fastapi/ .

# 6. Открытие порта, на котором будет работать приложение
EXPOSE 8000

# 7. Команда для запуска приложения
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
