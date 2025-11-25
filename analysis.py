"""
analysis.py
============

This script performs data preprocessing, feature engineering and anomaly detection
on the OpenSSH log dataset.  It loads the structured CSV file, extracts IP
addresses from the log contents, aggregates features per IP address and fits
an Isolation Forest model to detect anomalous IPs.  The resulting feature
matrix with anomaly labels is saved to a CSV file for further analysis or
visualisation.

Usage:
    python analysis.py

Dependencies:
    pandas, numpy, scikit-learn, regex (built into Python), and matplotlib (optional
    if you wish to generate charts from this script).

The script is written for Python 3.10 or higher.
"""

import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def extract_ip(content: str) -> str:
    """Extract the first IPv4 address from a log message.

    Args:
        content: The log message string.

    Returns:
        The first IP address found in the string or None if no IP is present.
    """
    ip_regex = r"(?:\d{1,3}\.){3}\d{1,3}"
    match = re.search(ip_regex, str(content))
    return match.group(0) if match else None


def load_dataset(path: Path) -> pd.DataFrame:
    """Load the OpenSSH structured log CSV into a DataFrame and add an IP column.

    Args:
        path: Path to the CSV file.

    Returns:
        DataFrame with an additional IP column.
    """
    df = pd.read_csv(path)
    df["IP"] = df["Content"].apply(extract_ip)
    return df


def aggregate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-IP features from the raw log DataFrame.

    The features include total number of events, number of unique event IDs,
    average message length and duration of the session based on the first and
    last occurrences of the IP.

    Args:
        df: Raw DataFrame with an 'IP' column.

    Returns:
        Aggregated DataFrame indexed by IP with feature columns.
    """
    # Convert day and time into a datetime object.  Since the dataset does not
    # include the year, we assume an arbitrary year (e.g., 2023).  Month names
    # are stored in the 'Date' column.
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
    }
    # Build a datetime column
    df = df.copy()
    df["DateTime"] = df.apply(
        lambda r: datetime(
            2023,
            month_map.get(str(r["Date"]).strip(), 1),
            int(r["Day"]),
            int(str(r["Time"]).split(":")[0]),
            int(str(r["Time"]).split(":")[1]),
            int(str(r["Time"]).split(":")[2])
        ),
        axis=1,
    )

    # Compute aggregated metrics per IP
    ip_group = df.dropna(subset=["IP"]).groupby("IP").agg(
        total_events=("IP", "size"),
        unique_event_ids=("EventId", "nunique"),
        avg_msg_length=("Content", lambda x: x.str.len().mean()),
        first_ts=("DateTime", "min"),
        last_ts=("DateTime", "max"),
    )
    ip_group["duration_sec"] = (
        ip_group["last_ts"] - ip_group["first_ts"]
    ).dt.total_seconds().fillna(0)
    return ip_group


def detect_anomalies(features: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """Fit an Isolation Forest to detect anomalies based on feature vectors.

    Args:
        features: DataFrame with numerical features for anomaly detection.
        contamination: The proportion of anomalies expected in the data.

    Returns:
        The input DataFrame with additional 'anomaly' and 'anomaly_score' columns.
    """
    model = IsolationForest(contamination=contamination, random_state=42)
    X = features[["total_events", "unique_event_ids", "duration_sec"]].fillna(0)
    model.fit(X)
    features["anomaly"] = model.predict(X)
    # Higher anomaly_score means more normal; negative values are anomalies.
    features["anomaly_score"] = model.decision_function(X)
    return features


def main():
    data_path = Path(__file__).resolve().parent / "OpenSSH_2k.log_structured.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")
    # Load data and compute features
    raw_df = load_dataset(data_path)
    features = aggregate_features(raw_df)
    features_with_anomaly = detect_anomalies(features)
    # Save aggregated features to CSV
    out_path = Path(__file__).resolve().parent / "OpenSSH_ip_features.csv"
    features_with_anomaly.to_csv(out_path)
    print(f"Aggregated features saved to {out_path}")


if __name__ == "__main__":
    main()