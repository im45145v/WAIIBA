import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="OpenSSH Security Analytics Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for business analytics theme
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #0e1117;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d2137 100%);
        border-radius: 10px;
        padding: 20px;
        border-left: 4px solid #00d4ff;
        margin: 10px 0;
    }
    
    /* Header styling */
    .dashboard-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-bottom: 3px solid #e94560;
    }
    
    /* KPI metric styling */
    .kpi-value {
        font-size: 36px;
        font-weight: bold;
        color: #00d4ff;
    }
    
    .kpi-label {
        font-size: 14px;
        color: #8892b0;
        text-transform: uppercase;
    }
    
    /* Alert styling */
    .alert-critical {
        background-color: rgba(233, 69, 96, 0.2);
        border-left: 4px solid #e94560;
        padding: 10px;
        border-radius: 5px;
    }
    
    .alert-warning {
        background-color: rgba(255, 193, 7, 0.2);
        border-left: 4px solid #ffc107;
        padding: 10px;
        border-radius: 5px;
    }
    
    .alert-success {
        background-color: rgba(0, 212, 255, 0.2);
        border-left: 4px solid #00d4ff;
        padding: 10px;
        border-radius: 5px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1a2e;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Table styling */
    .dataframe {
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Color scheme for business analytics
COLORS = {
    'primary': '#00d4ff',
    'secondary': '#e94560',
    'success': '#00ff88',
    'warning': '#ffc107',
    'danger': '#ff4757',
    'info': '#5352ed',
    'background': '#0e1117',
    'card_bg': '#1a1a2e',
    'text': '#ffffff',
    'text_muted': '#8892b0'
}

# Plotly template for consistent styling
PLOTLY_TEMPLATE = {
    'layout': {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#ffffff'},
        'xaxis': {'gridcolor': 'rgba(255,255,255,0.1)', 'zerolinecolor': 'rgba(255,255,255,0.1)'},
        'yaxis': {'gridcolor': 'rgba(255,255,255,0.1)', 'zerolinecolor': 'rgba(255,255,255,0.1)'}
    }
}


@st.cache_data
def load_data():
    """Load and preprocess the OpenSSH log data from GitHub URL."""
    url = "https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log_structured.csv"
    df = pd.read_csv(url)
    
    # Create datetime column
    df['DateTime'] = pd.to_datetime('2023-' + df['Date'] + '-' + df['Day'].astype(str) + ' ' + df['Time'], 
                                    format='%Y-%b-%d %H:%M:%S', errors='coerce')
    
    # Extract IP addresses from Content
    def extract_ip(content):
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, str(content))
        return ips[0] if ips else None
    
    df['IP_Address'] = df['Content'].apply(extract_ip)
    
    # Categorize events
    def categorize_event(content):
        content = str(content).lower()
        if 'failed password' in content:
            return 'Failed Password'
        elif 'invalid user' in content:
            return 'Invalid User'
        elif 'authentication failure' in content:
            return 'Auth Failure'
        elif 'disconnect' in content:
            return 'Disconnect'
        elif 'accepted' in content:
            return 'Successful Login'
        elif 'break-in attempt' in content:
            return 'Break-in Attempt'
        elif 'session opened' in content:
            return 'Session Opened'
        elif 'session closed' in content:
            return 'Session Closed'
        else:
            return 'Other'
    
    df['Event_Category'] = df['Content'].apply(categorize_event)
    
    # Extract username attempts
    def extract_username(content):
        patterns = [
            r'for (?:invalid user )?(\w+) from',
            r'user[= ](\w+)',
            r'Invalid user (\w+)'
        ]
        content = str(content)
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None
    
    df['Username'] = df['Content'].apply(extract_username)
    
    # Determine severity
    def get_severity(category):
        severity_map = {
            'Break-in Attempt': 'Critical',
            'Failed Password': 'High',
            'Invalid User': 'High',
            'Auth Failure': 'Medium',
            'Disconnect': 'Low',
            'Successful Login': 'Info',
            'Session Opened': 'Info',
            'Session Closed': 'Info',
            'Other': 'Low'
        }
        return severity_map.get(category, 'Low')
    
    df['Severity'] = df['Event_Category'].apply(get_severity)
    
    return df


@st.cache_data
def load_ip_features():
    """Load IP features data."""
    try:
        ip_features = pd.read_csv("OpenSSH_ip_features.csv", index_col=0)
        return ip_features
    except FileNotFoundError:
        return None


def render_header():
    """Render the dashboard header."""
    st.markdown("""
    <div class="dashboard-header">
        <h1 style="color: #ffffff; margin-bottom: 5px;">🔒 OpenSSH Security Analytics Dashboard</h1>
        <p style="color: #8892b0; margin: 0;">Real-time security monitoring and business intelligence for SSH access patterns</p>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_cards(df):
    """Render KPI metric cards."""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_events = len(df)
    unique_ips = df['IP_Address'].nunique()
    failed_attempts = len(df[df['Event_Category'].isin(['Failed Password', 'Invalid User', 'Auth Failure'])])
    critical_events = len(df[df['Severity'] == 'Critical'])
    success_rate = (len(df[df['Event_Category'] == 'Successful Login']) / total_events * 100) if total_events > 0 else 0
    
    with col1:
        st.metric(
            label="📊 Total Events",
            value=f"{total_events:,}",
            delta="All logged events"
        )
    
    with col2:
        st.metric(
            label="🌐 Unique IPs",
            value=f"{unique_ips}",
            delta="Source addresses"
        )
    
    with col3:
        st.metric(
            label="⚠️ Failed Attempts",
            value=f"{failed_attempts:,}",
            delta=f"{(failed_attempts/total_events*100):.1f}% of total" if total_events > 0 else "0%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="🚨 Critical Events",
            value=f"{critical_events}",
            delta="Break-in attempts",
            delta_color="inverse" if critical_events > 0 else "off"
        )
    
    with col5:
        st.metric(
            label="✅ Success Rate",
            value=f"{success_rate:.2f}%",
            delta="Successful logins"
        )


def render_event_timeline(df):
    """Render event timeline chart."""
    st.subheader("📈 Event Timeline Analysis")
    
    # Group by time and event category
    timeline_df = df.groupby([df['DateTime'].dt.floor('1min'), 'Event_Category']).size().reset_index(name='Count')
    
    fig = px.area(
        timeline_df, 
        x='DateTime', 
        y='Count', 
        color='Event_Category',
        title='SSH Events Over Time',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_event_distribution(df):
    """Render event category distribution charts."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Event Category Distribution")
        category_counts = df['Event_Category'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=category_counts.index,
            values=category_counts.values,
            hole=0.4,
            marker=dict(colors=px.colors.qualitative.Set2),
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            showlegend=False,
            height=400,
            annotations=[dict(text='Events', x=0.5, y=0.5, font_size=16, showarrow=False, font_color='white')]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🔴 Severity Distribution")
        severity_counts = df['Severity'].value_counts()
        
        severity_colors = {
            'Critical': '#ff4757',
            'High': '#ff6b6b',
            'Medium': '#ffc107',
            'Low': '#00d4ff',
            'Info': '#00ff88'
        }
        
        fig = go.Figure(data=[go.Bar(
            x=severity_counts.index,
            y=severity_counts.values,
            marker_color=[severity_colors.get(s, '#8892b0') for s in severity_counts.index],
            text=severity_counts.values,
            textposition='auto'
        )])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Severity Level'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Count'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_ip_analysis(df):
    """Render IP address analysis charts."""
    st.subheader("🌐 IP Address Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top attacking IPs
        ip_counts = df['IP_Address'].value_counts().head(15)
        
        fig = go.Figure(data=[go.Bar(
            x=ip_counts.values,
            y=ip_counts.index,
            orientation='h',
            marker=dict(
                color=ip_counts.values,
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title='Events')
            ),
            text=ip_counts.values,
            textposition='auto'
        )])
        
        fig.update_layout(
            title='Top 15 IP Addresses by Event Count',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Number of Events'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='IP Address', autorange='reversed'),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # IP activity breakdown
        ip_event_breakdown = df.groupby(['IP_Address', 'Event_Category']).size().reset_index(name='Count')
        top_ips = df['IP_Address'].value_counts().head(10).index.tolist()
        ip_event_breakdown = ip_event_breakdown[ip_event_breakdown['IP_Address'].isin(top_ips)]
        
        fig = px.sunburst(
            ip_event_breakdown,
            path=['IP_Address', 'Event_Category'],
            values='Count',
            title='IP Address Event Breakdown (Top 10 IPs)',
            color='Count',
            color_continuous_scale='RdYlGn_r'
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_username_analysis(df):
    """Render username attack analysis."""
    st.subheader("👤 Username Attack Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Most targeted usernames
        username_counts = df['Username'].dropna().value_counts().head(20)
        
        fig = go.Figure(data=[go.Bar(
            x=username_counts.index,
            y=username_counts.values,
            marker=dict(
                color=username_counts.values,
                colorscale='Viridis',
                showscale=True
            ),
            text=username_counts.values,
            textposition='auto'
        )])
        
        fig.update_layout(
            title='Top 20 Targeted Usernames',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Username', tickangle=45),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Attack Attempts'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Username wordcloud-style treemap
        username_df = df['Username'].dropna().value_counts().head(30).reset_index()
        username_df.columns = ['Username', 'Count']
        
        fig = px.treemap(
            username_df,
            path=['Username'],
            values='Count',
            title='Username Attack Distribution',
            color='Count',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_hourly_heatmap(df):
    """Render hourly activity heatmap."""
    st.subheader("🕐 Hourly Activity Heatmap")
    
    # Create hour and event category pivot
    df['Hour'] = df['DateTime'].dt.hour
    df['Minute'] = df['DateTime'].dt.minute
    
    # Heatmap by hour and event category
    heatmap_data = df.groupby(['Hour', 'Event_Category']).size().unstack(fill_value=0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='YlOrRd',
        text=heatmap_data.values,
        texttemplate='%{text}',
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='Event Activity by Hour and Category',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(title='Event Category', tickangle=45),
        yaxis=dict(title='Hour of Day'),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_security_gauge(df):
    """Render security score gauges."""
    st.subheader("🛡️ Security Metrics Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    total = len(df)
    critical = len(df[df['Severity'] == 'Critical'])
    high = len(df[df['Severity'] == 'High'])
    
    # Calculate threat score (0-100)
    threat_score = min(100, (critical * 10 + high * 2) / total * 100) if total > 0 else 0
    security_score = 100 - threat_score
    
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=security_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Security Score", 'font': {'color': 'white'}},
            delta={'reference': 80, 'increasing': {'color': "#00ff88"}, 'decreasing': {'color': "#ff4757"}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': 'white'},
                'bar': {'color': "#00d4ff"},
                'bgcolor': "rgba(0,0,0,0)",
                'steps': [
                    {'range': [0, 40], 'color': '#ff4757'},
                    {'range': [40, 70], 'color': '#ffc107'},
                    {'range': [70, 100], 'color': '#00ff88'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Attack intensity gauge
        attack_rate = (len(df[df['Event_Category'].isin(['Failed Password', 'Invalid User'])]) / total * 100) if total > 0 else 0
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=attack_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Attack Intensity (%)", 'font': {'color': 'white'}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': 'white'},
                'bar': {'color': "#e94560"},
                'bgcolor': "rgba(0,0,0,0)",
                'steps': [
                    {'range': [0, 30], 'color': '#00ff88'},
                    {'range': [30, 60], 'color': '#ffc107'},
                    {'range': [60, 100], 'color': '#ff4757'}
                ]
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Unique attacker gauge
        unique_attackers = df['IP_Address'].nunique()
        max_attackers = 50  # Reference value
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=unique_attackers,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Unique Attackers", 'font': {'color': 'white'}},
            gauge={
                'axis': {'range': [0, max_attackers], 'tickcolor': 'white'},
                'bar': {'color': "#5352ed"},
                'bgcolor': "rgba(0,0,0,0)",
                'steps': [
                    {'range': [0, 15], 'color': '#00ff88'},
                    {'range': [15, 30], 'color': '#ffc107'},
                    {'range': [30, max_attackers], 'color': '#ff4757'}
                ]
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)


def render_event_template_analysis(df):
    """Render event template analysis."""
    st.subheader("📋 Event Template Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Event template frequency
        template_counts = df['EventId'].value_counts().head(15)
        
        fig = go.Figure(data=[go.Bar(
            x=template_counts.values,
            y=template_counts.index,
            orientation='h',
            marker=dict(
                color=template_counts.values,
                colorscale='Blues',
                showscale=True
            ),
            text=template_counts.values,
            textposition='auto'
        )])
        
        fig.update_layout(
            title='Top 15 Event Templates by Frequency',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Frequency'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Event ID', autorange='reversed'),
            height=450
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Event template statistics
        st.markdown("### Event Statistics")
        st.markdown(f"""
        - **Total Event Types:** {df['EventId'].nunique()}
        - **Most Common:** {df['EventId'].mode().values[0] if len(df['EventId'].mode()) > 0 else 'N/A'}
        - **Least Common:** {df['EventId'].value_counts().idxmin() if len(df) > 0 else 'N/A'}
        """)
        
        # Component breakdown
        st.markdown("### Component Analysis")
        component_counts = df['Component'].value_counts()
        for comp, count in component_counts.items():
            st.markdown(f"- **{comp}:** {count:,} events ({count/len(df)*100:.1f}%)")


def render_anomaly_analysis(df, ip_features):
    """Render anomaly analysis charts."""
    st.subheader("🔍 Anomaly Detection Analysis")
    
    if ip_features is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            # Anomaly scatter plot
            fig = px.scatter(
                ip_features.reset_index(),
                x='total_events',
                y='unique_event_ids',
                color=ip_features['anomaly'].map({1: 'Normal', -1: 'Anomaly'}),
                size='duration_sec',
                hover_data=['IP'],
                title='IP Behavior Analysis (Events vs Unique Types)',
                color_discrete_map={'Normal': '#00d4ff', 'Anomaly': '#e94560'}
            )
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Total Events'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Unique Event IDs'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Anomaly score distribution
            fig = px.histogram(
                ip_features,
                x='anomaly_score',
                nbins=30,
                title='Anomaly Score Distribution',
                color_discrete_sequence=['#00d4ff']
            )
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Anomaly Score'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Count'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Anomalous IPs table
        st.markdown("### 🚨 Detected Anomalous IPs")
        anomalous = ip_features[ip_features['anomaly'] == -1].sort_values('total_events', ascending=False)
        if len(anomalous) > 0:
            st.dataframe(
                anomalous[['total_events', 'unique_event_ids', 'duration_sec', 'anomaly_score']].head(10),
                use_container_width=True
            )
        else:
            st.info("No anomalous IPs detected in the dataset.")
    else:
        st.warning("IP features data not available. Run anomaly detection preprocessing to enable this feature.")


def render_attack_patterns(df):
    """Render attack pattern analysis."""
    st.subheader("⚔️ Attack Pattern Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Attack sequence analysis
        failed_df = df[df['Event_Category'].isin(['Failed Password', 'Invalid User', 'Auth Failure'])]
        attack_by_ip = failed_df.groupby('IP_Address').agg({
            'LineId': 'count',
            'Username': lambda x: x.nunique()
        }).reset_index()
        attack_by_ip.columns = ['IP_Address', 'Total_Attacks', 'Unique_Usernames']
        attack_by_ip = attack_by_ip.nlargest(15, 'Total_Attacks')
        
        fig = px.scatter(
            attack_by_ip,
            x='Total_Attacks',
            y='Unique_Usernames',
            size='Total_Attacks',
            hover_data=['IP_Address'],
            title='Attack Pattern: Total Attacks vs Username Variety',
            color='Total_Attacks',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Total Attack Attempts'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Unique Usernames Tried'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Attack timeline
        failed_df['Minute'] = failed_df['DateTime'].dt.floor('1min')
        attack_timeline = failed_df.groupby('Minute').size().reset_index(name='Attacks')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=attack_timeline['Minute'],
            y=attack_timeline['Attacks'],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#e94560'),
            marker=dict(size=4)
        ))
        
        fig.update_layout(
            title='Attack Frequency Over Time',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Time'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Attack Count'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_correlation_matrix(df):
    """Render correlation analysis."""
    st.subheader("📊 Correlation Analysis")
    
    # Create numeric features for correlation
    numeric_df = df.copy()
    numeric_df['Event_Category_Code'] = pd.Categorical(numeric_df['Event_Category']).codes
    numeric_df['Severity_Code'] = pd.Categorical(numeric_df['Severity']).codes
    numeric_df['Hour'] = numeric_df['DateTime'].dt.hour
    
    # IP event counts
    ip_counts = numeric_df['IP_Address'].value_counts()
    numeric_df['IP_Event_Count'] = numeric_df['IP_Address'].map(ip_counts)
    
    # Select numeric columns for correlation
    corr_cols = ['Pid', 'Hour', 'Event_Category_Code', 'Severity_Code', 'IP_Event_Count']
    corr_matrix = numeric_df[corr_cols].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=['PID', 'Hour', 'Event Category', 'Severity', 'IP Event Count'],
        y=['PID', 'Hour', 'Event Category', 'Severity', 'IP Event Count'],
        colorscale='RdBu',
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 12},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='Feature Correlation Matrix',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_detailed_logs(df):
    """Render detailed log viewer."""
    st.subheader("📜 Detailed Log Viewer")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_category = st.selectbox(
            "Filter by Event Category",
            ["All"] + list(df['Event_Category'].unique())
        )
    
    with col2:
        selected_severity = st.selectbox(
            "Filter by Severity",
            ["All"] + list(df['Severity'].unique())
        )
    
    with col3:
        selected_ip = st.selectbox(
            "Filter by IP Address",
            ["All"] + list(df['IP_Address'].dropna().unique()[:50])
        )
    
    filtered_df = df.copy()
    
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df['Event_Category'] == selected_category]
    
    if selected_severity != "All":
        filtered_df = filtered_df[filtered_df['Severity'] == selected_severity]
    
    if selected_ip != "All":
        filtered_df = filtered_df[filtered_df['IP_Address'] == selected_ip]
    
    st.markdown(f"**Showing {len(filtered_df):,} of {len(df):,} records**")
    
    display_cols = ['DateTime', 'Component', 'Event_Category', 'Severity', 'IP_Address', 'Username', 'Content']
    st.dataframe(
        filtered_df[display_cols].head(100),
        use_container_width=True,
        height=400
    )


def render_sidebar_filters(df):
    """Render sidebar with filters and info."""
    st.sidebar.markdown("## 🔧 Dashboard Controls")
    
    # Data info
    st.sidebar.markdown("### 📊 Data Overview")
    st.sidebar.info(f"""
    - **Records:** {len(df):,}
    - **Unique IPs:** {df['IP_Address'].nunique()}
    - **Event Types:** {df['Event_Category'].nunique()}
    - **Time Range:** {df['DateTime'].min().strftime('%H:%M') if pd.notna(df['DateTime'].min()) else 'N/A'} - {df['DateTime'].max().strftime('%H:%M') if pd.notna(df['DateTime'].max()) else 'N/A'}
    """)
    
    # Navigation
    st.sidebar.markdown("### 🧭 Navigation")
    page = st.sidebar.radio(
        "Select Dashboard View",
        [
            "🏠 Executive Summary",
            "📈 Time Analysis",
            "🌐 IP Intelligence",
            "👤 User Analysis",
            "🔍 Anomaly Detection",
            "⚔️ Attack Patterns",
            "📜 Log Explorer"
        ]
    )
    
    # Quick stats
    st.sidebar.markdown("### ⚡ Quick Stats")
    
    critical = len(df[df['Severity'] == 'Critical'])
    high = len(df[df['Severity'] == 'High'])
    
    if critical > 0:
        st.sidebar.error(f"🚨 {critical} Critical Events")
    if high > 0:
        st.sidebar.warning(f"⚠️ {high} High Severity Events")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="text-align: center; color: #8892b0; font-size: 12px;">
        <p>OpenSSH Security Analytics</p>
        <p>Data Source: LogHub OpenSSH Dataset</p>
    </div>
    """, unsafe_allow_html=True)
    
    return page


def main():
    """Main application entry point."""
    # Load data
    with st.spinner("Loading security data..."):
        df = load_data()
        ip_features = load_ip_features()
    
    # Render header
    render_header()
    
    # Render sidebar and get selected page
    page = render_sidebar_filters(df)
    
    # Render selected page content
    if page == "🏠 Executive Summary":
        render_kpi_cards(df)
        st.markdown("---")
        render_security_gauge(df)
        st.markdown("---")
        render_event_distribution(df)
        st.markdown("---")
        render_event_template_analysis(df)
    
    elif page == "📈 Time Analysis":
        render_kpi_cards(df)
        st.markdown("---")
        render_event_timeline(df)
        st.markdown("---")
        render_hourly_heatmap(df)
    
    elif page == "🌐 IP Intelligence":
        render_kpi_cards(df)
        st.markdown("---")
        render_ip_analysis(df)
        st.markdown("---")
        render_correlation_matrix(df)
    
    elif page == "👤 User Analysis":
        render_kpi_cards(df)
        st.markdown("---")
        render_username_analysis(df)
    
    elif page == "🔍 Anomaly Detection":
        render_kpi_cards(df)
        st.markdown("---")
        render_anomaly_analysis(df, ip_features)
    
    elif page == "⚔️ Attack Patterns":
        render_kpi_cards(df)
        st.markdown("---")
        render_attack_patterns(df)
    
    elif page == "📜 Log Explorer":
        render_kpi_cards(df)
        st.markdown("---")
        render_detailed_logs(df)


if __name__ == "__main__":
    main()
