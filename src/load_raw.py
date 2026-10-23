import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

from logger_config import get_logger

logger = get_logger("food_price_watch.load")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

EXPECTED_COLUMNS = [
    "date",
    "admin1",
    "admin2",
    "market",
    "market_id",
    "latitude",
    "longitude",
    "category",
    "commodity",
    "commodity_id",
    "unit",
    "priceflag",
    "pricetype",
    "currency",
    "price",
    "usdprice",
]


def get_engine():
    required_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing = [key for key in required_vars if not os.getenv(key)]

    if missing:
        raise ValueError(
            f"Missing database environment variables: {missing}"
        )

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(database_url, pool_pre_ping=True)


def main(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        raise ValueError("Cannot load an empty or missing DataFrame")

    # Normalize column names
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    missing = sorted(set(EXPECTED_COLUMNS) - set(df.columns))

    if missing:
        raise ValueError(
            f"Cannot load data. Missing columns: {missing}"
        )

    # Keep only the columns expected by the raw table, in table order
    df = df[EXPECTED_COLUMNS]

    # Convert values to compatible Python/Pandas types
    df["date"] = pd.to_datetime(
        df["date"], errors="raise"
    ).dt.date

    for column in ["latitude", "longitude", "price", "usdprice"]:
        df[column] = pd.to_numeric(df[column], errors="raise")

    logger.info(
        "Stage 3/4: PostgreSQL load started | rows=%d | table=public.staging_food_prices",
        len(df),
    )

    engine = get_engine()

    try:
        # TRUNCATE and INSERT are in one transaction.
        # If INSERT fails, the previous table contents are preserved.
        with engine.begin() as connection:
            connection.execute(
                text("TRUNCATE TABLE public.staging_food_prices")
            )

            df.to_sql(
                name="staging_food_prices",
                schema="public",
                con=connection,
                if_exists="append",
                index=False,
                chunksize=1000,
            )

            loaded_rows = connection.execute(
                text("SELECT COUNT(*) FROM public.staging_food_prices")
            ).scalar_one()

            if loaded_rows != len(df):
                raise RuntimeError(
                    f"Row count mismatch: expected {len(df)}, "
                    f"found {loaded_rows}"
                )

        logger.info(
            "Stage 3/4: PostgreSQL load successful | rows=%d",
            loaded_rows,
        )

        return {
            "status": "success",
            "rows": loaded_rows,
            "table": "public.staging_food_prices",
            "message": "Raw dataset loaded successfully",
        }

    except Exception:
        logger.exception("Stage 3/4: PostgreSQL load failed")
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    logger.error(
        "This module requires a DataFrame. "
        "Run it through run_pipeline.py."
    )
