# Data Engineering Fundamentals Tutorial

**A hands-on guide to modern data engineering using a real-world construction inventory tracking system**

## Project Overview

This tutorial teaches core data engineering concepts through **Type43 Analytics** - a construction business inventory and receipt tracking system. You'll learn how to build production-grade data pipelines, ensure data quality, and scale data systems.

### What You'll Build

A complete data platform that:
- Tracks receipts and physical inventory
- Calculates asset valuations and inflation gains
- Processes data at scale
- Maintains data quality
- Monitors pipeline health

### Business Context

**The Problem**: Construction contractors struggle to track expenses, inventory, and asset values across multiple job sites. Receipts get lost, tools disappear, and there's no visibility into inflation-driven equity gains.

**The Solution**: A data pipeline that ingests receipts, tracks physical assets, monitors market prices, and provides real-time analytics.

---

## Tutorial Modules

### Module 1: Data Modeling Fundamentals
**Concepts**: Schema design, normalization, relationships, data types

**What You'll Learn**:
- Designing dimensional models (star schema)
- Fact vs dimension tables
- Referential integrity
- SQLite vs PostgreSQL trade-offs

**Deliverables**: Production-ready database schema

[Start Module 1 →](./module_1_data_modeling/)

---

### Module 2: ETL Pipelines with Apache Airflow
**Concepts**: Orchestration, DAGs, task dependencies, scheduling

**What You'll Learn**:
- Building ETL workflows
- Airflow DAG creation
- Task dependencies and sensors
- Error handling and retries
- Backfilling historical data

**Deliverables**: Automated pipeline for receipt ingestion and market price updates

[Start Module 2 →](./module_2_etl_pipeline/)

---

### Module 3: Data Quality & Testing
**Concepts**: Validation, testing, data contracts, anomaly detection

**What You'll Learn**:
- Schema validation
- Data quality checks (Great Expectations)
- Unit testing data transformations
- Detecting duplicates and anomalies
- Building data quality dashboards

**Deliverables**: Comprehensive test suite and quality monitoring

[Start Module 3 →](./module_3_data_quality/)

---

### Module 4: Scalability with Parquet & Partitioning
**Concepts**: Columnar storage, partitioning, distributed processing

**What You'll Learn**:
- CSV vs Parquet performance
- Partition strategies (by date, category)
- Apache Spark for large-scale processing
- Query optimization
- Data lake architecture

**Deliverables**: Optimized data storage with 10x performance improvement

[Start Module 4 →](./module_4_scalability/)

---

### Module 5: Monitoring & Observability
**Concepts**: Logging, metrics, alerting, data lineage

**What You'll Learn**:
- Pipeline monitoring with Airflow
- Custom metrics and KPIs
- Alert configuration (Slack, email)
- Data lineage tracking
- Cost monitoring

**Deliverables**: Production monitoring stack

[Start Module 5 →](./module_5_monitoring/)

---

## Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Git
- 4GB RAM minimum

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/data-engineering-tutorial.git
cd data-engineering-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python init_db.py

# Run the dashboard
streamlit run app.py
```

### Using Docker

```bash
# Start all services (Airflow, PostgreSQL, Streamlit)
docker-compose up -d

# Access services:
# - Streamlit Dashboard: http://localhost:8501
# - Airflow UI: http://localhost:8080
# - PostgreSQL: localhost:5432
```

---

## Project Structure

```
data-engineering-tutorial/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .gitignore
│
├── app.py                          # Streamlit dashboard
├── cli.py                          # CLI for data entry
├── init_db.py                      # Database initialization
├── schema.sql                      # SQL schema definition
│
├── module_1_data_modeling/         # Module 1: Data Modeling
│   ├── README.md
│   ├── exercises/
│   └── solutions/
│
├── module_2_etl_pipeline/          # Module 2: ETL with Airflow
│   ├── README.md
│   ├── dags/
│   ├── exercises/
│   └── solutions/
│
├── module_3_data_quality/          # Module 3: Data Quality
│   ├── README.md
│   ├── tests/
│   ├── expectations/
│   └── solutions/
│
├── module_4_scalability/           # Module 4: Scalability
│   ├── README.md
│   ├── spark_jobs/
│   ├── benchmarks/
│   └── solutions/
│
├── module_5_monitoring/            # Module 5: Monitoring
│   ├── README.md
│   ├── dashboards/
│   ├── alerts/
│   └── solutions/
│
├── data/                           # Sample datasets
│   ├── receipts/
│   ├── inventory/
│   └── market_prices/
│
└── utils/                          # Shared utilities
    ├── db_utils.py
    ├── validation.py
    └── logging_config.py
```

---

## Learning Path

### Beginner Track (Weeks 1-2)
1. Complete Module 1 (Data Modeling)
2. Run the basic app and CLI
3. Understand the schema and relationships

### Intermediate Track (Weeks 3-4)
4. Complete Module 2 (ETL Pipeline)
5. Complete Module 3 (Data Quality)
6. Build your first production pipeline

### Advanced Track (Weeks 5-6)
7. Complete Module 4 (Scalability)
8. Complete Module 5 (Monitoring)
9. Deploy to production

---

## Technologies Used

| Technology | Purpose | Module |
|------------|---------|--------|
| **Python** | Core language | All |
| **SQLite/PostgreSQL** | Relational database | 1 |
| **Apache Airflow** | Workflow orchestration | 2 |
| **Great Expectations** | Data quality testing | 3 |
| **Apache Parquet** | Columnar storage | 4 |
| **Apache Spark** | Distributed processing | 4 |
| **Prometheus/Grafana** | Monitoring | 5 |
| **Streamlit** | Dashboard UI | All |
| **Docker** | Containerization | All |

---

## Key Concepts Covered

- **Data Modeling**: Star schema, normalization, relationships
- **ETL/ELT**: Extract, Transform, Load patterns
- **Orchestration**: DAGs, task dependencies, scheduling
- **Data Quality**: Validation, testing, anomaly detection
- **Scalability**: Partitioning, columnar storage, distributed computing
- **Observability**: Logging, metrics, alerting, lineage
- **DevOps**: Docker, CI/CD, infrastructure as code

---

## Real-World Applications

This tutorial's patterns apply to:
- E-commerce analytics platforms
- Financial transaction processing
- IoT sensor data pipelines
- Healthcare data warehouses
- Supply chain tracking systems
- Marketing attribution platforms

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## Resources

### Documentation
- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [Great Expectations](https://docs.greatexpectations.io/)
- [Apache Parquet](https://parquet.apache.org/docs/)
- [Streamlit](https://docs.streamlit.io/)

### Related Tutorials
- [Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp)
- [Awesome Data Engineering](https://github.com/igorbarinov/awesome-data-engineering)

---

## License

MIT License - See LICENSE file for details

---

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/data-engineering-tutorial/issues)
- Discussions: [Ask questions and share ideas](https://github.com/yourusername/data-engineering-tutorial/discussions)

---

**Ready to become a data engineer? Start with [Module 1](./module_1_data_modeling/)!**
