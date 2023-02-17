from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from pydantic import BaseModel

import datetime
from typing import List
from typing import Optional


from sqlalchemy import func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import FastAPI, Depends

app = FastAPI()


   
engine = create_async_engine(
    "postgresql+asyncpg://postgres:postgres@data_b/postgres",
    echo=True,
)



Base = declarative_base()

class A(Base):
    __tablename__ = "a"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[Optional[str]]
    create_date: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )

  

class AInfo(BaseModel):
    id:int
    data:str

    class Config:
        orm_mode = True
    

@app.on_event("startup")
async def startup() -> None:
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() :
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,  
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.close()

@app.on_event("shutdown")
async def shutdown() -> None:
    pass

import time
@app.get('/test')
async def test():
    for i in range(1,1000000):
        print(i)
    return ''

@app.get('/person/{name}')
async def person_get(name,session: AsyncSession = Depends(get_session)):
    async with session as ses:
        query = await ses.execute(select(A).where(A.data == name))
        result = query.fetchall()
    return result


@app.get('/person',response_model=List[AInfo])
async def get_all(session: AsyncSession = Depends(get_session)):
    async with session as ses:
        query = await ses.execute(select(A))
        result = query.scalars().all()
        return result


@app.post('/person/')
async def person_post(name:str,session: AsyncSession = Depends(get_session)):
    

    async with session as ses:
        person = A(data=name)
        ses.add(person)
        await ses.commit()

    return person