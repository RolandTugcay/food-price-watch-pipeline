import time
from datetime import datetime, timezone

from logger_config import get_logger

import download_data
import validate_data
import load_raw
import transform_data

logger = get_logger("food_price_watch.pipeline")

def run_pipeline():
    start_time = time.perf_counter()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    logger.info(
        "Pipeline started | run_id=%s",
        run_id,
    )

    try:

        ### Stage 1: Download data
        logger.info("Stage 1/4: Download started")

        result = download_data.main()

        if result["status"] != "success":
            raise RuntimeError(f"Download failed: {result['message']}")

        # Use the downloaded DataFrame in the next stage
        df = result["dataframe"]


        ### Stage 2: Validate
        logger.info("Stage 2/4: Validation started")

        validation_result = validate_data.main(df)

        if validation_result["status"] != "success":
            raise ValueError(f"Validation failed: {validation_result['errors']}")

        # Use the validated DataFrame in the next stage
        df = validation_result["dataframe"]


        ### Stage 3: Load into PostgreSQL
        logger.info("Stage 3/4: Database loading started")

        load_result = load_raw.main(df)

        if load_result["status"] != "success":
            raise RuntimeError(
                f"Database loading failed: {load_result['message']}"
            )


        ### Stage 4: Transform and populate normalized tables
        logger.info("Stage 4/4: Transformation started")

        transform_result = transform_data.main()

        if transform_result["status"] != "success":
            raise RuntimeError(f"Transformation failed: {transform_result['message']}")


        elapsed = time.perf_counter() - start_time

        logger.info(
            "Pipeline succeeded | run_id=%s | duration_seconds=%.2f",
            run_id,
            elapsed,
        )

    except Exception:
        elapsed = time.perf_counter() - start_time

        logger.exception(
            "Pipeline failed | run_id=%s | duration_seconds=%.2f",
            run_id,
            elapsed,
        )
        raise


if __name__ == "__main__":
    run_pipeline()
