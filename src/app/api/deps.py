from collections.abc import Iterator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session


def db() -> Iterator[Session]:
    yield from get_session()
