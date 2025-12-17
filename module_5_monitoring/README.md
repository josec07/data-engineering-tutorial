# Module 5: Monitoring & Observability

**Duration**: 3-4 hours
**Difficulty**: Intermediate
**Prerequisites**: Modules 1-4 completed

## Learning Objectives

- Implement logging best practices
- Set up Airflow monitoring
- Create custom metrics
- Configure alerts (email, Slack)
- Track data lineage
- Monitor costs

---

## The Observability Problem

**Questions You Can't Answer** (without monitoring):
- Is my pipeline running?
- Why did it fail?
- How long does each task take?
- Is data quality degrading?
- What's my infrastructure cost?

**Solution**: Comprehensive monitoring stack

---

## Exercise 1: Structured Logging

### Task

Implement structured logging:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }
        return json.dumps(log_data)

logger = logging.getLogger('type43')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Usage
logger.info('Receipt ingested', extra={'receipt_id': 123, 'amount': 500})
```

---

## Exercise 2: Airflow Monitoring Dashboard

### Metrics to Track

1. **DAG Metrics**:
   - Success rate
   - Duration trends
   - Task failure rate

2. **Data Metrics**:
   - Rows processed
   - Data quality score
   - Anomaly count

3. **Infrastructure**:
   - CPU/memory usage
   - Database connections
   - Queue length

### Airflow Metrics Export

```python
from airflow.models import DagRun, TaskInstance
import prometheus_client as prom

# Custom metric
receipts_processed = prom.Counter(
    'receipts_processed_total',
    'Total receipts processed'
)

def ingest_receipt(**context):
    # Process receipt
    receipts_processed.inc()
```

---

## Exercise 3: Alerting

### Task

Set up email alerts for:
- Pipeline failures
- Data quality violations
- Anomalies detected

**Example**:
```python
from airflow.utils.email import send_email

def alert_on_failure(context):
    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    error = str(context['exception'])

    send_email(
        to='data-team@company.com',
        subject=f'🚨 Pipeline Failed: {dag_id}',
        html_content=f'''
            <h2>Task Failed</h2>
            <p><strong>DAG:</strong> {dag_id}</p>
            <p><strong>Task:</strong> {task_id}</p>
            <p><strong>Error:</strong> {error}</p>
        '''
    )
```

---

## Exercise 4: Data Lineage

### Task

Track data lineage (where data came from, how it was transformed).

**Tool**: Apache Atlas or OpenLineage

**Visualization**:
```
receipts.csv → validate_schema → clean_data → receipts_table
                                                      ↓
                                           market_valuations_table
```

---

## Exercise 5: Cost Monitoring

### Metrics

- Database query costs
- Storage costs (S3, database)
- Compute costs (Spark clusters)

**Dashboard**: Track cost per pipeline run

---

## Best Practices

1. **Log Everything**: Every pipeline stage
2. **Alert Smartly**: Avoid alert fatigue
3. **Visualize Trends**: Use dashboards
4. **Track SLAs**: Set and monitor service levels
5. **Post-Mortems**: Learn from failures

---

## Production Checklist

- [ ] Structured logging configured
- [ ] Airflow monitoring dashboard
- [ ] Email alerts for critical failures
- [ ] Data quality metrics tracked
- [ ] Cost monitoring enabled
- [ ] Data lineage documented
- [ ] Runbooks for common issues
- [ ] On-call rotation defined

---

## Congratulations!

You've completed all 5 modules! You now have:
- Production-ready data models
- Automated ETL pipelines
- Data quality checks
- Scalable architecture
- Comprehensive monitoring

**Next Steps**:
- Deploy to production
- Share your learnings
- Contribute to the tutorial
- Build your own data platform!

---

**Questions?** Open an issue or discussion on GitHub!
