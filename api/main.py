from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from pydantic import BaseModel

import datetime

from sqlalchemy import func,inspect
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

from fastapi import FastAPI
from sqladmin import Admin, ModelView


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

    def __str__(self) -> str:
        return self.data

  
#https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#sqlalchemy.orm.joinedload
class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    data:Mapped[str] = mapped_column(String)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    # category: Mapped["Category"] = relationship(Category,lazy="joined")
    # category: Mapped["Category"] = relationship(Category,lazy="selectin")
    category: Mapped["Category"] = relationship(Category)


class User(SQLAlchemyBaseUserTableUUID, Base):
    first_name: Mapped[str] 

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

async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)

import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    first_name: str


class UserCreate(schemas.BaseUserCreate):
    first_name: str


class UserUpdate(schemas.BaseUserUpdate):
    first_name: str


import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase



SECRET = "SECRET"


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)

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
    
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}