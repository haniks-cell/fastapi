import json
from aiokafka import AIOKafkaProducer
from typing import Optional
from config import settings

class KafkaProducerManager:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_URL,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_message(self, topic: str, value: dict):
        if self.producer:
            await self.producer.send(topic, value=value)

# Создаем глобальный экземпляр
kafka_manager = KafkaProducerManager()