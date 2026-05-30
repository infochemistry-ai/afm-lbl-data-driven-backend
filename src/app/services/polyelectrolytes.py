import json
from importlib import resources
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import Polyelectrolyte


def load_catalog() -> list[dict[str, Any]]:
    with resources.files("app.data").joinpath("polyelectrolytes.json").open("r", encoding="utf-8") as f:
        return json.load(f)


CATALOG_IDS = tuple(entry["id"] for entry in load_catalog())


def seed_catalog(session: Session) -> int:
    entries = load_catalog()
    stmt = insert(Polyelectrolyte).values(entries)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={c.name: stmt.excluded[c.name] for c in Polyelectrolyte.__table__.columns if c.name != "id"},
    )
    session.execute(stmt)
    session.commit()
    return len(entries)


def get_all(session: Session) -> list[Polyelectrolyte]:
    return list(session.scalars(select(Polyelectrolyte).order_by(Polyelectrolyte.id)))
