"""
OpenSSH Security Analytics Dashboard
=====================================
A comprehensive business analytics dashboard for analyzing OpenSSH log data.
Built with Streamlit, Pandas, and Plotly for interactive data visualization.

Data Source: LogHub OpenSSH Dataset
URL: https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log_structured.csv
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from datetime import datetime

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="OpenSSH Security Analytics",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM STYLING - BUSINESS ANALYTICS THEME
# =============================================================================
st.markdown("""
<style>
    /* Dark business theme */
    .stApp {
        background-color: #0f1419;
    }
    
    /* Header card */
    .header-card {
        background: linear-gradient(135deg, #1a2634 0%, #0d1b2a 100%);
        padding: 2rem;
        border-radius: 12px;
        border-left: 5px solid #00d9ff;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .header-title {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .header-subtitle {
        color: #8899a6;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Metric cards */
    .metric-container {
        background: linear-gradient(135deg, #1a2634 0%, #0d1b2a 100%);
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 4px solid #00d9ff;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    /* Section headers */
    .section-header {
        color: #00d9ff;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #1a2634;
    }
    
    /* Alert boxes */
    .alert-danger {
        background: rgba(239, 68, 68, 0.15);
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .alert-warning {
        background: rgba(245, 158, 11, 0.15);
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .alert-success {
        background: rgba(34, 197, 94, 0.15);
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0d1b2a;
    }
    
    /* Info box */
    .info-box {
        background: #1a2634;
        padding: 1rem;
        border-radius: 8px;
        color: #8899a6;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# COLOR PALETTE
# =============================================================================
COLORS = {
    'primary': '#00d9ff',
    'secondary': '#7c3aed',
    'success': '#22c55e',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    'bg_dark': '#0f1419',
    'bg_card': '#1a2634',
    'text_primary': '#ffffff',
    'text_secondary': '#8899a6'
}

# =============================================================================
# DATA LOADING
# =============================================================================
@st.cache_data(ttl=3600)
def load_openssh_data():
    """
    Load OpenSSH log data from the LogHub GitHub repository.
    Includes data preprocessing and feature extraction.
    """
    url = "https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log_structured.csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None
    
    # Parse datetime
    df['DateTime'] = pd.to_datetime(
        '2023-' + df['Date'] + '-' + df['Day'].astype(str) + ' ' + df['Time'],
        format='%Y-%b-%d %H:%M:%S',
        errors='coerce'
    )
    
    # Extract hour for time-based analysis
    df['Hour'] = df['DateTime'].dt.hour
    
    # Extract IP addresses
    df['IP_Address'] = df['Content'].apply(extract_ip_address)
    
    # Categorize events
    df['Event_Type'] = df['Content'].apply(categorize_event)
    
    # Extract usernames
    df['Username'] = df['Content'].apply(extract_username)
    
    # Assign severity levels
    df['Severity'] = df['Event_Type'].apply(get_severity_level)
    
    return df


def extract_ip_address(content):
    """Extract IP address from log content."""
    pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    match = re.search(pattern, str(content))
    return match.group(0) if match else None


def categorize_event(content):
    """Categorize SSH events based on content."""
    content_lower = str(content).lower()
    
    if 'break-in attempt' in content_lower:
        return 'Break-in Attempt'
    elif 'failed password' in content_lower:
        return 'Failed Password'
    elif 'invalid user' in content_lower:
        return 'Invalid User'
    elif 'authentication failure' in content_lower:
        return 'Auth Failure'
    elif 'accepted' in content_lower:
        return 'Successful Login'
    elif 'session opened' in content_lower:
        return 'Session Opened'
    elif 'session closed' in content_lower:
        return 'Session Closed'
    elif 'disconnect' in content_lower:
        return 'Disconnect'
    elif 'connection closed' in content_lower:
        return 'Connection Closed'
    else:
        return 'Other'


def extract_username(content):
    """Extract username from log content."""
    patterns = [
        r'for (?:invalid user )?(\w+) from',
        r'user[= ](\w+)',
        r'Invalid user (\w+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, str(content))
        if match:
            return match.group(1)
    return None


def get_severity_level(event_type):
    """Map event types to severity levels."""
    severity_map = {
        'Break-in Attempt': 'Critical',
        'Failed Password': 'High',
        'Invalid User': 'High',
        'Auth Failure': 'Medium',
        'Disconnect': 'Low',
        'Connection Closed': 'Low',
        'Successful Login': 'Info',
        'Session Opened': 'Info',
        'Session Closed': 'Info',
        'Other': 'Low'
    }
    return severity_map.get(event_type, 'Low')


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================
def create_kpi_metrics(df):
    """Display key performance indicators."""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_events = len(df)
    unique_ips = df['IP_Address'].nunique()
    failed_attempts = len(df[df['Event_Type'].isin(['Failed Password', 'Invalid User', 'Auth Failure'])])
    critical_events = len(df[df['Severity'] == 'Critical'])
    success_count = len(df[df['Event_Type'] == 'Successful Login'])
    
    with col1:
        st.metric("📊 Total Events", f"{total_events:,}")
    
    with col2:
        st.metric("🌐 Unique IPs", f"{unique_ips}")
    
    with col3:
        st.metric("⚠️ Failed Attempts", f"{failed_attempts:,}")
    
    with col4:
        st.metric("🚨 Critical Events", f"{critical_events}")
    
    with col5:
        st.metric("✅ Successful Logins", f"{success_count}")


def create_event_distribution_chart(df):
    """Create donut chart for event type distribution."""
    event_counts = df['Event_Type'].value_counts().reset_index()
    event_counts.columns = ['Event_Type', 'Count']
    
    fig = px.pie(
        event_counts,
        values='Count',
        names='Event_Type',
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    return fig


def create_severity_bar_chart(df):
    """Create horizontal bar chart for severity distribution."""
    severity_order = ['Critical', 'High', 'Medium', 'Low', 'Info']
    severity_counts = df['Severity'].value_counts().reindex(severity_order, fill_value=0)
    
    colors = {
        'Critical': COLORS['danger'],
        'High': '#ff6b6b',
        'Medium': COLORS['warning'],
        'Low': COLORS['info'],
        'Info': COLORS['success']
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=severity_counts.values,
            y=severity_counts.index,
            orientation='h',
            marker_color=[colors[s] for s in severity_counts.index],
            text=severity_counts.values,
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='Count',
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='',
            gridcolor='rgba(255,255,255,0.1)'
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    
    return fig


def create_timeline_chart(df):
    """Create area chart showing events over time."""
    timeline = df.groupby([df['DateTime'].dt.floor('1min'), 'Event_Type']).size().reset_index(name='Count')
    
    fig = px.area(
        timeline,
        x='DateTime',
        y='Count',
        color='Event_Type',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='Time',
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Event Count',
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        height=400
    )
    
    return fig


def create_hourly_heatmap(df):
    """Create heatmap of events by hour and event type."""
    heatmap_data = df.groupby(['Hour', 'Event_Type']).size().unstack(fill_value=0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='YlOrRd',
        hoverongaps=False,
        hovertemplate='Hour: %{y}<br>Event: %{x}<br>Count: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(title='Event Type', tickangle=45),
        yaxis=dict(title='Hour of Day'),
        margin=dict(l=20, r=20, t=40, b=100),
        height=450
    )
    
    return fig


def create_top_ips_chart(df):
    """Create bar chart of top IP addresses by event count."""
    ip_counts = df['IP_Address'].value_counts().head(10).reset_index()
    ip_counts.columns = ['IP_Address', 'Count']
    
    fig = go.Figure(data=[
        go.Bar(
            x=ip_counts['Count'],
            y=ip_counts['IP_Address'],
            orientation='h',
            marker=dict(
                color=ip_counts['Count'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title='Count')
            ),
            text=ip_counts['Count'],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Events: %{x}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='Number of Events',
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            title='',
            autorange='reversed'
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    return fig


def create_ip_sunburst(df):
    """Create sunburst chart for IP and event type breakdown."""
    ip_events = df.groupby(['IP_Address', 'Event_Type']).size().reset_index(name='Count')
    top_ips = df['IP_Address'].value_counts().head(8).index.tolist()
    ip_events_filtered = ip_events[ip_events['IP_Address'].isin(top_ips)]
    
    fig = px.sunburst(
        ip_events_filtered,
        path=['IP_Address', 'Event_Type'],
        values='Count',
        color='Count',
        color_continuous_scale='RdYlGn_r'
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    return fig


def create_username_chart(df):
    """Create bar chart of most targeted usernames."""
    username_counts = df['Username'].dropna().value_counts().head(15).reset_index()
    username_counts.columns = ['Username', 'Count']
    
    fig = px.bar(
        username_counts,
        x='Username',
        y='Count',
        color='Count',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='Username',
            tickangle=45,
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            title='Attack Count',
            gridcolor='rgba(255,255,255,0.1)'
        ),
        margin=dict(l=20, r=20, t=40, b=100),
        height=400
    )
    
    return fig


def create_username_treemap(df):
    """Create treemap of username attack distribution."""
    username_counts = df['Username'].dropna().value_counts().head(20).reset_index()
    username_counts.columns = ['Username', 'Count']
    
    fig = px.treemap(
        username_counts,
        path=['Username'],
        values='Count',
        color='Count',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    return fig


def create_security_gauge(value, title, color):
    """Create a gauge chart for security metrics."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'color': 'white', 'size': 16}},
        number={'font': {'color': 'white'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': 'white', 'tickfont': {'color': 'white'}},
            'bar': {'color': color},
            'bgcolor': 'rgba(0,0,0,0)',
            'steps': [
                {'range': [0, 40], 'color': 'rgba(34, 197, 94, 0.3)'},
                {'range': [40, 70], 'color': 'rgba(245, 158, 11, 0.3)'},
                {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.3)'}
            ]
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=20, r=20, t=60, b=20),
        height=250
    )
    
    return fig


def create_attack_scatter(df):
    """Create scatter plot of attack patterns."""
    failed_events = df[df['Event_Type'].isin(['Failed Password', 'Invalid User', 'Auth Failure'])]
    
    attack_stats = failed_events.groupby('IP_Address').agg({
        'LineId': 'count',
        'Username': lambda x: x.nunique()
    }).reset_index()
    attack_stats.columns = ['IP_Address', 'Total_Attacks', 'Unique_Usernames']
    attack_stats = attack_stats.nlargest(20, 'Total_Attacks')
    
    fig = px.scatter(
        attack_stats,
        x='Total_Attacks',
        y='Unique_Usernames',
        size='Total_Attacks',
        color='Total_Attacks',
        hover_name='IP_Address',
        color_continuous_scale='Reds',
        size_max=40
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='Total Attack Attempts',
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            title='Unique Usernames Tried',
            gridcolor='rgba(255,255,255,0.1)'
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    return fig


def create_event_template_chart(df):
    """Create bar chart for event templates."""
    template_counts = df['EventId'].value_counts().head(12).reset_index()
    template_counts.columns = ['EventId', 'Count']
    
    fig = go.Figure(data=[
        go.Bar(
            x=template_counts['Count'],
            y=template_counts['EventId'],
            orientation='h',
            marker=dict(
                color=template_counts['Count'],
                colorscale='Blues',
                showscale=True
            ),
            text=template_counts['Count'],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='Frequency',
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            title='Event Template ID',
            autorange='reversed'
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    return fig


# =============================================================================
# SIDEBAR
# =============================================================================
def render_sidebar(df):
    """Render the sidebar with navigation and data info."""
    st.sidebar.markdown("## 🔐 SSH Analytics")
    st.sidebar.markdown("---")
    
    # Data overview
    st.sidebar.markdown("### 📊 Data Overview")
    st.sidebar.markdown(f"""
    - **Records:** {len(df):,}
    - **Unique IPs:** {df['IP_Address'].nunique()}
    - **Event Types:** {df['Event_Type'].nunique()}
    - **Time Range:** {df['DateTime'].min().strftime('%H:%M') if pd.notna(df['DateTime'].min()) else 'N/A'} to {df['DateTime'].max().strftime('%H:%M') if pd.notna(df['DateTime'].max()) else 'N/A'}
    """)
    
    st.sidebar.markdown("---")
    
    # Page navigation
    st.sidebar.markdown("### 🧭 Navigation")
    page = st.sidebar.radio(
        "Select View",
        [
            "📊 Executive Summary",
            "📈 Time Analysis",
            "🌐 IP Analysis",
            "👤 User Analysis",
            "⚔️ Attack Patterns",
            "📋 Event Templates",
            "🔍 Log Explorer"
        ],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # Alert summary
    st.sidebar.markdown("### ⚡ Alert Summary")
    critical = len(df[df['Severity'] == 'Critical'])
    high = len(df[df['Severity'] == 'High'])
    
    if critical > 0:
        st.sidebar.error(f"🚨 {critical} Critical Events")
    if high > 0:
        st.sidebar.warning(f"⚠️ {high} High Severity Events")
    if critical == 0 and high == 0:
        st.sidebar.success("✅ No Critical/High Events")
    
    st.sidebar.markdown("---")
    
    # Data source info
    st.sidebar.markdown("### ℹ️ Data Source")
    st.sidebar.caption("LogHub OpenSSH Dataset")
    st.sidebar.caption("2,000 SSH log entries")
    
    return page


# =============================================================================
# PAGE RENDERERS
# =============================================================================
def render_executive_summary(df):
    """Render the executive summary page."""
    # KPI Metrics
    create_kpi_metrics(df)
    
    st.markdown("---")
    
    # Security gauges
    st.markdown("### 🛡️ Security Metrics")
    
    total = len(df)
    critical = len(df[df['Severity'] == 'Critical'])
    high = len(df[df['Severity'] == 'High'])
    failed = len(df[df['Event_Type'].isin(['Failed Password', 'Invalid User'])])
    
    threat_score = min(100, (critical * 10 + high * 2) / total * 100) if total > 0 else 0
    attack_intensity = (failed / total * 100) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = create_security_gauge(100 - threat_score, "Security Score", COLORS['success'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = create_security_gauge(attack_intensity, "Attack Intensity", COLORS['danger'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        unique_ips = df['IP_Address'].nunique()
        ip_score = min(100, unique_ips * 2)
        fig = create_security_gauge(ip_score, "Unique Attackers", COLORS['warning'])
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Distribution charts
    st.markdown("### 📊 Event Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Event Types")
        fig = create_event_distribution_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Severity Levels")
        fig = create_severity_bar_chart(df)
        st.plotly_chart(fig, use_container_width=True)


def render_time_analysis(df):
    """Render the time analysis page."""
    create_kpi_metrics(df)
    
    st.markdown("---")
    
    # Timeline
    st.markdown("### 📈 Event Timeline")
    fig = create_timeline_chart(df)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Hourly heatmap
    st.markdown("### 🕐 Hourly Activity Heatmap")
    fig = create_hourly_heatmap(df)
    st.plotly_chart(fig, use_container_width=True)


def render_ip_analysis(df):
    """Render the IP analysis page."""
    create_kpi_metrics(df)
    
    st.markdown("---")
    
    st.markdown("### 🌐 IP Address Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Top IP Addresses")
        fig = create_top_ips_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### IP Event Breakdown")
        fig = create_ip_sunburst(df)
        st.plotly_chart(fig, use_container_width=True)


def render_user_analysis(df):
    """Render the user analysis page."""
    create_kpi_metrics(df)
    
    st.markdown("---")
    
    st.markdown("### 👤 Username Attack Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Most Targeted Usernames")
        fig = create_username_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Username Distribution")
        fig = create_username_treemap(df)
        st.plotly_chart(fig, use_container_width=True)


def render_attack_patterns(df):
    """Render the attack patterns page."""
    create_kpi_metrics(df)
    
    st.markdown("---")
    
    st.markdown("### ⚔️ Attack Pattern Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Attack Behavior by IP")
        fig = create_attack_scatter(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Attack statistics
        st.markdown("#### Attack Statistics")
        
        failed_events = df[df['Event_Type'].isin(['Failed Password', 'Invalid User', 'Auth Failure'])]
        
        st.markdown(f"""
        <div class="info-box">
            <h4 style="color: #00d9ff; margin-top: 0;">Attack Summary</h4>
            <ul style="color: #ffffff;">
                <li><strong>Total Failed Attempts:</strong> {len(failed_events):,}</li>
                <li><strong>Unique Attacking IPs:</strong> {failed_events['IP_Address'].nunique()}</li>
                <li><strong>Unique Targeted Users:</strong> {failed_events['Username'].nunique()}</li>
                <li><strong>Most Attacked User:</strong> {failed_events['Username'].mode().values[0] if len(failed_events['Username'].dropna()) > 0 else 'N/A'}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def render_event_templates(df):
    """Render the event templates page."""
    create_kpi_metrics(df)
    
    st.markdown("---")
    
    st.markdown("### 📋 Event Template Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Top Event Templates")
        fig = create_event_template_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Template Statistics")
        st.markdown(f"""
        <div class="info-box">
            <ul style="color: #ffffff;">
                <li><strong>Total Templates:</strong> {df['EventId'].nunique()}</li>
                <li><strong>Most Common:</strong> {df['EventId'].mode().values[0] if len(df['EventId'].mode()) > 0 else 'N/A'}</li>
                <li><strong>Components:</strong> {df['Component'].nunique()}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### Component Breakdown")
        component_counts = df['Component'].value_counts()
        for comp, count in component_counts.items():
            pct = count / len(df) * 100
            st.markdown(f"**{comp}:** {count:,} ({pct:.1f}%)")


def render_log_explorer(df):
    """Render the log explorer page."""
    create_kpi_metrics(df)
    
    st.markdown("---")
    
    st.markdown("### 🔍 Log Explorer")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        event_filter = st.selectbox(
            "Filter by Event Type",
            ["All"] + list(df['Event_Type'].unique())
        )
    
    with col2:
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["All"] + list(df['Severity'].unique())
        )
    
    with col3:
        ip_options = ["All"] + list(df['IP_Address'].dropna().unique()[:50])
        ip_filter = st.selectbox("Filter by IP", ip_options)
    
    # Apply filters
    filtered_df = df.copy()
    
    if event_filter != "All":
        filtered_df = filtered_df[filtered_df['Event_Type'] == event_filter]
    
    if severity_filter != "All":
        filtered_df = filtered_df[filtered_df['Severity'] == severity_filter]
    
    if ip_filter != "All":
        filtered_df = filtered_df[filtered_df['IP_Address'] == ip_filter]
    
    st.markdown(f"**Showing {len(filtered_df):,} of {len(df):,} records**")
    
    # Display data
    display_cols = ['DateTime', 'Event_Type', 'Severity', 'IP_Address', 'Username', 'Content']
    st.dataframe(
        filtered_df[display_cols].head(100),
        use_container_width=True,
        height=500
    )


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    """Main application entry point."""
    
    # Load data
    with st.spinner("Loading OpenSSH log data..."):
        df = load_openssh_data()
    
    if df is None:
        st.error("Failed to load data. Please check your internet connection.")
        return
    
    # Header
    st.markdown("""
    <div class="header-card">
        <h1 class="header-title">🔐 OpenSSH Security Analytics Dashboard</h1>
        <p class="header-subtitle">Real-time security monitoring and business intelligence for SSH access patterns</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar and navigation
    page = render_sidebar(df)
    
    # Render selected page
    if page == "📊 Executive Summary":
        render_executive_summary(df)
    elif page == "📈 Time Analysis":
        render_time_analysis(df)
    elif page == "🌐 IP Analysis":
        render_ip_analysis(df)
    elif page == "👤 User Analysis":
        render_user_analysis(df)
    elif page == "⚔️ Attack Patterns":
        render_attack_patterns(df)
    elif page == "📋 Event Templates":
        render_event_templates(df)
    elif page == "🔍 Log Explorer":
        render_log_explorer(df)


if __name__ == "__main__":
    main()
