from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import (
    backref,
    declarative_base,
    relationship,
    selectinload,
    sessionmaker,
)
from sqlalchemy.sql import functions
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()
mapper_args = {"eager_defaults": True}


class ThankModel(Base):
    __tablename__ = "thanks"
    __table_args__ = {"comment": "Represents a 'thank' given from one user to another"}
    id = Column(Integer, primary_key=True)
    guild_id = Column(
        BigInteger,
        ForeignKey("guilds.id"),
        doc="Guild in which the user was thanked",
    )
    guild = relationship("GuildModel", foreign_keys=[guild_id])
    thanker_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        doc="The member who sent the thanks",
    )
    thanker = relationship(
        "UserModel",
        # back_populates="sent_thanks",
        foreign_keys=[thanker_id],
        backref="sent_thanks",
    )
    thanked_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        doc="The member who was thanked",
    )
    thanked = relationship(
        "UserModel",
        # back_populates="thanks",
        foreign_keys=[thanked_id],
        backref="thanks",
    )
    time = Column(DateTime, server_default=functions.now())
    comment = Column(String(100))
    __mapper_args__ = mapper_args


class GuildModel(Base):
    __tablename__ = "guilds"
    __table_args__ = {"comment": "Represents a discord guild's settings"}
    id = Column(BigInteger, primary_key=True, comment="Discord ID of the guild")
    # all_thanks: fields.ForeignKeyRelation[ThankModel]
    prefix = Column(
        String(10), server_default=".", comment="Custom prefix of the guild"
    )
    all_thanks = relationship("ThankModel", back_populates="guild")
    __mapper_args__ = mapper_args


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "Represents all users"}
    id = Column(BigInteger, primary_key=True, comment="Discord ID of the user")
    # External references
    github_oauth_token = Column(
        String(50), nullable=True, comment="Github OAuth2 access token of the user"
    )
    stackoverflow_oauth_token = Column(
        String(50),
        nullable=True,
        comment="Stackoverflow OAuth2 access token of the user",
    )
    joke_submissions = relationship("JokeModel", back_populates="creator")
    # sent_thanks = relationship(
    # "ThankModel",
    # backref="thanker",
    # back_populates="thanker",
    # )
    # thanks = relationship(
    # "ThankModel",
    # backref="thanked",
    # back_populates="thanked",
    # )
    __mapper_args__ = mapper_args


class JokeModel(Base):
    __tablename__ = "jokes"
    __table_args__ = {"comment": "User submitted jokes being collected"}
    id = Column(Integer, primary_key=True, comment="Joke ID")

    setup = Column(String(150), nullable=False, comment="Joke setup")
    end = Column(String(150), nullable=False, comment="Joke end")
    tags = Column(JSON, server_default="[]", comment="List of tags")

    accepted = Column(
        Boolean, default=False, comment="Whether the joke has been accepted in"
    )

    creator_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        doc="User who submitted this Joke",
    )
    creator = relationship("UserModel", back_populates="joke_submissions")
    __mapper_args__ = mapper_args


async def main():
    from sqlalchemy import select

    engine = create_async_engine(
        "postgresql+asyncpg://falsedev@localhost:5432/discord-forms", echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        async with session.begin():
            session.add(GuildModel(id=1))
            session.add(UserModel(id=1))
            session.add(
                JokeModel(id=1, creator_id=1, setup="Joke setup", end="Joke end")
            )
        global guilds, users, jokes
        guilds = await session.execute(select(GuildModel))
        users = await session.execute(
            select(UserModel).options(
                selectinload(
                    UserModel.joke_submissions,
                ),
                selectinload(UserModel.thanks),
                selectinload(UserModel.sent_thanks),
            )
        )
        jokes = await session.execute(select(JokeModel))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
