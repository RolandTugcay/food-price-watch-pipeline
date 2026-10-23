# FoodPriceWatch — Philippines Food Price Data Pipeline

An automated data engineering project that collects, validates, stages, and transforms food price data for the Philippines using the World Food Programme (WFP) dataset. The pipeline uses Python, Pandas, SQLAlchemy, PostgreSQL, Supabase, and GitHub Actions.

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Data Source](#data-source)
- [Data Pipeline](#data-pipeline)
- [Database Design](#database-design)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create a Virtual Environment](#2-create-a-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
  - [5. Run the Pipeline](#5-run-the-pipeline)
- [Supabase Configuration](#supabase-configuration)
- [Automated Execution with GitHub Actions](#automated-execution-with-github-actions)
  - [Schedule](#schedule)
- [Security and Reliability](#security-and-reliability)
- [Project Goal](#project-goal)

## Project Overview

FoodPriceWatch automates the processing of food price observations from the WFP food prices dataset for the Philippines.

The pipeline downloads the source CSV, validates the data, loads the raw records into a staging table, and transforms them into normalized relational tables in PostgreSQL hosted on Supabase.

The project demonstrates an end-to-end data engineering workflow, from raw data ingestion to database transformation and scheduled cloud execution.

## Technology Stack

- **Python** — Pipeline orchestration and data processing
- **Pandas** — Data cleaning and transformation
- **SQLAlchemy** — Database connections and SQL operations
- **Psycopg 3** — PostgreSQL database driver
- **Requests** — Source data download
- **python-dotenv** — Local environment variable management
- **PostgreSQL** — Relational database
- **Supabase** — Hosted PostgreSQL database
- **GitHub Actions** — Automated pipeline execution

## Data Source

The project uses the World Food Programme food price dataset for the Philippines, published through the Humanitarian Data Exchange (HDX).

Source dataset: [WFP Food Prices — Philippines](https://data.humdata.org/dataset/ea251823-8694-47b4-82d0-7d27f00e8aba/resource/9a842d72-0d7d-4922-ad0e-eb8106c1ab0e/download/wfp_food_prices_phl.csv)

The source data contains food price observations associated with markets, commodities, dates, units, currencies, and price information.

## Data Pipeline

The pipeline follows a staged data processing approach:

1. **Data extraction** — Download the source CSV.
2. **Data validation** — Check the downloaded dataset before loading.
3. **Raw data loading** — Load source records into `staging_food_prices`.
4. **Data transformation** — Populate normalized tables from the staging data.
5. **Database storage** — Persist the processed data in Supabase PostgreSQL.

The pipeline is orchestrated through `src/run_pipeline.py`.

## Database Design

The database uses a staging table and normalized tables to separate raw ingestion from structured analytical data.

| Table | Purpose |
|---|---|
| `staging_food_prices` | Stores the raw imported food price records |
| `markets` | Stores market information |
| `categories` | Stores commodity category information |
| `commodities` | Stores commodity information and category relationships |
| `price_observations` | Stores dated food price observations and related foreign keys |

Source identifiers such as `market_id` and `commodity_id` are retained when populating the normalized tables.

## Project Structure

```text
food-price-watch-pipeline/
└── .github/
    └── workflows/
        └── foodpricewatch.yml
├── data
├── logs
├── src/
    ├── download_data.py
    ├── load_raw.py
    ├── logger_config.py
    ├── run_pipeline.py
    ├── transform_data.py
    ├── validate_data.py
├── .env                 # Local only; not committed
├── .env.example         # Example variable names, if maintained
├── .gitignore
├── README.md
├── requirements.txt
```

Additional source files may be present depending on the implementation.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/RolandTugcay/food-price-watch-pipeline
cd food-price-watch-pipeline
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file in the project root:

```dotenv
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

Replace the example values with your actual database connection details.

**Security:** Never commit `.env` or expose database credentials in source code. Keep `.env` in `.gitignore`.

### 5. Run the pipeline

From the project root:

```bash
python src/run_pipeline.py
```

Ensure the database is accessible and the required tables have been created before running the pipeline.

## Supabase Configuration

The pipeline connects to a hosted PostgreSQL database in Supabase using environment variables.

For GitHub Actions, use the Supabase Session Pooler connection details when appropriate for the runner's network connectivity.

Configure these repository secrets under **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `DB_HOST` | Database or pooler hostname |
| `DB_PORT` | Database connection port |
| `DB_NAME` | Database name |
| `DB_USER` | Database username |
| `DB_PASSWORD` | Database password |

The GitHub Actions workflow injects these secrets as environment variables during execution. The pipeline does not require the local `.env` file in GitHub Actions.

## Automated Execution with GitHub Actions

The workflow is defined in:

```text
.github/workflows/food-price-watch-pipeline.yml
```

It supports scheduled execution and manual triggering through the GitHub Actions interface.

### Schedule

```yaml
on:
  schedule:
    - cron: "0 16 * * 1"
  workflow_dispatch:
```

GitHub Actions interprets cron schedules in UTC.

- **UTC schedule:** Monday at 16:00
- **Philippine time:** Tuesday at 12:00 AM (midnight, UTC+8)
- **Frequency:** Weekly
- **Manual execution:** Available through `workflow_dispatch`

Scheduled workflow runs may be delayed by GitHub Actions, so the configured time is the target start time.

## Security and Reliability

- Database credentials are stored in GitHub repository secrets.
- Local environment files are excluded from version control.
- The raw staging table is separated from the normalized data tables.
- PostgreSQL access should follow the principle of least privilege.
- Database transformations should be designed to handle repeated executions safely and avoid unintended duplicate records.

## Project Goal

FoodPriceWatch demonstrates practical data engineering skills through automated data ingestion, data validation, relational database design, cloud database integration, and scheduled pipeline orchestration.

The project provides a foundation for analyzing food price trends across markets in the Philippines.
