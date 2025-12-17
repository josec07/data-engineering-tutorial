# Module 2: ETL Pipeline with Apache Airflow

**Duration**: 4-6 hours
**Difficulty**: Intermediate
**Prerequisites**: Module 1 completed, basic Python knowledge

## Learning Objectives

By the end of this module, you will:
- Understand ETL vs ELT patterns
- Build Apache Airflow DAGs
- Implement task dependencies
- Handle errors and retries
- Schedule automated workflows
- Monitor pipeline execution

---

## The Business Problem

**Manual Process** (Current):
1. User manually enters receipts via CLI
2. Market prices are never updated
3. No validation of data quality
4. No historical tracking

**Automated Solution** (Goal):
1. Auto-ingest receipts from scanned files (OCR)
2. Daily market price updates from external APIs
3. Automated data quality checks
4. Email alerts on failures

---

## Core Concepts

### ETL vs ELT

**ETL (Extract, Transform, Load)**:
```
Source → Transform in Pipeline → Load to Warehouse
```
- Transform before loading
- Good for smaller data volumes
- Cleaner data in warehouse

**ELT (Extract, Load, Transform)**:
```
Source → Load to Warehouse → Transform in Warehouse
```
- Transform after loading
- Better for large data volumes
- Leverage warehouse compute power

**Our Approach**: Hybrid (ETL for receipts, ELT for analytics)

### Apache Airflow Components

1. **DAG** (Directed Acyclic Graph): Workflow definition
2. **Task**: A single unit of work
3. **Operator**: What the task does (Python, SQL, Bash)
4. **Sensor**: Wait for a condition
5. **Schedule**: When the DAG runs

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│               APACHE AIRFLOW                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  DAG 1: receipt_ingestion_pipeline                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐       │
│  │ Scan for │ → │ Extract  │ → │ Load to  │       │
│  │ Receipts │   │ Data     │   │ Database │       │
│  └──────────┘   └──────────┘   └──────────┘       │
│                                                      │
│  DAG 2: market_price_update                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐       │
│  │ Fetch    │ → │ Transform│ → │ Update   │       │
│  │ API Data │   │ Prices   │   │ Database │       │
│  └──────────┘   └──────────┘   └──────────┘       │
│                                                      │
│  DAG 3: daily_analytics_report                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐       │
│  │ Calculate│ → │ Generate │ → │ Send     │       │
│  │ Metrics  │   │ Report   │   │ Email    │       │
│  └──────────┘   └──────────┘   └──────────┘       │
│                                                      │
└─────────────────────────────────────────────────────┘
           ↓                    ↓
    PostgreSQL              S3/Data Lake
```

---

## Exercise 1: Your First Airflow DAG

### Task

Create a simple DAG that:
1. Prints "Starting pipeline"
2. Counts receipts in database
3. Prints "Pipeline complete"

### Starter Code

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-engineer',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def start_pipeline():
    print("Starting Type43 Pipeline")

def count_receipts():
    # TODO: Connect to database and count receipts
    pass

def complete_pipeline():
    print("Pipeline complete!")

# TODO: Define the DAG
# TODO: Add tasks
# TODO: Set dependencies
```

**Starter file**: [exercises/hello_airflow.py](./exercises/hello_airflow.py)
**Solution**: [solutions/hello_airflow.py](./solutions/hello_airflow.py)

---

## Exercise 2: Receipt Ingestion Pipeline

### Business Requirements

**Input**: CSV files dropped in `data/receipts/incoming/`
**Process**:
1. Detect new files
2. Validate schema (vendor, date, amount)
3. Check for duplicates
4. Insert into database
5. Move file to `data/receipts/processed/`

### Task Dependencies

```
check_for_files
       ↓
validate_schema
       ↓
check_duplicates
       ↓
insert_receipts
       ↓
move_files
```

### Key Concepts

**FileSensor** - Wait for files to arrive
```python
from airflow.sensors.filesystem import FileSensor

wait_for_file = FileSensor(
    task_id='wait_for_receipt_files',
    filepath='/data/receipts/incoming/*.csv',
    poke_interval=30,  # Check every 30 seconds
    timeout=600,       # Timeout after 10 minutes
)
```

**PythonOperator** - Run Python functions
```python
from airflow.operators.python import PythonOperator

validate = PythonOperator(
    task_id='validate_schema',
    python_callable=validate_receipt_schema,
    op_kwargs={'file_path': '/data/receipts/incoming/latest.csv'}
)
```

**Starter file**: [exercises/receipt_ingestion_dag.py](./exercises/receipt_ingestion_dag.py)
**Solution**: [solutions/receipt_ingestion_dag.py](./solutions/receipt_ingestion_dag.py)

---

## Exercise 3: Market Price Update Pipeline

### Business Requirements

Fetch current market prices from external API daily to track inflation gains.

**Schedule**: Every day at 6 AM
**Data Source**: Home Depot API, commodities API
**Process**:
1. Get list of inventory items
2. For each item, fetch current market price
3. Insert into `market_valuations` table
4. Send summary email

### Advanced Concepts

**Dynamic Task Generation**
```python
from airflow.decorators import task

@task
def get_inventory_items():
    # Return list of items
    return ['Plywood', 'Drill', 'Hammer']

@task
def fetch_price(item):
    # Fetch price for one item
    price = call_api(item)
    return {'item': item, 'price': price}

# Create dynamic tasks
items = get_inventory_items()
prices = fetch_price.expand(item=items)  # Dynamic mapping!
```

**XCom** - Share data between tasks
```python
# Task 1: Store data
def extract_data(**context):
    data = fetch_api()
    context['ti'].xcom_push(key='api_data', value=data)

# Task 2: Retrieve data
def transform_data(**context):
    data = context['ti'].xcom_pull(key='api_data')
    transformed = process(data)
    return transformed
```

**Starter file**: [exercises/market_price_dag.py](./exercises/market_price_dag.py)
**Solution**: [solutions/market_price_dag.py](./solutions/market_price_dag.py)

---

## Exercise 4: Error Handling & Retries

### Task

Add robust error handling:
1. Retry failed tasks (3 attempts)
2. Send alert email on final failure
3. Log errors to database
4. Implement exponential backoff

### Example

```python
from airflow.operators.python import PythonOperator
from airflow.utils.email import send_email

def on_failure_callback(context):
    """Called when task fails after all retries"""
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    error = context['exception']

    send_email(
        to='admin@example.com',
        subject=f'Airflow Task Failed: {dag_id}.{task_id}',
        html_content=f'<p>Error: {error}</p>'
    )

task = PythonOperator(
    task_id='risky_operation',
    python_callable=might_fail,
    retries=3,
    retry_delay=timedelta(minutes=5),
    retry_exponential_backoff=True,
    on_failure_callback=on_failure_callback,
)
```

**Starter file**: [exercises/error_handling.py](./exercises/error_handling.py)
**Solution**: [solutions/error_handling.py](./solutions/error_handling.py)

---

## Exercise 5: Backfilling Historical Data

### Scenario

You just set up the pipeline, but need to ingest 6 months of historical receipts.

### Airflow Backfill Command

```bash
# Backfill receipts from Jan 1 to June 30, 2023
airflow dags backfill \
    --start-date 2023-01-01 \
    --end-date 2023-06-30 \
    receipt_ingestion_pipeline
```

### Idempotency

**Critical Concept**: DAGs should be idempotent (running multiple times produces same result)

**Bad** (not idempotent):
```python
def insert_receipt(data):
    # Will create duplicates!
    db.insert(data)
```

**Good** (idempotent):
```python
def insert_receipt(data):
    # Upsert: insert or update if exists
    db.upsert(data, on_conflict='receipt_id')
```

**Exercise**: Make your receipt ingestion DAG idempotent.

---

## Running Airflow Locally

### Installation

```bash
# Install Airflow
pip install apache-airflow==2.7.0

# Initialize database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start web server
airflow webserver --port 8080

# Start scheduler (in another terminal)
airflow scheduler
```

### Using Docker Compose

```bash
# Start Airflow with Docker
docker-compose up -d

# Access UI: http://localhost:8080
# Username: admin
# Password: admin
```

---

## Best Practices

### 1. DAG Design
- Keep DAGs simple and focused
- One DAG per business process
- Avoid complex branching

### 2. Task Design
- Make tasks atomic (do one thing)
- Make tasks idempotent
- Avoid long-running tasks (split them up)

### 3. Dependencies
- Minimize cross-DAG dependencies
- Use sensors for external dependencies
- Set appropriate timeouts

### 4. Resource Management
- Set task concurrency limits
- Use pools for shared resources
- Configure appropriate retries

### 5. Monitoring
- Add logging to all tasks
- Set up email alerts
- Monitor DAG duration trends

---

## Common Patterns

### Pattern 1: Branching Logic
```python
from airflow.operators.python import BranchPythonOperator

def decide_branch(**context):
    if condition:
        return 'task_a'
    else:
        return 'task_b'

branch = BranchPythonOperator(
    task_id='branching',
    python_callable=decide_branch
)

branch >> [task_a, task_b]
```

### Pattern 2: SubDAGs
```python
from airflow.operators.subdag import SubDagOperator

subdag = SubDagOperator(
    task_id='process_items',
    subdag=create_processing_subdag()
)
```

### Pattern 3: Trigger Rules
```python
# Run even if upstream fails
task = PythonOperator(
    task_id='cleanup',
    trigger_rule='all_done',  # Run regardless
    python_callable=cleanup
)
```

---

## Real-World Examples

### Data Warehouse ETL
```
extract_from_postgres >> transform_data >> load_to_snowflake
```

### ML Pipeline
```
extract_features >> train_model >> evaluate >> deploy_if_better
```

### Report Generation
```
query_data >> generate_charts >> create_pdf >> email_report
```

---

## Knowledge Check

1. **What's the difference between ETL and ELT?**
2. **Why should tasks be idempotent?**
3. **When would you use a Sensor vs a PythonOperator?**
4. **How does XCom work and when should you use it?**
5. **What's the purpose of backfilling?**

**Answers**: [solutions/knowledge_check.md](./solutions/knowledge_check.md)

---

## Going Further

### Advanced Topics
- Airflow Variables and Connections
- Custom Operators
- TaskFlow API (@task decorator)
- Kubernetes Executor
- Airflow REST API

### Recommended Reading
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- "Data Pipelines Pocket Reference" by James Densmore

---

## Next Steps

Once you've completed the exercises:
1. Deploy your DAGs to Airflow
2. Run and monitor pipeline execution
3. Test error handling and retries
4. Proceed to [Module 3: Data Quality →](../module_3_data_quality/)

---

**Questions?** Open an issue or discussion on GitHub!
