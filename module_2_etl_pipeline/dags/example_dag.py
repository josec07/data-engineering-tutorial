"""
Example Airflow DAG for Type43 Analytics
This is a starter DAG showing basic Airflow concepts
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Default arguments for all tasks
default_args = {
    'owner': 'data-engineer',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def hello_type43():
    """Simple hello world function"""
    print("Hello from Type43 Analytics!")
    print("This DAG will process receipts and inventory data")

def check_database():
    """Check database connection"""
    # TODO: Add actual database connection check
    print("Checking database connection...")
    print("Database is healthy!")

def generate_report():
    """Generate a simple report"""
    print("Generating daily report...")
    print("Report complete!")

# Define the DAG
with DAG(
    'example_type43_pipeline',
    default_args=default_args,
    description='Example pipeline for Type43 Analytics',
    schedule_interval=timedelta(days=1),  # Run daily
    catchup=False,
    tags=['example', 'type43'],
) as dag:

    # Task 1: Hello world
    task_hello = PythonOperator(
        task_id='hello_type43',
        python_callable=hello_type43,
    )

    # Task 2: Check database
    task_check_db = PythonOperator(
        task_id='check_database',
        python_callable=check_database,
    )

    # Task 3: Generate report
    task_report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report,
    )

    # Define task dependencies
    task_hello >> task_check_db >> task_report
