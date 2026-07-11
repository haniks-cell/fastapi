# Telegram MagicLink Bot

Бот для Telegram на базе `aiogram` с прослушиванием Kafka topic `magiclink`.

## Установка

```bash
cd aiogram
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Настройка

Создайте файл `.env`:

```env
BOT_TOKEN=ваш_токен_от_BotFather
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
PROXY_URL=http://127.0.0.1:10808
```

## Запуск

```bash
python aiogram_bot.py
```

## Формат Kafka сообщения

Topic: `magiclink`

```json
{
  "email": "123456789",
  "link": "https://example.com"
}
```

- `email` — Telegram ID пользователя
- `link` — ссылка для отправки

## Команды

- `/start` — приветствие и отображение вашего Telegram ID