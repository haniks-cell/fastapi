from main import create_admin
from database import create_db
import asyncio

async def start():
    await create_db()
    await create_admin()

asyncio.run(start())