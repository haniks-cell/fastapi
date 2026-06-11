## Настройка JWT-ключей

Для аутентификации с помощью JWT (алгоритм RS256) требуются приватный и публичный ключи.

1.  Создайте директорию `certs` в корне проекта, если она не существует:
    ```bash
    mkdir certs
    ```

2.  Перейдите в эту директорию:
    ```bash
    cd certs
    ```

3.  Выполните следующие команды для генерации ключей с помощью `openssl`:
    ```bash
    # Генерация приватного ключа
    openssl genrsa -out private.pem 2048

    # Извлечение публичного ключа из приватного
    openssl rsa -in private.pem -pubout -out public.pem
    ```

4. Создайте файл окружения `.env`:
    ```bash
    touch .env
    ```
5. Отредактируйте его и запишите следующее содержимое:
DB_HOST=postgres #localhost
DB_PORT=5432 #5438
DB_NAME=fastapi
DB_USER=postgres
DB_PASS=WRITE_YOUR_PASSWORD_HERE
APP_NAME=Fast Shop
STATIC_DIR=static
IMAGE_DIR=static/images
REDIS_PASSWORD=WRITE_YOUR_PASSWORD_HERE
REDIS_USER=fastapi
REDIS_USER_PASSWORD=WRITE_YOUR_PASSWORD_HERE
KAFKA_URL=kafka:29092 #localhost:9092