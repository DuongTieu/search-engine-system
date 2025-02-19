import uuid
from datetime import datetime, timedelta
from typing import Any

from pydantic import UUID4
from sqlalchemy import insert, select
from src.auth import utils
from src.auth.config import auth_config
from src.auth.schemas import AuthUser
from src.database import auth_user, execute, fetch_all, fetch_one, refresh_tokens
from src.utils import LOGGER


async def init_user(email):
    insert_query = auth_user.insert().values(
        email=email, created_at=datetime.utcnow(), is_admin=True
    )

    user = await get_user_by_email(email=email)

    if user:
        LOGGER.info("Admin user is exists!")
    else:
        LOGGER.info("Create Admin user...")
        await execute(insert_query)
        LOGGER.info("Create successfully!")


async def create_user(user: AuthUser) -> dict[str, Any] | None:
    insert_query = (
        insert(auth_user)
        .values(
            {
                "email": user.email,
                "username": user.username,
                "image": user.image,
                "created_at": datetime.utcnow(),
            }
        )
        .returning(auth_user)
    )

    return await fetch_one(insert_query)


async def get_all_user():
    select_query = select(auth_user)

    # Execute the query and fetch all results
    return await fetch_all(select_query)


async def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    select_query = select(auth_user).where(auth_user.c.id == user_id)

    return await fetch_one(select_query)


async def get_user_by_email(email: str) -> dict[str, Any] | None:
    select_query = select(auth_user).where(auth_user.c.email == email)

    return await fetch_one(select_query)


async def create_refresh_token(
    *, user_id: int, refresh_token: str | None = None
) -> str:
    if not refresh_token:
        refresh_token = utils.generate_random_alphanum(64)

    insert_query = refresh_tokens.insert().values(
        uuid=uuid.uuid4(),
        refresh_token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(seconds=auth_config.REFRESH_TOKEN_EXP),
        user_id=user_id,
    )
    await execute(insert_query)

    return refresh_token


async def get_refresh_token(refresh_token: str) -> dict[str, Any] | None:
    select_query = refresh_tokens.select().where(
        refresh_tokens.c.refresh_token == refresh_token
    )

    return await fetch_one(select_query)


async def expire_refresh_token(refresh_token_uuid: UUID4) -> None:
    update_query = (
        refresh_tokens.update()
        .values(expires_at=datetime.utcnow() - timedelta(days=1))
        .where(refresh_tokens.c.uuid == refresh_token_uuid)
    )

    await execute(update_query)


async def authenticate_user(auth_data: AuthUser) -> dict[str, Any]:
    # Verify token google

    # Check email exists
    user = await get_user_by_email(auth_data.email)
    if not user:
        # Create new user
        LOGGER.info("Create new user")
        user = await create_user(user=auth_data)
    else:
        LOGGER.info("User is exists!")

    return user
