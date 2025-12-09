import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Community Health Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# THEME TOGGLE & STYLING
# =============================================================================
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# Define colors based on the state
if st.session_state.dark_mode:
    # DARK MODE COLORS
    bg_color = "#0e1117"
    text_color = "white"
    card_bg = "#262730"
    metric_val_color = "#f0f2f6"
else:
    # LIGHT MODE COLORS
    bg_color = "#ffffff"
    text_color = "black"
    card_bg = "#f0f2f6"
    metric_val_color = "#31333F"

# Inject CSS dynamically
st.markdown(f"""
<style>
    /* Force the main app background */
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    /* Custom Metric Card Style */
    .metric-card {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    /* Streamlit's native metric container */
    .stMetric {{
        background-color: {card_bg};
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }}
    
    div[data-testid="stMetricValue"] {{
        font-size: 28px;
        font-weight: bold;
        color: {metric_val_color};
    }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA LOADING
# =============================================================================
@st.cache_data
def load_data():
    try:
        member_df = pd.read_csv('member_cleaned_from_export.csv')
        channel_df = pd.read_csv('channel_cleaned_from_export.csv')
        workspace_df = pd.read_csv('workspace_daily_from_export.csv')
        
        # 1. Clean Date
        workspace_df['date'] = pd.to_datetime(workspace_df['date'])

        
        if member_df['messages_posted'].dtype == 'object':
            member_df['messages_posted'] = member_df['messages_posted'].astype(str).str.replace(',', '')
            
        member_df['messages_posted'] = pd.to_numeric(member_df['messages_posted'], errors='coerce').fillna(0)
        member_df['days_active'] = pd.to_numeric(member_df['days_active'], errors='coerce').fillna(0)
        
        
        member_df['display_name'] = member_df['display_name'].fillna(member_df['name']).fillna("Unknown Member")

        # Create retention groups
        def get_retention_group(days):
            if days <= 5: return "0-5 days"
            elif days <= 15: return "6-15 days"
            elif days <= 30: return "16-30 days"
            else: return "30+ days"
        
        member_df['retention_group'] = member_df['days_active'].apply(get_retention_group)
        
        return member_df, channel_df, workspace_df
    except FileNotFoundError as e:
        st.error(f"❌ CSV files not found: {e}")
        st.stop()

member_df, channel_df, workspace_df = load_data()

# =============================================================================
# CALCULATE ALL METRICS (Power BI Requirements)
# =============================================================================
def calculate_metrics(member_df, channel_df, workspace_df, filtered_workspace_df):
    # MEMBER METRICS
    total_members = len(member_df['user_id'].unique())
    total_member_messages = member_df['messages_posted'].sum()
    avg_messages_per_member = total_member_messages / total_members if total_members > 0 else 0
    avg_days_active = member_df['days_active'].mean()
    high_engagement_count = member_df['high_engagement'].sum()
    pct_high_engagement = (high_engagement_count / total_members * 100) if total_members > 0 else 0
    members_with_messages = len(member_df[member_df['messages_posted'] > 0])
    pct_members_with_messages = (members_with_messages / total_members * 100) if total_members > 0 else 0
    
    # CHANNEL METRICS
    total_channels = len(channel_df['channel'].unique())
    total_channel_messages = channel_df['messages_posted'].sum()
    avg_messages_per_channel = total_channel_messages / total_channels if total_channels > 0 else 0
    total_channel_membership = channel_df['total_membership'].sum()
    
    # WORKSPACE METRICS (for filtered date range)
    peak_daily_active = filtered_workspace_df['daily_active_people'].max()
    peak_messages_per_day = filtered_workspace_df['messages_posted'].max()
    avg_daily_active = filtered_workspace_df['daily_active_people'].mean()
    avg_messages_per_day = filtered_workspace_df['messages_posted'].mean()
    total_messages_period = filtered_workspace_df['messages_posted'].sum()
    avg_engagement_ratio = filtered_workspace_df['engagement_ratio'].mean()
    latest_enabled_members = filtered_workspace_df['total_enabled_members'].iloc[-1] if len(filtered_workspace_df) > 0 else 0
    
    return {
        'total_members': total_members,
        'total_member_messages': total_member_messages,
        'avg_messages_per_member': avg_messages_per_member,
        'avg_days_active': avg_days_active,
        'high_engagement_count': high_engagement_count,
        'pct_high_engagement': pct_high_engagement,
        'members_with_messages': members_with_messages,
        'pct_members_with_messages': pct_members_with_messages,
        'total_channels': total_channels,
        'total_channel_messages': total_channel_messages,
        'avg_messages_per_channel': avg_messages_per_channel,
        'total_channel_membership': total_channel_membership,
        'peak_daily_active': peak_daily_active,
        'peak_messages_per_day': peak_messages_per_day,
        'avg_daily_active': avg_daily_active,
        'avg_messages_per_day': avg_messages_per_day,
        'total_messages_period': total_messages_period,
        'avg_engagement_ratio': avg_engagement_ratio,
        'latest_enabled_members': latest_enabled_members
    }

# =============================================================================
# HEADER & THEME TOGGLE
# =============================================================================
col1, col2 = st.columns([6, 1])
with col1:
    st.title("📊 Community Health Dashboard")
    st.markdown("**Comprehensive Analytics for Workspace Engagement**")
with col2:
    theme_button = st.button("🌓 Toggle Theme", on_click=toggle_theme)

st.divider()

# =============================================================================
# SIDEBAR FILTERS
# =============================================================================
st.sidebar.header("🔍 Filters")
st.sidebar.markdown("---")

# Date range filter
# Date range filter (robust)
min_date = workspace_df['date'].min().date()
max_date = workspace_df['date'].max().date()

date_range = st.sidebar.date_input(
    "📅 Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Normalize returned value to (start_date, end_date)
if isinstance(date_range, (list, tuple)):
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        start_date, end_date = min_date, max_date
else:
    # single date object
    start_date = end_date = date_range

mask = (workspace_df['date'].dt.date >= start_date) & (workspace_df['date'].dt.date <= end_date)
filtered_workspace_df = workspace_df.loc[mask].sort_values('date')


# Member activity filter
st.sidebar.markdown("---")
min_messages = st.sidebar.slider("📨 Min Messages Posted", 0, int(member_df['messages_posted'].max()), 0)
filtered_member_df = member_df[member_df['messages_posted'] >= min_messages]

# Calculate metrics
metrics = calculate_metrics(filtered_member_df, channel_df, workspace_df, filtered_workspace_df)

st.sidebar.markdown("---")
st.sidebar.info(f"📊 **Data Summary**\n\n- Date Range: {len(filtered_workspace_df)} days\n- Members: {metrics['total_members']:,}\n- Channels: {metrics['total_channels']:,}")

# =============================================================================
# TABS
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "👥 Members", "📢 Channels", "📊 Trends"])

# =============================================================================
# TAB 1: OVERVIEW
# =============================================================================
with tab1:
    st.header("Key Performance Indicators")
    
    # Top KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Members",
            f"{metrics['total_members']:,}",
            f"{metrics['pct_members_with_messages']:.1f}% active"
        )
    
    with col2:
        st.metric(
            "Total Messages",
            f"{metrics['total_member_messages']:,}",
            f"{metrics['avg_messages_per_member']:.1f} avg/member"
        )
    
    with col3:
        st.metric(
            "High Engagement",
            f"{metrics['high_engagement_count']:,}",
            f"{metrics['pct_high_engagement']:.1f}%"
        )
    
    with col4:
        st.metric(
            "Avg Days Active",
            f"{metrics['avg_days_active']:.1f}",
            "Retention metric"
        )
    
    with col5:
        st.metric(
            "Engagement Rate",
            f"{metrics['avg_engagement_ratio']*100:.1f}%",
            "Daily active rate"
        )
    
    st.divider()
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Member Retention Distribution")
        retention_counts = filtered_member_df['retention_group'].value_counts().reset_index()
        retention_counts.columns = ['Retention Group', 'Count']
        
        fig_retention = px.pie(
            retention_counts,
            values='Count',
            names='Retention Group',
            color_discrete_sequence=px.colors.sequential.RdBu,
            hole=0.4
        )
        fig_retention.update_traces(textposition='inside', textinfo='percent+label')
        fig_retention.update_layout(height=400)
        st.plotly_chart(fig_retention, use_container_width=True)
    
    with col2:
        st.subheader("📈 Daily Active Users Trend")
        fig_dau = px.area(
            filtered_workspace_df,
            x='date',
            y='daily_active_people',
            color_discrete_sequence=['#667eea']
        )
        fig_dau.update_layout(
            xaxis_title="Date",
            yaxis_title="Active Users",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig_dau, use_container_width=True)
    
    st.divider()
    
    # Channel & Workspace KPIs
    st.subheader("Channel & Workspace Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Channels", f"{metrics['total_channels']:,}")
    
    with col2:
        st.metric("Channel Messages", f"{metrics['total_channel_messages']:,}")
    
    with col3:
        st.metric("Peak Daily Active", f"{int(metrics['peak_daily_active']):,}")
    
    with col4:
        st.metric("Peak Messages/Day", f"{int(metrics['peak_messages_per_day']):,}")

# =============================================================================
# TAB 2: MEMBER ANALYTICS
# =============================================================================
with tab2:
    st.header("Member Engagement Analysis")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Members", f"{metrics['total_members']:,}")
    with col2:
        st.metric("Total Messages", f"{metrics['total_member_messages']:,}")
    with col3:
        st.metric("High Engagement", f"{metrics['pct_high_engagement']:.1f}%")
    with col4:
        st.metric("Active Posters", f"{metrics['pct_members_with_messages']:.1f}%")
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 20 Most Active Members")
        top_members = filtered_member_df.nlargest(20, 'messages_posted')[['display_name', 'messages_posted', 'days_active']]
        
        fig_top = px.bar(
            top_members,
            x='messages_posted',
            y='display_name',
            orientation='h',
            color='messages_posted',
            color_continuous_scale='Viridis',
            labels={'messages_posted': 'Messages Posted', 'display_name': 'Member'}
        )
        fig_top.update_layout(height=600, showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)
    
    with col2:
        st.subheader("📊 Activity vs Retention Scatter")
        fig_scatter = px.scatter(
            filtered_member_df,
            x='days_active',
            y='messages_posted',
            color='high_engagement',
            size='messages_posted',
            hover_data=['display_name'],
            color_discrete_map={0: '#cbd5e1', 1: '#10b981'},
            labels={'days_active': 'Days Active', 'messages_posted': 'Messages Posted', 'high_engagement': 'High Engagement'}
        )
        fig_scatter.update_layout(height=600)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.divider()
    
    # Distribution
    st.subheader("📈 Message Distribution")
    fig_hist = px.histogram(
        filtered_member_df,
        x='messages_posted',
        nbins=50,
        color_discrete_sequence=['#8b5cf6'],
        labels={'messages_posted': 'Messages Posted', 'count': 'Number of Members'}
    )
    fig_hist.update_layout(height=400)
    st.plotly_chart(fig_hist, use_container_width=True)

# =============================================================================
# TAB 3: CHANNEL ANALYTICS
# =============================================================================
with tab3:
    st.header("Channel Performance Analysis")
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Channels", f"{metrics['total_channels']:,}")
    with col2:
        st.metric("Total Messages", f"{metrics['total_channel_messages']:,}")
    with col3:
        st.metric("Avg Messages/Channel", f"{metrics['avg_messages_per_channel']:.0f}")
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Top 20 Channels by Volume")
        top_channels = channel_df.nlargest(20, 'messages_posted')[['name', 'messages_posted', 'total_membership']]
        
        fig_vol = px.bar(
            top_channels,
            x='name',
            y='messages_posted',
            color='messages_posted',
            color_continuous_scale='Reds',
            labels={'messages_posted': 'Messages', 'name': 'Channel'}
        )
        fig_vol.update_layout(
            height=500,
            xaxis_tickangle=-45,
            showlegend=False
        )
        st.plotly_chart(fig_vol, use_container_width=True)
    
    with col2:
        st.subheader("💬 Deep Engagement Channels")
        st.caption("Channels with highest avg messages per posting member")
        
        deep_channels = channel_df.nlargest(20, 'avg_messages_per_user')[['name', 'avg_messages_per_user', 'members_who_posted']]
        
        fig_deep = px.bar(
            deep_channels,
            x='name',
            y='avg_messages_per_user',
            color='avg_messages_per_user',
            color_continuous_scale='Greens',
            labels={'avg_messages_per_user': 'Avg Msgs/User', 'name': 'Channel'}
        )
        fig_deep.update_layout(
            height=500,
            xaxis_tickangle=-45,
            showlegend=False
        )
        st.plotly_chart(fig_deep, use_container_width=True)
    
    st.divider()
    
    # Scatter
    st.subheader("📊 Channel Size vs Activity")
    fig_channel_scatter = px.scatter(
        channel_df,
        x='total_membership',
        y='messages_posted',
        size='messages_posted',
        hover_name='name',
        color='avg_messages_per_user',
        color_continuous_scale='Plasma',
        labels={
            'total_membership': 'Total Members',
            'messages_posted': 'Total Messages',
            'avg_messages_per_user': 'Engagement Depth'
        }
    )
    fig_channel_scatter.update_layout(height=500)
    st.plotly_chart(fig_channel_scatter, use_container_width=True)

# =============================================================================
# TAB 4: WORKSPACE TRENDS
# =============================================================================
with tab4:
    st.header("Workspace Activity Trends")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Peak Daily Active", f"{int(metrics['peak_daily_active']):,}")
    with col2:
        st.metric("Peak Messages/Day", f"{int(metrics['peak_messages_per_day']):,}")
    with col3:
        st.metric("Avg Daily Active", f"{metrics['avg_daily_active']:.0f}")
    with col4:
        st.metric("Avg Messages/Day", f"{metrics['avg_messages_per_day']:.0f}")
    
    st.divider()
    
    # Line Charts
    st.subheader("📈 Daily Active People")
    fig_dap = px.line(
        filtered_workspace_df,
        x='date',
        y='daily_active_people',
        markers=True,
        color_discrete_sequence=['#3b82f6']
    )
    fig_dap.update_layout(
        xaxis_title="Date",
        yaxis_title="Active People",
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig_dap, use_container_width=True)
    
    st.subheader("💬 Messages Posted Per Day")
    fig_msgs = px.area(
        filtered_workspace_df,
        x='date',
        y='messages_posted',
        color_discrete_sequence=['#ec4899']
    )
    fig_msgs.update_layout(
        xaxis_title="Date",
        yaxis_title="Messages",
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig_msgs, use_container_width=True)
    
    st.subheader("📊 Engagement Ratio Trend")
    st.caption("Daily Active People / Total Enabled Members")
    
    fig_ratio = px.line(
        filtered_workspace_df,
        x='date',
        y='engagement_ratio',
        markers=True,
        color_discrete_sequence=['#10b981']
    )
    fig_ratio.update_layout(
        xaxis_title="Date",
        yaxis_title="Engagement Ratio",
        height=400,
        hovermode='x unified',
        yaxis=dict(tickformat='.1%')
    )
    #fig_ratio.update_yaxis=dict(tickformat='.1%')
    
    st.plotly_chart(fig_ratio, use_container_width=True)
    
    st.divider()
    
    # Summary Stats
    st.subheader("📋 Period Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Messages (Period)", f"{int(metrics['total_messages_period']):,}")
    with col2:
        st.metric("Avg Engagement Rate", f"{metrics['avg_engagement_ratio']*100:.2f}%")
    with col3:
        st.metric("Latest Enabled Members", f"{int(metrics['latest_enabled_members']):,}")

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"📅 Data from {min_date} to {max_date}")
with col2:
    st.caption("📊 Built with Streamlit & Plotly")
with col3:
    st.caption(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
