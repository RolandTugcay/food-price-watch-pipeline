import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

from logger_config import get_logger

logger = get_logger("food_price_watch.transform")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_engine():
    required = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(
            f"Missing database environment variables: {missing}"
        )

    url = URL.create(
        "postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(url, pool_pre_ping=True)


def main() -> dict:
    engine = get_engine()

    try:
        with engine.begin() as connection:
            # Confirm the staging table contains records
            staging_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM public.staging_food_prices"
                )
            ).scalar_one()

            if staging_count == 0:
                raise ValueError(
                    "staging_food_prices is empty; "
                    "run the download and load stages first"
                )

            logger.info(
                "Stage 4/4: Transformation started | staging_rows=%d",
                staging_count,
            )

            # 1. Populate categories
            connection.execute(text("""
                INSERT INTO public.categories (category_name)
                SELECT DISTINCT TRIM(category)
                FROM public.staging_food_prices
                WHERE category IS NOT NULL
                  AND TRIM(category) <> ''
                ON CONFLICT (category_name) DO NOTHING
            """))

            # 2. Populate markets using original WFP market_id
            connection.execute(text("""
                INSERT INTO public.markets (
                    market_id,
                    market_name,
                    admin1,
                    admin2,
                    latitude,
                    longitude
                )
                SELECT DISTINCT ON (market_id)
                    market_id,
                    market,
                    admin1,
                    admin2,
                    latitude,
                    longitude
                FROM public.staging_food_prices
                WHERE market_id IS NOT NULL
                  AND market IS NOT NULL
                ORDER BY market_id, market
                ON CONFLICT (market_id) DO UPDATE SET
                    market_name = EXCLUDED.market_name,
                    admin1 = EXCLUDED.admin1,
                    admin2 = EXCLUDED.admin2,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude
            """))

            # 3. Populate commodities using original WFP commodity_id
            connection.execute(text("""
                INSERT INTO public.commodities (
                    commodity_id,
                    commodity_name,
                    category_id
                )
                SELECT DISTINCT ON (s.commodity_id)
                    s.commodity_id,
                    s.commodity,
                    c.category_id
                FROM public.staging_food_prices AS s
                LEFT JOIN public.categories AS c
                    ON c.category_name = TRIM(s.category)
                WHERE s.commodity_id IS NOT NULL
                  AND s.commodity IS NOT NULL
                ORDER BY
                    s.commodity_id,
                    s.commodity,
                    c.category_id
                ON CONFLICT (commodity_id) DO UPDATE SET
                    commodity_name = EXCLUDED.commodity_name,
                    category_id = EXCLUDED.category_id
            """))

            # 4. Populate price observations
            connection.execute(text("""
                INSERT INTO public.price_observations (
                    observation_date,
                    market_id,
                    commodity_id,
                    unit,
                    price_flag,
                    price_type,
                    currency,
                    price,
                    usd_price
                )
                SELECT DISTINCT
                    s.date,
                    s.market_id,
                    s.commodity_id,
                    s.unit,
                    s.priceflag,
                    s.pricetype,
                    s.currency,
                    s.price,
                    s.usdprice
                FROM public.staging_food_prices AS s
                INNER JOIN public.markets AS m
                    ON m.market_id = s.market_id
                INNER JOIN public.commodities AS co
                    ON co.commodity_id = s.commodity_id
                WHERE s.date IS NOT NULL
                ON CONFLICT ON CONSTRAINT uq_price_observation
                DO UPDATE SET
                    price_flag = EXCLUDED.price_flag,
                    price = EXCLUDED.price,
                    usd_price = EXCLUDED.usd_price
            """))

            # 5. Collect final table counts
            counts = {}

            for table in [
                "markets",
                "categories",
                "commodities",
                "price_observations",
            ]:
                counts[table] = connection.execute(
                    text(f"SELECT COUNT(*) FROM public.{table}")
                ).scalar_one()

        logger.info(
            "Stage 4/4: Transformation completed | table_counts=%s",
            counts,
        )

        return {
            "status": "success",
            "staging_rows": staging_count,
            "table_counts": counts,
            "message": "Normalized tables populated successfully",
        }

    except Exception:
        logger.exception("Stage 4/4: Transformation failed")
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    result = main()
    print(result)
