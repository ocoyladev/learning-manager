import os
import secrets
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


@contextmanager
def isolated_session_factory(
    database_url: str,
    migration_sql: str,
    schema: str | None = None,
) -> Iterator[Callable[[], Session]]:
    """Create a schema-bound factory and always remove its schema."""
    isolated_schema = schema or f"test_{secrets.token_hex(8)}"
    engine = create_engine(
        database_url,
        connect_args={"options": f"-csearch_path={isolated_schema}"},
    )
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{isolated_schema}"'))
        with engine.begin() as connection:
            connection.exec_driver_sql(migration_sql)
        yield sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{isolated_schema}" CASCADE'))
        engine.dispose()


@pytest.fixture
def isolated_session_factory_factory() -> Callable[..., object]:
    return isolated_session_factory


@pytest.fixture
def session_factory() -> Iterator[Callable[[], Session]]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("requires PostgreSQL (set DATABASE_URL)")

    migration_path = (
        Path(__file__).parents[2]
        / "learning_manager"
        / "persistence"
        / "migrations"
        / "001_initial.sql"
    )
    migration_sql = migration_path.read_text(encoding="utf-8")
    with isolated_session_factory(database_url, migration_sql) as factory:
        yield factory
