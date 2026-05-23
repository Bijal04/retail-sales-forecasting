🛒 Retail Sales Forecasting & Demand Planning

📌 Overview
A end-to-end data analytics project that ingests, cleans, and models 3 years of transactional retail sales data to forecast monthly demand by product category. The project combines Python-based data engineering, statistical forecasting, SQL data warehousing, and interactive Power BI visualization to support inventory and restocking decisions.

🛠️ Tech Stack
LayerToolsData Cleaning & EDAPython, Pandas, NumPyForecasting ModelsStatsmodels (ARIMA, Exponential Smoothing)Data WarehousingSQL (Star Schema, ETL Pipeline)VisualizationPower BIEnvironmentJupyter Notebook

📂 Project Structure
retail-sales-forecasting/
│
├── data/
│   ├── raw/                  # Original transactional sales data
│   └── processed/            # Cleaned and transformed datasets
│
├── notebooks/
│   ├── 01_data_cleaning.ipynb
│   ├── 02_eda.ipynb
│   └── 03_forecasting_models.ipynb
│
├── sql/
│   ├── schema.sql            # Star schema DDL (fact & dimension tables)
│   ├── etl_pipeline.sql      # ETL transformation queries
│   └── queries.sql           # Reporting and aggregation queries
│
├── src/
│   ├── data_cleaning.py      # Reusable cleaning functions
│   ├── forecasting.py        # ARIMA & Exponential Smoothing logic
│   └── etl.py                # ETL pipeline scripts
│
├── powerbi/
│   └── dashboard.pbix        # Power BI dashboard file
│
├── reports/
│   └── dashboard_preview.png # Dashboard screenshot
│
├── requirements.txt
├── .gitignore
└── README.md

🔍 Project Highlights
🧹 Data Cleaning & Preprocessing

Ingested 3 years of raw transactional sales data (50,000+ records)
Resolved missing values, duplicate entries, and schema inconsistencies using Pandas and NumPy
Standardized data types, column naming conventions, and date formats for downstream processing

📈 Forecasting Models

Built and compared two forecasting approaches using Statsmodels:

ARIMA — for capturing trend and autocorrelation patterns
Exponential Smoothing — for handling seasonality and level shifts


Achieved 91% forecast accuracy measured by MAPE (Mean Absolute Percentage Error)
Forecasted monthly sales across multiple product categories

🗄️ SQL ETL Pipeline & Data Warehouse

Designed a star schema data warehouse with clearly separated fact and dimension tables
Built an end-to-end SQL ETL pipeline to load cleaned Python output into structured warehouse tables
Optimized schema for reporting efficiency and BI tool compatibility

📊 Power BI Dashboard

Developed an interactive dashboard featuring:

Dynamic KPIs (revenue, units sold, forecast vs. actual)
Seasonal trend lines by product category
Inventory risk flags for low-stock alerts


Enabled data-driven restocking decisions, reducing the simulated stockout rate by 18%


🚀 Getting Started
Prerequisites

Python 3.8+
Jupyter Notebook
Power BI Desktop (to view .pbix file)
A SQL engine (PostgreSQL, MySQL, or SQLite)

Installation
bash# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/retail-sales-forecasting.git

# 2. Navigate into the project directory
cd retail-sales-forecasting

# 3. Install required Python libraries
pip install -r requirements.txt

# 4. Launch Jupyter and run notebooks in order
jupyter notebook
Run Notebooks in Order
01_data_cleaning.ipynb   →   02_eda.ipynb   →   03_forecasting_models.ipynb

📷 Dashboard Preview

Power BI dashboard showing KPIs, seasonal trends, and inventory risk flags

"------------------Show Image"

📊 Results Summary
MetricResultRecords Processed50,000+Forecast Accuracy (MAPE)91%Stockout Rate Reduction18%Forecasting Models UsedARIMA, Exponential SmoothingData Warehouse SchemaStar Schema

🤝 Contributing
Contributions, issues, and feature requests are welcome. Feel free to open an issue or submit a pull request.

📄 License
This project is licensed under the MIT License — see the LICENSE file for details.

👤 Author
Your Name

GitHub: @Bijal04
LinkedIn: linkedin.com/in/bijal-panchal
