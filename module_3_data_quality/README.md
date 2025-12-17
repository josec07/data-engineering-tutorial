# Module 3: Data Quality & Testing

**Duration**: 3-4 hours
**Difficulty**: Intermediate
**Prerequisites**: Modules 1-2 completed

## Learning Objectives

By the end of this module, you will:
- Implement data validation with Great Expectations
- Write unit tests for data transformations
- Detect data anomalies
- Build data quality dashboards
- Create data contracts

---

## The Business Problem

**Bad Data Scenarios**:
- Receipt with negative amount (-$500)
- Duplicate receipts imported twice
- Inventory quantity of 1,000,000 hammers (typo)
- Missing vendor name (NULL)
- Future dates (purchase_date = 2025-01-01)

**Impact**:
- Incorrect financial reports
- Lost trust in data
- Bad business decisions

**Solution**: Automated data quality checks at every pipeline stage

---

## Core Concepts

### 1. Data Quality Dimensions

- **Accuracy**: Is the data correct?
- **Completeness**: Are there missing values?
- **Consistency**: Does data match across systems?
- **Timeliness**: Is data up-to-date?
- **Validity**: Does data conform to rules?
- **Uniqueness**: Are there duplicates?

### 2. Testing Pyramid

```
       /\
      /  \     E2E Tests (Few)
     /____\
    /      \   Integration Tests (Some)
   /________\
  /          \ Unit Tests (Many)
 /____________\
```

---

## Exercise 1: Great Expectations Setup

### Task

Set up Great Expectations to validate receipts data.

**Install**:
```bash
pip install great-expectations
great_expectations init
```

**Create Expectation Suite**:
```python
import great_expectations as gx

# Expectations for receipts
suite = gx.ExpectationSuite(name="receipts_suite")

# Amount must be positive
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="total_amount",
        min_value=0,
        max_value=100000
    )
)

# Vendor name required
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(
        column="vendor_name"
    )
)

# Date format validation
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToMatchRegex(
        column="purchase_date",
        regex=r"^\d{4}-\d{2}-\d{2}$"
    )
)
```

**Starter**: [exercises/expectations_setup.py](./exercises/expectations_setup.py)
**Solution**: [solutions/expectations_setup.py](./solutions/expectations_setup.py)

---

## Exercise 2: Unit Testing Transformations

### Task

Write pytest tests for data transformation functions.

**Example**:
```python
import pytest
from utils.transformations import calculate_inflation_gain

def test_calculate_inflation_gain():
    # Test normal case
    purchase_price = 100
    current_price = 150
    expected = 50

    result = calculate_inflation_gain(purchase_price, current_price)
    assert result == expected

def test_calculate_inflation_gain_negative():
    # Test depreciation
    purchase_price = 100
    current_price = 80
    expected = -20

    result = calculate_inflation_gain(purchase_price, current_price)
    assert result == expected

def test_calculate_inflation_gain_zero():
    # Test edge case
    purchase_price = 0
    current_price = 100

    with pytest.raises(ValueError):
        calculate_inflation_gain(purchase_price, current_price)
```

**Starter**: [exercises/test_transformations.py](./exercises/test_transformations.py)

---

## Exercise 3: Anomaly Detection

### Task

Build a statistical anomaly detector for receipt amounts.

**Approach**:
1. Calculate mean and standard deviation
2. Flag values > 3 standard deviations
3. Log anomalies to database

**Example**:
```python
import pandas as pd
import numpy as np

def detect_anomalies(df, column, threshold=3):
    mean = df[column].mean()
    std = df[column].std()

    df['z_score'] = (df[column] - mean) / std
    df['is_anomaly'] = np.abs(df['z_score']) > threshold

    return df[df['is_anomaly']]

# Usage
anomalies = detect_anomalies(receipts_df, 'total_amount')
print(f"Found {len(anomalies)} anomalies")
```

**Starter**: [exercises/anomaly_detection.py](./exercises/anomaly_detection.py)

---

## Exercise 4: Duplicate Detection

### Task

Find and handle duplicate receipts.

**Strategies**:
1. Exact match (same vendor, date, amount)
2. Fuzzy match (similar amounts, dates within 1 day)
3. Hash-based deduplication

**Example**:
```python
# Exact duplicates
duplicates = df[df.duplicated(
    subset=['vendor_name', 'purchase_date', 'total_amount'],
    keep=False
)]

# Fuzzy duplicates using hashing
df['receipt_hash'] = df.apply(
    lambda row: hash(f"{row['vendor']}{row['date']}{round(row['amount'], 2)}"),
    axis=1
)
```

---

## Exercise 5: Data Quality Dashboard

### Task

Create a Streamlit dashboard showing data quality metrics.

**Metrics to Display**:
- Completeness rate (% non-null)
- Duplicate count
- Anomaly count
- Schema validation status
- Data freshness (time since last update)

**Starter**: [exercises/quality_dashboard.py](./exercises/quality_dashboard.py)

---

## Best Practices

1. **Validate Early**: Check at ingestion, not analytics
2. **Fail Fast**: Stop pipeline on critical failures
3. **Log Everything**: Record quality check results
4. **Monitor Trends**: Track quality over time
5. **Automate**: Run checks in every DAG

---

## Integration with Airflow

```python
from airflow.operators.python import PythonOperator
from great_expectations_provider.operators.great_expectations import GreatExpectationsOperator

# Add to your DAG
validate_receipts = GreatExpectationsOperator(
    task_id='validate_receipts',
    expectation_suite_name='receipts_suite',
    data_context_root_dir='/path/to/gx',
    fail_task_on_validation_failure=True
)

ingest_data >> validate_receipts >> transform_data
```

---

## Next Steps

Proceed to [Module 4: Scalability →](../module_4_scalability/)
