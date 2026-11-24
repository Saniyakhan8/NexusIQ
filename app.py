import hashlib
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(page_title="NexusIQ", page_icon="📊", layout="wide")

st.title("📊 NexusIQ")
st.subheader("Intelligent Business Decision & Prediction Platform")
st.write(
    "Transform business data into meaningful insights "
    "and smarter business decisions."
)


# =====================================================
# 2. SQLITE DATABASE CONFIGURATION
# =====================================================

DB_PATH = Path(__file__).resolve().parent / "nexusiq.db"
TABLE_NAME = "cleaned_transactions"


def get_sql_connection():
    """Create a connection to the local NexusIQ SQLite database."""
    return sqlite3.connect(DB_PATH)


def run_sql(query, params=()):
    """Run a SQL query and return the result as a DataFrame."""
    with get_sql_connection() as connection:
        return pd.read_sql_query(query, connection, params=params)


# =====================================================
# 3. DATASET UPLOAD
# =====================================================

uploaded_file = st.file_uploader(
    "📁 Upload your business dataset",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("Upload your Online Retail dataset to begin.")
    st.stop()

try:
    file_bytes = uploaded_file.getvalue()

    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

except Exception as e:
    st.error(f"Unable to read dataset: {e}")
    st.stop()

st.success("Dataset uploaded successfully!")


# =====================================================
# 4. DATASET OVERVIEW
# =====================================================

st.header("📋 Dataset Overview")

col1, col2, col3 = st.columns(3)
col1.metric("Total Records", f"{len(df):,}")
col2.metric("Total Columns", f"{len(df.columns):,}")
col3.metric("Missing Values", f"{int(df.isna().sum().sum()):,}")

with st.expander("View Dataset Preview"):
    preview_df = df.head(10).copy()

    for col in preview_df.columns:
        if (
            pd.api.types.is_object_dtype(preview_df[col])
            or isinstance(preview_df[col].dtype, pd.CategoricalDtype)
        ):
            preview_df[col] = preview_df[col].astype("string")

    st.dataframe(preview_df, width="stretch", hide_index=True)

with st.expander("View Data Summary"):
    summary = df.describe(include="all").transpose().astype("string")
    st.dataframe(summary, width="stretch")


# =====================================================
# 5. REQUIRED COLUMN VALIDATION
# =====================================================

required_columns = [
    "InvoiceNo", "StockCode", "Description", "Quantity",
    "InvoiceDate", "UnitPrice", "CustomerID", "Country"
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error(f"Missing required columns: {missing_columns}")
    st.stop()


# =====================================================
# 6. DATA CLEANING
# =====================================================

st.header("🧹 Data Cleaning")

clean_df = df.copy()
clean_df["InvoiceDate"] = pd.to_datetime(
    clean_df["InvoiceDate"], errors="coerce"
)
clean_df["Quantity"] = pd.to_numeric(
    clean_df["Quantity"], errors="coerce"
)
clean_df["UnitPrice"] = pd.to_numeric(
    clean_df["UnitPrice"], errors="coerce"
)

clean_df = clean_df[
    (~clean_df["InvoiceNo"].astype("string").str.startswith("C", na=False))
    & (clean_df["Quantity"] > 0)
    & (clean_df["UnitPrice"] > 0)
    & (clean_df["InvoiceDate"].notna())
].copy()

clean_df["Revenue"] = clean_df["Quantity"] * clean_df["UnitPrice"]

st.write(f"Original records: **{len(df):,}**")
st.write(f"Valid transactions: **{len(clean_df):,}**")
st.write(f"Records removed: **{len(df) - len(clean_df):,}**")

if clean_df.empty:
    st.warning("No valid transactions found.")
    st.stop()


# =====================================================
# 7. SAVE CLEANED DATA TO SQLITE
# =====================================================

st.header("🗄️ SQL Database")

dataset_signature = hashlib.sha256(file_bytes).hexdigest()

if st.session_state.get("database_signature") != dataset_signature:
    try:
        with st.spinner("Saving cleaned transactions to the SQLite database..."):
            with get_sql_connection() as connection:
                clean_df.to_sql(
                    TABLE_NAME,
                    connection,
                    if_exists="replace",
                    index=False
                )

        st.session_state["database_signature"] = dataset_signature
        st.success("Cleaned transactions saved to the NexusIQ SQLite database.")

    except Exception as e:
        st.error(f"Could not save data to SQLite: {e}")
        st.stop()

try:
    database_rows = run_sql(
        f"SELECT COUNT(*) AS total_rows FROM {TABLE_NAME}"
    ).iloc[0]["total_rows"]
except Exception as e:
    st.error(f"Could not read the SQLite database: {e}")
    st.stop()

db_col1, db_col2 = st.columns(2)
db_col1.metric("Database", "nexusiq.db")
db_col2.metric("Transactions stored in SQL", f"{int(database_rows):,}")

st.caption(
    "The SQLite database file is created in the same folder as app.py."
)


# =====================================================
# 8. INTERACTIVE FILTERS
# =====================================================

st.header("🔎 Explore Your Business Data")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    countries = (
        ["All Countries"]
        + sorted(clean_df["Country"].dropna().astype(str).unique().tolist())
    )
    selected_country = st.selectbox("Select Country", countries)

with filter_col2:
    min_date = clean_df["InvoiceDate"].min().date()
    max_date = clean_df["InvoiceDate"].max().date()
    selected_dates = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# Build parameterized SQL filters.
sql_conditions = []
sql_params = []

if selected_country != "All Countries":
    sql_conditions.append("Country = ?")
    sql_params.append(selected_country)

if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        sql_conditions.append("date(InvoiceDate) >= date(?)")
        sql_conditions.append("date(InvoiceDate) <= date(?)")
        sql_params.extend([start_date.isoformat(), end_date.isoformat()])
    elif len(selected_dates) == 1:
        selected_date = selected_dates[0]
        sql_conditions.append("date(InvoiceDate) = date(?)")
        sql_params.append(selected_date.isoformat())

where_clause = ""
if sql_conditions:
    where_clause = " WHERE " + " AND ".join(sql_conditions)

# Retain filtered transaction rows for the CSV download.
filtered_df = clean_df.copy()

if selected_country != "All Countries":
    filtered_df = filtered_df[
        filtered_df["Country"].astype(str) == selected_country
    ]

if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_df = filtered_df[
            (filtered_df["InvoiceDate"].dt.date >= start_date)
            & (filtered_df["InvoiceDate"].dt.date <= end_date)
        ]
    elif len(selected_dates) == 1:
        selected_date = selected_dates[0]
        filtered_df = filtered_df[
            filtered_df["InvoiceDate"].dt.date == selected_date
        ]

if filtered_df.empty:
    st.warning("No transactions found for these filters.")
    st.stop()


# =====================================================
# 9. SQL-POWERED BUSINESS OVERVIEW
# =====================================================

st.header("📌 Business Overview")
st.caption("Metrics below are calculated using SQL queries on SQLite.")

try:
    business_metrics = run_sql(
        f"""
        SELECT
            COALESCE(SUM(Revenue), 0) AS total_revenue,
            COUNT(DISTINCT InvoiceNo) AS total_orders,
            COUNT(DISTINCT CustomerID) AS total_customers,
            COALESCE(SUM(Quantity), 0) AS total_units
        FROM {TABLE_NAME}
        {where_clause}
        """,
        sql_params
    ).iloc[0]
except Exception as e:
    st.error(f"SQL business overview query failed: {e}")
    st.stop()

total_revenue = float(business_metrics["total_revenue"])
total_orders = int(business_metrics["total_orders"])
total_customers = int(business_metrics["total_customers"])
total_units = float(business_metrics["total_units"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"£{total_revenue:,.2f}")
col2.metric("Total Orders", f"{total_orders:,}")
col3.metric("Unique Customers", f"{total_customers:,}")
col4.metric("Units Sold", f"{total_units:,.0f}")

st.caption(
    f"Showing {len(filtered_df):,} valid transactions after applying filters."
)


# =====================================================
# 10. MONTHLY REVENUE ANALYSIS USING SQL
# =====================================================

st.header("📅 Monthly Revenue Analysis")

monthly_sales = run_sql(
    f"""
    SELECT
        strftime('%Y-%m', InvoiceDate) AS Month,
        SUM(Revenue) AS Revenue
    FROM {TABLE_NAME}
    {where_clause}
    GROUP BY strftime('%Y-%m', InvoiceDate)
    ORDER BY Month
    """,
    sql_params
)

if not monthly_sales.empty:
    monthly_sales["InvoiceDate"] = pd.to_datetime(
        monthly_sales["Month"] + "-01", errors="coerce"
    )
    fig_monthly = px.line(
        monthly_sales,
        x="InvoiceDate",
        y="Revenue",
        markers=True,
        title="Monthly Revenue Trend"
    )
    fig_monthly.update_layout(
        xaxis_title="Month",
        yaxis_title="Revenue (£)",
        xaxis=dict(tickformat="%b %Y")
    )
    st.plotly_chart(fig_monthly, width="stretch")
else:
    st.info("No monthly revenue data is available for these filters.")


# =====================================================
# 11. TOP 10 PRODUCTS USING SQL
# =====================================================

st.header("🏆 Top 10 Products")

product_sales = run_sql(
    f"""
    SELECT
        COALESCE(Description, 'Unknown Product') AS Description,
        SUM(Revenue) AS Revenue
    FROM {TABLE_NAME}
    {where_clause}
    GROUP BY COALESCE(Description, 'Unknown Product')
    ORDER BY Revenue DESC
    LIMIT 10
    """,
    sql_params
)

if not product_sales.empty:
    fig_products = px.bar(
        product_sales,
        x="Revenue",
        y="Description",
        orientation="h",
        title="Top 10 Products by Revenue"
    )
    fig_products.update_layout(
        xaxis_title="Revenue (£)",
        yaxis_title="Product",
        yaxis={"categoryorder": "total ascending"}
    )
    st.plotly_chart(fig_products, width="stretch")
else:
    st.info("No product sales data is available for these filters.")


# =====================================================
# 12. COUNTRY SALES ANALYSIS USING SQL
# =====================================================

st.header("🌍 Sales by Country")

country_sales = run_sql(
    f"""
    SELECT Country, SUM(Revenue) AS Revenue
    FROM {TABLE_NAME}
    {where_clause}
    GROUP BY Country
    ORDER BY Revenue DESC
    LIMIT 10
    """,
    sql_params
)

if not country_sales.empty:
    fig_country = px.bar(
        country_sales,
        x="Country",
        y="Revenue",
        title="Top 10 Countries by Revenue"
    )
    fig_country.update_layout(
        xaxis_title="Country",
        yaxis_title="Revenue (£)"
    )
    st.plotly_chart(fig_country, width="stretch")
else:
    st.info("No country sales data is available for these filters.")


# =====================================================
# 13. RFM CUSTOMER SEGMENTATION USING SQL + PYTHON
# =====================================================

st.header("👥 RFM Customer Segmentation")
st.write(
    "SQL calculates customer-level purchase metrics; Python assigns "
    "the customer segments using Recency, Frequency and Monetary scores."
)

snapshot_date = filtered_df["InvoiceDate"].max() + pd.Timedelta(days=1)
snapshot_text = snapshot_date.strftime("%Y-%m-%d %H:%M:%S")

rfm_conditions = list(sql_conditions)
rfm_conditions.append("CustomerID IS NOT NULL")
rfm_where_clause = " WHERE " + " AND ".join(rfm_conditions)

try:
    rfm = run_sql(
        f"""
        SELECT
            CustomerID,
            CAST(
                julianday(?) - julianday(MAX(InvoiceDate))
                AS INTEGER
            ) AS Recency,
            COUNT(DISTINCT InvoiceNo) AS Frequency,
            SUM(Revenue) AS Monetary
        FROM {TABLE_NAME}
        {rfm_where_clause}
        GROUP BY CustomerID
        """,
        [snapshot_text] + sql_params
    )
except Exception as e:
    st.error(f"SQL RFM query failed: {e}")
    rfm = pd.DataFrame()

if rfm.empty:
    st.warning("No customers with Customer IDs were found for RFM analysis.")
elif len(rfm) < 5:
    st.warning("At least five customers are needed for five-level RFM scoring.")
else:
    rfm["R_Score"] = pd.qcut(
        rfm["Recency"].rank(method="first"),
        q=5,
        labels=[5, 4, 3, 2, 1]
    ).astype(int)

    rfm["F_Score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str)
        + rfm["F_Score"].astype(str)
        + rfm["M_Score"].astype(str)
    )

    def assign_segment(row):
        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 3 and f >= 4:
            return "Loyal Customers"
        elif r >= 4 and f >= 2:
            return "Potential Loyalists"
        elif r <= 2 and f >= 3:
            return "At Risk"
        elif r <= 2 and f <= 2:
            return "Lost Customers"
        return "Regular Customers"

    rfm["Segment"] = rfm.apply(assign_segment, axis=1)

    st.subheader("📊 Customer Segmentation Overview")
    total_rfm_customers = len(rfm)
    champions = (rfm["Segment"] == "Champions").sum()
    loyal = (rfm["Segment"] == "Loyal Customers").sum()
    at_risk = (rfm["Segment"] == "At Risk").sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Customers", f"{total_rfm_customers:,}")
    col2.metric("Champions", f"{champions:,}")
    col3.metric("Loyal Customers", f"{loyal:,}")
    col4.metric("At Risk", f"{at_risk:,}")

    st.subheader("Customer Segment Distribution")
    segment_summary = (
        rfm["Segment"]
        .value_counts()
        .rename_axis("Segment")
        .reset_index(name="Customers")
    )

    fig_segments = px.pie(
        segment_summary,
        names="Segment",
        values="Customers",
        title="Customer Distribution by Segment",
        hole=0.4
    )
    st.plotly_chart(fig_segments, width="stretch")

    st.subheader("💡 Business Recommendations")
    recommendations = {
        "Champions": (
            "Reward these customers with loyalty benefits, "
            "exclusive offers and early access to new products."
        ),
        "Loyal Customers": (
            "Encourage repeat purchases through loyalty programs "
            "and personalised product recommendations."
        ),
        "Potential Loyalists": (
            "Build stronger relationships using targeted offers "
            "and membership incentives."
        ),
        "At Risk": (
            "Reach out with personalised offers and reminders "
            "to encourage customers to return."
        ),
        "Lost Customers": (
            "Consider reactivation campaigns and special discounts "
            "to win back inactive customers."
        ),
        "Regular Customers": (
            "Use relevant promotions and recommendations "
            "to increase purchase frequency."
        )
    }

    for segment, recommendation in recommendations.items():
        count = (rfm["Segment"] == segment).sum()
        if count > 0:
            with st.expander(f"{segment} — {count:,} customers"):
                st.write(recommendation)

    st.subheader("📋 Customer RFM Details")
    rfm_display = rfm.sort_values("Monetary", ascending=False)
    st.dataframe(rfm_display, width="stretch", hide_index=True)

    rfm_csv = rfm.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download RFM Customer Report",
        data=rfm_csv,
        file_name="nexusiq_rfm_report.csv",
        mime="text/csv"
    )


# =====================================================
# 14. SQL QUERY EXAMPLES
# =====================================================

st.header("💻 SQL Query Examples")
st.write(
    "Examples of SQL statements used by NexusIQ to retrieve "
    "business insights from the SQLite database."
)

with st.expander("View SQL queries"):
    st.markdown("**1. Business metrics**")
    st.code(
        """
SELECT
    SUM(Revenue) AS total_revenue,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    COUNT(DISTINCT CustomerID) AS total_customers,
    SUM(Quantity) AS total_units
FROM cleaned_transactions;
        """,
        language="sql"
    )

    st.markdown("**2. Monthly revenue**")
    st.code(
        """
SELECT
    strftime('%Y-%m', InvoiceDate) AS Month,
    SUM(Revenue) AS Revenue
FROM cleaned_transactions
GROUP BY Month
ORDER BY Month;
        """,
        language="sql"
    )

    st.markdown("**3. Top 10 products**")
    st.code(
        """
SELECT
    Description,
    SUM(Revenue) AS Revenue
FROM cleaned_transactions
GROUP BY Description
ORDER BY Revenue DESC
LIMIT 10;
        """,
        language="sql"
    )

    st.markdown("**4. Customer purchase metrics for RFM**")
    st.code(
        """
SELECT
    CustomerID,
    MAX(InvoiceDate) AS LastPurchaseDate,
    COUNT(DISTINCT InvoiceNo) AS Frequency,
    SUM(Revenue) AS Monetary
FROM cleaned_transactions
WHERE CustomerID IS NOT NULL
GROUP BY CustomerID;
        """,
        language="sql"
    )


# =====================================================
# 15. DOWNLOAD FILTERED DATA
# =====================================================

st.header("📥 Download Filtered Dataset")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Filtered Data",
    data=csv_data,
    file_name="nexusiq_filtered_data.csv",
    mime="text/csv"
)


# =====================================================
# 16. FOOTER
# =====================================================

st.divider()
st.caption("NexusIQ | Intelligent Business Decision & Prediction Platform")
