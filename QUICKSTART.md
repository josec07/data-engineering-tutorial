# Quick Start Guide

Get up and running with the Data Engineering Tutorial in 5 minutes!

## Option 1: Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Access the applications:
# - Streamlit Dashboard: http://localhost:8501
# - Airflow UI: http://localhost:8080 (admin/admin)
# - Jupyter Notebook: http://localhost:8888
```

## Option 2: Local Python

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run the CLI
python cli.py

# Run the dashboard
streamlit run app.py
```

## Project Structure

```
data-engineering-tutorial/
├── README.md                    ← Start here!
├── QUICKSTART.md               ← You are here
│
├── app.py                      ← Streamlit dashboard
├── cli.py                      ← Command-line interface
├── init_db.py                  ← Database setup
│
├── module_1_data_modeling/     ← Module 1: Learn data modeling
├── module_2_etl_pipeline/      ← Module 2: Build ETL with Airflow
├── module_3_data_quality/      ← Module 3: Data quality & testing
├── module_4_scalability/       ← Module 4: Scale with Parquet/Spark
└── module_5_monitoring/        ← Module 5: Monitoring & observability
```

## Learning Path

1. **Week 1**: Read [README.md](./README.md) and complete [Module 1](./module_1_data_modeling/)
2. **Week 2**: Complete [Module 2](./module_2_etl_pipeline/) - Build your first DAG
3. **Week 3**: Complete [Module 3](./module_3_data_quality/) - Add data quality checks
4. **Week 4**: Complete [Module 4](./module_4_scalability/) - Scale with Spark
5. **Week 5**: Complete [Module 5](./module_5_monitoring/) - Add monitoring

## Troubleshooting

### Docker issues
```bash
# Reset everything
docker-compose down -v
docker-compose up -d --build
```

### Database connection errors
```bash
# Reinitialize database
python init_db.py
```

### Port already in use
```bash
# Change ports in docker-compose.yml
# Default ports: 8501 (Streamlit), 8080 (Airflow), 8888 (Jupyter)
```

## Next Steps

- Read the [main README](./README.md)
- Start with [Module 1: Data Modeling](./module_1_data_modeling/)
- Join our [GitHub Discussions](https://github.com/yourusername/data-engineering-tutorial/discussions)

## Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Questions and general discussion
- **Email**: your-email@example.com

Happy learning!
