import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def load_data():
    """
    Load the preprocessed IP features and raw log data.
    Returns a tuple of (ip_features_df, raw_df).
    """
    ip_features = pd.read_csv("OpenSSH_ip_features.csv", index_col=0)
    raw_df = pd.read_csv("OpenSSH_2k.log_structured.csv")
    return ip_features, raw_df

def show_summary(ip_features: pd.DataFrame, raw_df: pd.DataFrame):
    st.header("Dataset Summary")
    total_events = len(raw_df)
    unique_ips = ip_features.shape[0]
    num_anomalies = (ip_features["anomaly"] == -1).sum()
    st.write(f"Total log events: **{total_events}**")
    st.write(f"Unique IP addresses: **{unique_ips}**")
    st.write(f"Anomalous IPs detected: **{num_anomalies}**")
    st.subheader("Top 10 IPs by event count")
    top_ips = ip_features.sort_values("total_events", ascending=False).head(10)
    st.dataframe(top_ips[['total_events', 'unique_event_ids', 'duration_sec', 'anomaly']])

def plot_event_distribution(ip_features: pd.DataFrame):
    st.subheader("Event Count Distribution")
    top_n = st.slider("Select number of top IPs to display", 5, 30, 10)
    top_ips = ip_features.sort_values("total_events", ascending=False).head(top_n)
    fig, ax = plt.subplots()
    ax.bar(top_ips.index.astype(str), top_ips["total_events"])
    ax.set_xlabel("IP Address")
    ax.set_ylabel("Total Events")
    ax.set_title(f"Top {top_n} IPs by Event Count")
    plt.xticks(rotation=90)
    st.pyplot(fig)

def plot_anomaly_scatter(ip_features: pd.DataFrame):
    st.subheader("Anomaly Scatter Plot")
    fig, ax = plt.subplots()
    normal = ip_features[ip_features["anomaly"] == 1]
    ax.scatter(normal["total_events"], normal["unique_event_ids"], label="Normal", alpha=0.7)
    anomalies = ip_features[ip_features["anomaly"] == -1]
    ax.scatter(anomalies["total_events"], anomalies["unique_event_ids"], marker='x', label="Anomaly", alpha=0.9)
    ax.set_xlabel("Total Events")
    ax.set_ylabel("Unique Event IDs")
    ax.set_title("Event Count vs Unique Events (Anomaly Detection)")
    ax.legend()
    st.pyplot(fig)

def main():
    st.title("OpenSSH API Usage Analytics & Anomaly Detection")
    st.write("This dashboard analyses real-world OpenSSH log data to detect abnormal API usage patterns and help improve API management.")
    ip_features, raw_df = load_data()
    page = st.sidebar.selectbox(
        "Select a view",
        ("Summary", "Event Distribution", "Anomaly Scatter"),
    )
    if page == "Summary":
        show_summary(ip_features, raw_df)
    elif page == "Event Distribution":
        plot_event_distribution(ip_features)
    elif page == "Anomaly Scatter":
        plot_anomaly_scatter(ip_features)

if __name__ == "__main__":
    main()
