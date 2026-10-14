"""Small shared database helpers. SQL values always use bind parameters."""

from contextlib import contextmanager
import oracledb
from fastapi import HTTPException
from backend.database.connection import get_connection


@contextmanager
def database(write=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        if write:
            conn.commit()
    except HTTPException:
        if write:
            conn.rollback()
        raise
    except oracledb.IntegrityError:
        if write:
            conn.rollback()
        raise HTTPException(
            409, "Hay datos duplicados o relacionados que impiden la operación"
        )
    except Exception:
        if write:
            conn.rollback()
        raise
    finally:
        conn.close()


def rows(cur):
    names = [column[0].lower() for column in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def new_id(cur, sql, values):
    result = cur.var(oracledb.NUMBER)
    cur.execute(
        sql + " RETURNING " + values.pop("_pk") + " INTO :new_id",
        {**values, "new_id": result},
    )
    return int(result.getvalue()[0])
