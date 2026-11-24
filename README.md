# 📊 NexusIQ – Intelligent Business Decision & Prediction Platform

NexusIQ is an interactive business analytics platform developed using Python, Streamlit, and SQL. It transforms retail transaction data into meaningful business insights through data cleaning, sales analysis, SQL-based queries, and RFM customer segmentation.

The platform helps businesses understand sales performance, identify valuable customers, analyze purchasing behavior, and make data-driven decisions.

## 🚀 Key Features

### 1. Dataset Upload & Data Cleaning
- Upload datasets in CSV and Excel formats.
- View dataset structure, records, columns, and missing values.
- Remove cancelled invoices and invalid transactions.
- Handle missing and invalid data.
- Calculate revenue using quantity and unit price.

### 2. Business Overview
- Total Revenue
- Total Orders
- Unique Customers
- Total Units Sold
- Interactive country and date filters.
- SQL-powered business metrics.

### 3. Sales Analytics
- Monthly Revenue Analysis.
- Top 10 Products by Revenue.
- Country-wise Sales Analysis.
- Interactive visualizations using Plotly.

### 4. SQL Database Integration
- Stores cleaned transactions in an SQLite database.
- Performs analytical queries using SQL.
- Calculates business metrics, product performance, and country-wise revenue.
- Generates the database automatically when the application processes a dataset.

### 5. RFM Customer Segmentation

Uses RFM analysis to understand customer purchasing behavior.

- **Recency:** How recently a customer made a purchase.
- **Frequency:** How frequently a customer purchased.
- **Monetary:** How much a customer spent.

Customers are categorized into the following segments:

- Champions
- Loyal Customers
- Potential Loyalists
- At Risk
- Lost Customers
- Regular Customers

The dashboard displays customer segment distribution, customer metrics, and segment-based business recommendations.

### 6. Data Export
- Download filtered transaction data as CSV.
- Download customer segmentation results as CSV.

## 🛠️ Technologies Used

- **Programming Language:** Python
- **Dashboard:** Streamlit
- **Data Processing:** Pandas
- **Data Visualization:** Plotly
- **Database:** SQLite
- **Excel Support:** OpenPyXL

## 📂 Project Structure

```text
NexusIQ/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── screenshots/
    ├── business-overview.png
    ├── monthly-revenue.png
    └── customer-segmentation.png
```

The SQLite database (`nexusiq.db`) is generated automatically when the application processes a dataset.

## 📸 Dashboard Preview

### 1. Business Overview

![Business Overview](screenshots/business-overview.png)

### 2. Monthly Revenue Analysis

![Monthly Revenue Analysis](screenshots/monthly-revenue.png)

### 3. Customer Segmentation

![Customer Segmentation](screenshots/customer-segmentation.png)

## 📊 Dataset

This project uses the **Online Retail Dataset** from the UCI Machine Learning Repository.

The dataset contains retail transactions from a UK-based online retailer between December 2010 and December 2011.

- 541,909 transaction records
- 8 columns
- Customer and product information
- Invoice dates, quantities, and unit prices

Dataset source: [UCI Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail)

Download the dataset and upload the Excel file through the NexusIQ application.

## ⚙️ Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Saniyakhan8/NexusIQ.git
```

### Step 2: Navigate to the Project Folder

```bash
cd NexusIQ
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
streamlit run app.py
```

### Step 5: Upload the Dataset

Open the local URL displayed in your terminal, upload the Online Retail Excel dataset, and explore the dashboard.

## 🎯 Project Objective

The objective of NexusIQ is to demonstrate how Python, SQL, data analytics, and customer segmentation can be combined to transform raw business data into actionable insights.

This project demonstrates practical skills in data cleaning, database management, SQL querying, data visualization, and business analytics.

## 👩‍💻 Author

**Saniya Khan**

Computer Science Graduate

- GitHub: [Saniyakhan8](https://github.com/Saniyakhan8)
- LinkedIn: [Saniya Khan](https://linkedin.com/in/saniya-khan-6898b52a3)

---

*Built with Python, SQL, and Streamlit.*
