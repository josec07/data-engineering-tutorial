# Module 4: Scalability with Parquet & Spark

**Duration**: 4-5 hours
**Difficulty**: Advanced
**Prerequisites**: Modules 1-3 completed

## Learning Objectives

- Understand columnar storage (Parquet vs CSV)
- Partition data for performance
- Use Apache Spark for distributed processing
- Optimize query performance
- Design data lake architecture

---

## The Performance Problem

**Current State**: 10,000 receipts in SQLite
- Query time: 50ms
- Storage: 2MB

**Future State**: 10,000,000 receipts
- Query time with SQLite: 30+ seconds ⚠️
- Storage: 2GB

**Solution**: Parquet files + partitioning + Spark

---

## Exercise 1: CSV vs Parquet Benchmark

### Task

Compare performance and storage:

```python
import pandas as pd
import time

# Generate large dataset
df = generate_receipts(1_000_000)

# Benchmark CSV
start = time.time()
df.to_csv('receipts.csv', index=False)
csv_time = time.time() - start

# Benchmark Parquet
start = time.time()
df.to_parquet('receipts.parquet')
parquet_time = time.time() - start

print(f"CSV: {csv_time:.2f}s, {os.path.getsize('receipts.csv') / 1e6:.2f}MB")
print(f"Parquet: {parquet_time:.2f}s, {os.path.getsize('receipts.parquet') / 1e6:.2f}MB")
```

**Expected Results**:
- Parquet is 5-10x smaller
- Parquet write is faster
- Parquet read (columnar) is 10-100x faster for analytics

---

## Exercise 2: Partitioning Strategy

### Task

Partition receipts by year and month:

```
data/
  receipts/
    year=2023/
      month=01/
        part-0001.parquet
      month=02/
        part-0001.parquet
    year=2024/
      month=01/
        part-0001.parquet
```

**Benefits**:
- Query only relevant partitions
- Faster queries (partition pruning)
- Easier data management

**Code**:
```python
# Write partitioned
df.to_parquet(
    'data/receipts/',
    partition_cols=['year', 'month'],
    engine='pyarrow'
)

# Read specific partition
df = pd.read_parquet('data/receipts/year=2024/month=01/')
```

---

## Exercise 3: Apache Spark Processing

### Task

Process 10M receipts with Spark:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Type43").getOrCreate()

# Read Parquet
receipts = spark.read.parquet("data/receipts/")

# Aggregation (distributed!)
totals = receipts.groupBy("vendor_name").sum("total_amount")

# Write results
totals.write.parquet("data/vendor_totals/")
```

---

## Exercise 4: Query Optimization

### Compare

**Slow** (full scan):
```sql
SELECT * FROM receipts WHERE total_amount > 1000;
```

**Fast** (partitioned + columnar):
```python
df = pd.read_parquet(
    'data/receipts/',
    filters=[('total_amount', '>', 1000)],
    columns=['vendor_name', 'total_amount']  # Only read needed columns
)
```

---

## Exercise 5: Data Lake Architecture

Design a data lake with:
- Bronze layer (raw data)
- Silver layer (cleaned data)
- Gold layer (aggregated metrics)

---

## Next Steps

Proceed to [Module 5: Monitoring →](../module_5_monitoring/)
