
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Afficionado Coffee Analytics",
    page_icon="☕",
    layout="wide"
)

st.title("☕ Afficionado Coffee Roasters")
st.subheader("Sales Analytics & Peak Demand Dashboard")

# ==========================================
# LOAD DATA
# ==========================================
FILE_NAME = "Afficionado Coffee Roasters.xlsx - Transactions.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(FILE_NAME)

    # Check required columns
    required_columns = [
        "transaction_id",
        "transaction_qty",
        "unit_price",
        "transaction_time",
        "store_location",
        "product_category",
        "product_detail"
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    # Convert numeric columns
    df["transaction_qty"] = pd.to_numeric(
        df["transaction_qty"], errors="coerce"
    )

    df["unit_price"] = pd.to_numeric(
        df["unit_price"], errors="coerce"
    )

    # Remove rows with invalid essential values
    df = df.dropna(
        subset=[
            "transaction_qty",
            "unit_price",
            "transaction_time",
            "store_location",
            "product_category"
        ]
    ).copy()

    # Calculate revenue
    df["Revenue"] = df["transaction_qty"] * df["unit_price"]

    # Convert transaction time
    df["transaction_time"] = pd.to_datetime(
        df["transaction_time"],
        format="%H:%M:%S",
        errors="coerce"
    )

    df = df.dropna(subset=["transaction_time"]).copy()

    # Extract hour
    df["Hour"] = df["transaction_time"].dt.hour

    return df


try:
    data = load_data()

except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()


# ==========================================
# SIDEBAR FILTERS
# ==========================================
st.sidebar.header("Dashboard Filters")

stores = sorted(data["store_location"].dropna().unique())

selected_stores = st.sidebar.multiselect(
    "Select Store",
    stores,
    default=stores
)

categories = sorted(data["product_category"].dropna().unique())

selected_categories = st.sidebar.multiselect(
    "Select Product Category",
    categories,
    default=categories
)

filtered = data[
    data["store_location"].isin(selected_stores)
    & data["product_category"].isin(selected_categories)
].copy()

if filtered.empty:
    st.warning("No data available for the selected filters.")
    st.stop()


# ==========================================
# BUSINESS OVERVIEW
# ==========================================
st.header("Business Overview")

total_quantity = filtered["transaction_qty"].sum()
total_revenue = filtered["Revenue"].sum()
total_transactions = filtered["transaction_id"].nunique()

col1, col2, col3 = st.columns(3)

col1.metric("Total Quantity Sold", f"{total_quantity:,.0f}")
col2.metric("Total Revenue", f"${total_revenue:,.2f}")
col3.metric("Total Transactions", f"{total_transactions:,.0f}")

st.divider()


# ==========================================
# 1. HOURLY DEMAND ANALYSIS
# ==========================================
st.header("1. Hourly Demand Analysis")

hourly_demand = (
    filtered.groupby("Hour")
    .agg(
        Total_Quantity=("transaction_qty", "sum"),
        Total_Revenue=("Revenue", "sum"),
        Total_Transactions=("transaction_id", "count")
    )
    .reindex(range(24), fill_value=0)
    .rename_axis("Hour")
    .reset_index()
)

st.subheader("Hourly Demand Summary")
st.dataframe(hourly_demand, use_container_width=True)

if hourly_demand["Total_Quantity"].sum() > 0:

    peak = hourly_demand.loc[
        hourly_demand["Total_Quantity"].idxmax()
    ]

    st.success(
        f"Peak Demand: {int(peak['Hour']):02d}:00 "
        f"({int(peak['Total_Quantity']):,} items sold)"
    )

# Quantity chart
st.subheader("Hourly Quantity Sold")

fig, ax = plt.subplots(figsize=(12, 5))

ax.bar(
    hourly_demand["Hour"],
    hourly_demand["Total_Quantity"]
)

ax.set_xlabel("Hour of Day")
ax.set_ylabel("Quantity Sold")
ax.set_title("Hourly Coffee Demand")
ax.set_xticks(range(24))

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# Revenue chart
st.subheader("Hourly Revenue")

st.bar_chart(
    hourly_demand.set_index("Hour")[["Total_Revenue"]]
)

st.divider()


# ==========================================
# 2. STORE-WISE SALES ANALYSIS
# ==========================================
st.header("2. Store-wise Sales Analysis")

store_summary = (
    filtered.groupby("store_location")
    .agg(
        Total_Quantity=("transaction_qty", "sum"),
        Total_Revenue=("Revenue", "sum"),
        Total_Transactions=("transaction_id", "nunique")
    )
    .reset_index()
    .sort_values("Total_Revenue", ascending=False)
)

st.dataframe(store_summary, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by Store")

    st.bar_chart(
        store_summary.set_index("store_location")[["Total_Revenue"]]
    )

with col2:
    st.subheader("Quantity by Store")

    st.bar_chart(
        store_summary.set_index("store_location")[["Total_Quantity"]]
    )

st.divider()


# ==========================================
# 3. PRODUCT CATEGORY ANALYSIS
# ==========================================
st.header("3. Product Category Analysis")

category_summary = (
    filtered.groupby("product_category")
    .agg(
        Total_Quantity=("transaction_qty", "sum"),
        Total_Revenue=("Revenue", "sum"),
        Total_Transactions=("transaction_id", "nunique")
    )
    .reset_index()
    .sort_values("Total_Revenue", ascending=False)
)

st.dataframe(category_summary, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by Category")

    st.bar_chart(
        category_summary.set_index("product_category")[["Total_Revenue"]]
    )

with col2:
    st.subheader("Quantity by Category")

    st.bar_chart(
        category_summary.set_index("product_category")[["Total_Quantity"]]
    )

st.divider()


# ==========================================
# 4. TOP 10 PRODUCTS
# ==========================================
st.header("4. Top 10 Products")

top_products = (
    filtered.groupby("product_detail")
    .agg(
        Total_Quantity=("transaction_qty", "sum"),
        Total_Revenue=("Revenue", "sum")
    )
    .reset_index()
    .sort_values("Total_Quantity", ascending=False)
    .head(10)
)

st.subheader("Top Products by Quantity")

st.bar_chart(
    top_products.set_index("product_detail")[["Total_Quantity"]]
)

st.dataframe(top_products, use_container_width=True)

st.divider()


# ==========================================
# 5. PEAK DEMAND BY STORE
# ==========================================
st.header("5. Peak Demand by Store")

store_hourly = (
    filtered.groupby(["store_location", "Hour"])
    .agg(
        Total_Quantity=("transaction_qty", "sum"),
        Total_Revenue=("Revenue", "sum")
    )
    .reset_index()
)

if not store_hourly.empty:

    peak_indices = store_hourly.groupby(
        "store_location"
    )["Total_Quantity"].idxmax()

    peak_store = store_hourly.loc[peak_indices].copy()

    peak_store["Peak_Hour"] = peak_store["Hour"].apply(
        lambda hour: f"{int(hour):02d}:00"
    )

    peak_store = peak_store.rename(
        columns={
            "store_location": "Store",
            "Total_Quantity": "Peak_Quantity",
            "Total_Revenue": "Peak_Revenue"
        }
    )

    st.subheader("Busiest Hour for Each Store")

    st.dataframe(
        peak_store[
            ["Store", "Peak_Hour", "Peak_Quantity", "Peak_Revenue"]
        ],
        use_container_width=True
    )

    st.subheader("Peak Quantity by Store")

    st.bar_chart(
        peak_store.set_index("Store")[["Peak_Quantity"]]
    )

    # Store vs hour heatmap
    st.subheader("Store vs Hour Demand Heatmap")

    heatmap_data = (
        store_hourly.pivot(
            index="store_location",
            columns="Hour",
            values="Total_Quantity"
        )
        .reindex(columns=range(24), fill_value=0)
        .fillna(0)
    )

    fig, ax = plt.subplots(figsize=(14, 5))

    image = ax.imshow(
        heatmap_data,
        aspect="auto",
        cmap="YlOrRd"
    )

    ax.set_xticks(range(24))
    ax.set_xticklabels(range(24))

    ax.set_yticks(range(len(heatmap_data.index)))
    ax.set_yticklabels(heatmap_data.index)

    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Store")
    ax.set_title("Historical Hourly Demand Heatmap")

    fig.colorbar(image, ax=ax, label="Quantity Sold")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

else:
    st.info("No store-level hourly data available.")

st.divider()


# ==========================================
# 6. HOURLY DEMAND PROFILE
# ==========================================
st.header("6. Hourly Demand Profile")

st.info(
    "This is historical demand analysis, not a future forecast. "
    "The current dataset does not contain a transaction date."
)

demand_profile = (
    filtered.groupby("Hour")["transaction_qty"]
    .sum()
    .reindex(range(24), fill_value=0)
    .rename("Quantity")
    .reset_index()
)

total_demand = demand_profile["Quantity"].sum()

if total_demand > 0:

    demand_profile["Demand_Percentage"] = (
        demand_profile["Quantity"] / total_demand * 100
    )

else:
    demand_profile["Demand_Percentage"] = 0

st.subheader("Demand Distribution by Hour")
st.dataframe(demand_profile, use_container_width=True)

st.subheader("Hourly Demand Percentage")

st.bar_chart(
    demand_profile.set_index("Hour")[["Demand_Percentage"]]
)

if total_demand > 0:

    average_hourly_demand = total_demand / 24

    busy_hours = demand_profile[
        demand_profile["Quantity"] > average_hourly_demand
    ]

    st.subheader("Hours Above Average Demand")

    st.dataframe(busy_hours, use_container_width=True)

# Download demand profile
profile_csv = demand_profile.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Hourly Demand Profile",
    data=profile_csv,
    file_name="hourly_demand_profile.csv",
    mime="text/csv"
)

st.divider()


# ==========================================
# 7. DOWNLOAD REPORTS
# ==========================================
st.header("7. Download Reports")

hourly_csv = hourly_demand.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Hourly Demand CSV",
    data=hourly_csv,
    file_name="hourly_demand_summary.csv",
    mime="text/csv"
)

store_csv = store_summary.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Store Sales CSV",
    data=store_csv,
    file_name="store_sales_summary.csv",
    mime="text/csv"
)

category_csv = category_summary.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Category Sales CSV",
    data=category_csv,
    file_name="category_sales_summary.csv",
    mime="text/csv"
)

peak_csv = peak_store.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Store Peak Demand CSV",
    data=peak_csv,
    file_name="store_peak_demand.csv",
    mime="text/csv"
)

st.divider()


# ==========================================
# 8. RAW TRANSACTION DATA
# ==========================================
st.header("8. Transaction Data")

with st.expander("View Filtered Transaction Data"):

    st.dataframe(
        filtered,
        use_container_width=True
    )

st.caption(
    "Afficionado Coffee Roasters | Historical Sales Analytics Dashboard"
)