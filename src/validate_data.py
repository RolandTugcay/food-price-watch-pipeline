import pandas as pd
from logger_config import get_logger

logger = get_logger("food_price_watch.validation")

REQUIRED_COLUMNS = {
    "date",
    "market",
    "commodity",
    "unit",
    "price",
}

NUMERIC_COLUMNS = [
    "price",
    "usdprice",
]


def main(df: pd.DataFrame) -> dict:

    errors = []
    warnings = []

    try:
        if df is None:
            raise ValueError("Input DataFrame is None")

        if df.empty:
            raise ValueError("Dataset is empty")

        # Standardize column names for checking
        df = df.copy()
        df.columns = df.columns.str.strip().str.lower()

        # 1. Check required columns
        missing_columns = REQUIRED_COLUMNS - set(df.columns)

        if missing_columns:
            errors.append(
                f"Missing required columns: {sorted(missing_columns)}"
            )

        if errors:
            logger.error("Stage 2/4: Validation failed: %s", errors)

            return {
                "status": "failed",
                "rows": len(df),
                "errors": errors,
                "warnings": warnings,
                "dataframe": None,
            }

        # 2. Check missing values in important columns
        for column in REQUIRED_COLUMNS:
            missing_count = int(df[column].isna().sum())

            if missing_count > 0:
                warnings.append(
                    f"{column}: {missing_count} missing values"
                )

        # 3. Validate dates
        parsed_dates = pd.to_datetime(
            df["date"],
            errors="coerce",
        )

        invalid_dates = int(parsed_dates.isna().sum())

        if invalid_dates > 0:
            warnings.append(
                f"Found {invalid_dates} invalid or missing dates"
            )

        if invalid_dates == len(df):
            errors.append("All dates are invalid or missing")

        # 4. Validate numeric price columns
        for column in NUMERIC_COLUMNS:
            if column not in df.columns:
                continue

            numeric_values = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            invalid_count = int(
                (df[column].notna() & numeric_values.isna()).sum()
            )

            if invalid_count > 0:
                warnings.append(
                    f"{column}: {invalid_count} non-numeric values"
                )

            negative_count = int((numeric_values < 0).sum())

            if negative_count > 0:
                warnings.append(
                    f"{column}: {negative_count} negative prices"
                )

        # 5. Check duplicate rows
        duplicate_count = int(df.duplicated().sum())

        if duplicate_count > 0:
            warnings.append(
                f"Found {duplicate_count} duplicate rows"
            )

        # 6. Report results
        status = "failed" if errors else "success"

        logger.info(
            "Stage 2/4: Validation completed | status=%s | rows=%d | errors=%d | warnings=%d",
            status,
            len(df),
            len(errors),
            len(warnings),
        )

        for warning in warnings:
            logger.warning(warning)

        return {
            "status": status,
            "rows": len(df),
            "errors": errors,
            "warnings": warnings,
            "dataframe": df if status == "success" else None,
        }

    except Exception:
        logger.exception("Stage 2/4: Unexpected validation error")
        raise
