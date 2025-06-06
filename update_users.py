import asyncio
from sqlalchemy import select, insert
from other.database import async_session_maker
from other.models import User, UserSettings


async def update_users():
        async with async_session_maker() as session:
            stmt = select(User)
            users = (await session.execute(stmt)).all()
            await session.commit()

            for i in range(len(users)):
                stmt = insert(UserSettings).values(usr=users[i][0].tg_id)
                await session.execute(stmt)

            await session.commit()


asyncio.run(update_users())