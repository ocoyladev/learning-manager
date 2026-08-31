import os
import secrets
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def session_factory() -> Iterator[Callable[[], Session]]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("requires PostgreSQL (set DATABASE_URL)")

    schema = f"test_{secrets.token_hex(8)}"
    engine = create_engine(
        database_url,
        connect_args={"options": f"-csearch_path={schema}"},
    )
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    with engine.begin() as connection:
        connection.execute(text(f'SET search_path TO "{schema}"'))

    migration_path = (
        Path(__file__).parents[2]
        / "learning_manager"
        / "persistence"
        / "migrations"
        / "001_initial.sql"
    )
    migration_sql = migration_path.read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.exec_driver_sql(migration_sql)
    factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    try:
        yield factory
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()
