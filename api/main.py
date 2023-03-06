from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


from pydantic import BaseModel

import datetime

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
from typing import Optional, List
from sqlalchemy.orm import mapped_column
from sqlalchemy import (
    ForeignKey,

)
from sqlalchemy.orm import joinedload, lazyload
from sqlalchemy.orm import relationship

app = FastAPI()


   
engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    
)



Base = declarative_base()

class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[Optional[str]]
    create_date: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )

  
#https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#sqlalchemy.orm.joinedload
class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    data:Mapped[str]
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    # category: Mapped["Category"] = relationship(Category,lazy="joined")
    # category: Mapped["Category"] = relationship(Category,lazy="selectin")
    category: Mapped["Category"] = relationship(Category)


    

@app.on_event("startup")
async def startup() -> None:
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



async def get_session() :
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.close()

@app.on_event("shutdown")
async def shutdown() -> None:
    pass




class CategoryCreate(BaseModel):
    id:int
    data:str
    
    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    id:Optional[int] = None
    data:str
    category_id:int

class ProductInfo(BaseModel):
    id:int
    data:str
    category:CategoryCreate

    class Config:
        orm_mode = True

@app.post('/category/')
async def person_post(data:CategoryCreate,session: AsyncSession = Depends(get_session)):
    
    async with session as ses:
        person = Category(**data.dict())
        ses.add(person)
        await ses.commit()

    return person

@app.get('/category/',response_model=List[CategoryCreate])
async def get_all(session: AsyncSession = Depends(get_session)):
    async with session as ses:
        query = await ses.execute(select(Category))
        result = query.scalars().all()
    return result

@app.post('/product/')
async def person_post(data:ProductCreate,session: AsyncSession = Depends(get_session)):
    
    async with session as ses:
        person = Product(**data.dict())
        ses.add(person)
        await ses.commit()

    return person


@app.get('/product/',response_model=List[ProductInfo])
async def get_all(session: AsyncSession = Depends(get_session)):
    async with session as ses:
        query = await ses.execute(select(Product).options(joinedload(Product.category, innerjoin=True)))
        # query = await ses.execute(select(Product).options(joinedload("*")))
        # query = await ses.execute(select(Product))
        result = query.scalars().all()
        return result