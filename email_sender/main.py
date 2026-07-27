import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib, json
from jinja2 import Environment, FileSystemLoader

from faststream import FastStream
from faststream.kafka import KafkaBroker

from config import settings, global_settings
from schemas import KafkaInput

# Настройка Jinja2 для загрузки шаблонов из папки 'templates'
env = Environment(loader=FileSystemLoader('templates'))

broker = KafkaBroker(global_settings.KAFKA_URL)
app = FastStream(broker)

async def send_email(recipient_email: str, link: str):
    """
    Асинхронно отправляет email с использованием шаблона и настроек.

    :param recipient_email: Email адрес получателя.
    :param link: Ссылка для вставки в шаблон.
    """
    try:
        # Загружаем шаблон письма
        template = env.get_template('registration.html')
        # Рендерим шаблон с переданной ссылкой
        html_content = template.render(link=link)

        # Создаем объект сообщения
        message = MIMEMultipart()
        message["From"] = settings.GMAIL_LOGIN
        message["To"] = recipient_email
        message["Subject"] = "Registration on site.com"
        message.attach(MIMEText(html_content, "html"))

        # Отправляем письмо
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            username=settings.GMAIL_LOGIN,
            password=settings.GMAIL_PASSWORD,
            use_tls=True,
        )
        print(f"Email successfully sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}. Error: {e}")


@broker.subscriber("magiclinkEmail", group_id="send_email_group", auto_offset_reset="earliest")
async def handle_magiclink(payload_str: str) -> None:
    payload = KafkaInput.model_validate_json(payload_str)
    await send_email(payload.email, payload.link)


# Пример использования функции
if __name__ == "__main__":
    # confirmation_link = f'{global_settings.APPLICATION_URL}api/auth/email_confirm/?token=some_unique_token'
    # asyncio.run(send_email(settings.GMAIL_LOGIN, confirmation_link))
    asyncio.run(app.run())