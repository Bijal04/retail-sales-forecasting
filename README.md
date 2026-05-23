# Retail Sales Forecasting & Demand Planning

A machine learning and statistical forecasting system for predicting monthly retail sales by product category, backed by a SQL data warehouse and an interactive Power BI dashboard for demand planning and inventory optimization.

## Description

This end-to-end data analytics project simulates a real-world retail forecasting pipeline. It ingests and cleans 3 years of transactional sales data (50,000+ records) sourced from the UCI Machine Learning Repository, applies time series forecasting models (ARIMA and Exponential Smoothing), and delivers insights through a structured SQL data warehouse and a Power BI dashboard. The project achieves 91% forecast accuracy (MAPE) and supports data-driven restocking decisions — reducing simulated stockout rates by 18%.

## Getting Started

### Dependencies

* Python 3.9 or higher
* Jupyter Notebook or JupyterLab
* SQL environment — PostgreSQL, MySQL, or SQLite
* Microsoft Power BI Desktop (Windows)
* Required Python libraries (see Installing section)
* OS: Windows 10/11 or macOS 12+

### Installing

1. Clone the repository:
git clone https://github.com/bijal04/retail-sales-forecasting.git
cd retail-sales-forecasting
cd retail-sales-forecasting

2. Create and activate a virtual environment (recommended):
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

3. Install all required Python dependencies:
pip install -r requirements.txt

4. Download the dataset from the UCI Machine Learning Repository:
   Visit: http://archive.ics.uci.edu/dataset/502/online+retail+ii
   Download the Excel file and place it in the `data/raw/` folder as `online_retail.xlsx`

5. Set up the SQL database by running the schema script:
psql -U your_username -d your_database -f sql/schema.sql

6. Open Power BI Desktop and load `powerbi/dashboard.pbix` to explore the dashboard.

### Executing Program

Run the notebooks in the following order for the full pipeline:

**Step 1 — Data Cleaning & Preprocessing**
jupyter notebook notebooks/01_data_cleaning.ipynb

**Step 2 — Exploratory Data Analysis**
jupyter notebook notebooks/02_eda.ipynb

**Step 3 — Forecasting Models (ARIMA & Exponential Smoothing)**
jupyter notebook notebooks/03_forecasting_models.ipynb

**Step 4 — Load processed data into SQL warehouse**
python src/etl.py

**Step 5 — Open the Power BI dashboard**
* Launch Power BI Desktop
* Open `powerbi/dashboard.pbix`
* Refresh data source connection if prompted

## Help

**Common Issues:**

If `statsmodels` throws a convergence warning during ARIMA fitting:
model = ARIMA(data, order=(p,d,q)).fit(method_kwargs={"warn_convergence": False})

If Power BI cannot find the data source, update the file path under:
Home → Transform Data → Data Source Settings

If dependencies fail to install:
pip install --upgrade pip
pip install -r requirements.txt

If the UCI dataset file throws a format error on load:
df = pd.read_excel('data/raw/online_retail.xlsx', engine='openpyxl')

## Authors

* LinkedIn: www.linkedin.com/in/bijal-panchal
* GitHub: @bijal04

## Version History

* 0.2
    * Added Exponential Smoothing model and MAPE comparison
    * Power BI dashboard with inventory risk flags
    * See [release history]()
* 0.1
    * Initial release: data cleaning pipeline, ARIMA model, SQL star schema ETL

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
