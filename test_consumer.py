import asyncio
from pydantic import BaseModel, Field
from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

# 1. Описываем модель данных (наша схема JSON)
class UserAction(BaseModel):
    user_id: int
    status: str
    payload: str

# 2. Настраиваем брокер (используем наш рабочий localhost:9092)
broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

# 3. Подписываемся на топик
@broker.subscriber("my_test_topic", group_id="my_stable_service", 
                   auto_offset_reset="earliest")
async def handle_user_action(msg: UserAction, logger: Logger):
    # FastStream САМ сделал json.loads() и валидацию!
    # Здесь msg — это уже объект класса UserAction, а не словарь.
    
    print(f"Обработка пользователя {msg.user_id}")
    
    # if msg.action == "purchase":
    #     total = msg.items_count * 100
    #     print(f"💰 Пользователь купил товары на сумму: {total}")
    
    print(f"Данные из Pydantic: {msg.model_dump()}")

async def main():
    # Запускаем приложение
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())