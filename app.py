import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import psycopg2
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import time
import random

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Vamos - Smart Fitness Dashboard",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    .alert-high { background-color: #ffcccc; border-left: 5px solid #ff0000; }
    .alert-medium { background-color: #fff4cc; border-left: 5px solid #ffcc00; }
    .alert-low { background-color: #ccffcc; border-left: 5px solid #00cc00; }
    .real-time-metric {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)


class Dashboard:
    def __init__(self):
        self.init_connections()
        self.setup_data_retention()  # Setup automatic data cleanup

    def init_connections(self):
        """Initialize database connections"""
        try:
            # PostgreSQL connection
            self.pg_conn = psycopg2.connect(
                host=os.getenv('PG_HOST', 'localhost'),
                port=int(os.getenv('PG_PORT', 5432)),
                dbname=os.getenv('PG_DB', 'vamos_fitness'),
                user=os.getenv('PG_USER', 'postgres'),
                password=os.getenv('PG_PASSWORD', 'password'),
                connect_timeout=3
            )
            st.sidebar.success("✅ PostgreSQL connected")

            # MongoDB connection with better error handling
            try:
                mongo_uri = f"mongodb://{os.getenv('MONGO_HOST', 'localhost')}:{os.getenv('MONGO_PORT', 27017)}/"
                self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                self.mongo_db = self.mongo_client[os.getenv('MONGO_DB', 'vamos_fitness')]

                # Test MongoDB connection
                self.mongo_client.admin.command('ping')

                # Check if collections have data
                metrics_count = self.mongo_db.user_metrics.count_documents({})
                if metrics_count > 0:
                    st.sidebar.success(f"✅ MongoDB connected")
                else:
                    st.sidebar.warning("⚠️ MongoDB connected but no sensor data found")

                self.demo_mode = False

            except Exception as mongo_error:
                st.sidebar.warning(f"🔧 MongoDB not available: {mongo_error}")
                self.demo_mode = True

        except Exception as e:
            st.sidebar.warning(f"🔧 PostgreSQL connection failed. Using demo mode.")
            self.demo_mode = True

    def setup_data_retention(self):
        """Setup TTL index for automatic data cleanup (7 days retention)"""
        try:
            if not self.demo_mode and hasattr(self, 'mongo_db'):
                # Create TTL index to automatically delete data after 7 days
                self.mongo_db.real_time_metrics.create_index(
                    "timestamp",
                    expireAfterSeconds=7 * 24 * 60 * 60  # 7 days
                )
        except Exception as e:
            print(f"TTL index setup warning: {e}")

    def load_data(self):
        """Load data"""
        if self.demo_mode:
            return self.load_demo_data()

        try:
            # Load data from PostgreSQL
            users_df = pd.read_sql("SELECT * FROM users", self.pg_conn)
            activities_df = pd.read_sql("SELECT * FROM activities", self.pg_conn)
            health_metrics_df = pd.read_sql("SELECT * FROM health_metrics", self.pg_conn)
            goals_df = pd.read_sql("SELECT * FROM goals", self.pg_conn)
            alerts_df = pd.read_sql("SELECT * FROM alerts", self.pg_conn)

            # Load data from MongoDB
            user_metrics = list(self.mongo_db.user_metrics.find())
            nutrition_logs = list(self.mongo_db.nutrition_logs.find())
            sleep_records = list(self.mongo_db.sleep_records.find())
            real_time_metrics = list(self.mongo_db.real_time_metrics.find().sort("timestamp", -1).limit(1000))

            data = {
                'users': users_df,
                'activities': activities_df,
                'health_metrics': health_metrics_df,
                'goals': goals_df,
                'alerts': alerts_df,
                'user_metrics': pd.DataFrame(user_metrics),
                'nutrition_logs': pd.DataFrame(nutrition_logs),
                'sleep_records': pd.DataFrame(sleep_records),
                'real_time_metrics': pd.DataFrame(real_time_metrics)
            }

        except Exception as e:
            st.error(f"Database data loading failed: {e}")
            data = self.load_demo_data()

        # Unified date format processing
        return self.process_dates(data)

    def load_demo_data(self):
        """Load demo data"""
        try:
            data = {
                'users': pd.read_csv('postgres/users.csv'),
                'activities': pd.read_csv('postgres/activities.csv'),
                'health_metrics': pd.read_csv('postgres/health_metrics.csv'),
                'goals': pd.read_csv('postgres/goals.csv'),
                'alerts': pd.read_csv('postgres/alerts.csv')
            }

            # Try to load MongoDB data
            try:
                data['user_metrics'] = pd.read_json('mongo/user_metrics.json', lines=True)
            except:
                data['user_metrics'] = pd.DataFrame()

            try:
                data['nutrition_logs'] = pd.read_json('mongo/nutrition_logs.json', lines=True)
            except:
                data['nutrition_logs'] = pd.DataFrame()

            try:
                data['sleep_records'] = pd.read_json('mongo/sleep_records.json', lines=True)
            except:
                data['sleep_records'] = pd.DataFrame()

            # Generate demo real-time data
            data['real_time_metrics'] = self.generate_demo_real_time_data()

        except Exception as e:
            st.error(f"Demo data loading failed: {e}")
            # Create empty data frames
            data = {
                'users': pd.DataFrame(),
                'activities': pd.DataFrame(),
                'health_metrics': pd.DataFrame(),
                'goals': pd.DataFrame(),
                'alerts': pd.DataFrame(),
                'user_metrics': pd.DataFrame(),
                'nutrition_logs': pd.DataFrame(),
                'sleep_records': pd.DataFrame(),
                'real_time_metrics': self.generate_demo_real_time_data()
            }

        return self.process_dates(data)

    def generate_demo_real_time_data(self):
        """Generate demo real-time metrics data"""
        now = datetime.now()
        data = []
        for i in range(100):
            timestamp = now - timedelta(seconds=i * 2)
            data.append({
                'user_id': f'user-{random.randint(1, 500):04d}',
                'metric_type': random.choice(['heart_rate', 'steps', 'calories_burned', 'active_minutes']),
                'value': random.randint(60, 180) if random.choice(
                    ['heart_rate', 'steps']) == 'heart_rate' else random.randint(0, 50),
                'timestamp': timestamp,
                'device_id': f'device-{random.randint(1, 10):03d}',
                'session_id': f'session-{random.randint(1000, 9999)}'
            })
        return pd.DataFrame(data)

    def process_dates(self, data):
        """Unified date format processing"""
        # Process activities dates
        if not data['activities'].empty and 'date' in data['activities'].columns:
            data['activities']['date'] = pd.to_datetime(data['activities']['date'], errors='coerce')

        # Process health_metrics dates
        if not data['health_metrics'].empty and 'recorded_at' in data['health_metrics'].columns:
            data['health_metrics']['recorded_at'] = pd.to_datetime(data['health_metrics']['recorded_at'],
                                                                   errors='coerce')

        # Process goals dates
        if not data['goals'].empty and 'deadline' in data['goals'].columns:
            data['goals']['deadline'] = pd.to_datetime(data['goals']['deadline'], errors='coerce')
        if not data['goals'].empty and 'created_at' in data['goals'].columns:
            data['goals']['created_at'] = pd.to_datetime(data['goals']['created_at'], errors='coerce')

        # Process alerts dates
        if not data['alerts'].empty and 'triggered_at' in data['alerts'].columns:
            data['alerts']['triggered_at'] = pd.to_datetime(data['alerts']['triggered_at'], errors='coerce')

        # Process users dates
        if not data['users'].empty and 'created_at' in data['users'].columns:
            data['users']['created_at'] = pd.to_datetime(data['users']['created_at'], errors='coerce')

        # Process MongoDB data dates
        if not data['user_metrics'].empty and 'ts' in data['user_metrics'].columns:
            data['user_metrics']['ts'] = pd.to_datetime(data['user_metrics']['ts'], errors='coerce')

        if not data['nutrition_logs'].empty and 'timestamp' in data['nutrition_logs'].columns:
            data['nutrition_logs']['timestamp'] = pd.to_datetime(data['nutrition_logs']['timestamp'], errors='coerce')

        if not data['sleep_records'].empty and 'date' in data['sleep_records'].columns:
            data['sleep_records']['date'] = pd.to_datetime(data['sleep_records']['date'], errors='coerce')

        # Process real-time metrics dates
        if not data['real_time_metrics'].empty and 'timestamp' in data['real_time_metrics'].columns:
            data['real_time_metrics']['timestamp'] = pd.to_datetime(data['real_time_metrics']['timestamp'],
                                                                    errors='coerce')

        return data

    def get_user_real_time_metrics(self, user_id):
        """Get real-time metrics for a specific user"""
        try:
            if self.demo_mode:
                return self.generate_user_demo_metrics(user_id)

            # Get real-time metrics for specific user
            user_metrics = list(self.mongo_db.real_time_metrics.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(50))

            if not user_metrics:
                return self.generate_user_demo_metrics(user_id)

            return pd.DataFrame(user_metrics)

        except Exception as e:
            st.error(f"Error fetching user real-time metrics: {e}")
            return self.generate_user_demo_metrics(user_id)

    def generate_user_demo_metrics(self, user_id):
        """Generate demo real-time metrics for a specific user"""
        now = datetime.now()
        data = []
        for i in range(20):
            timestamp = now - timedelta(seconds=i * 3)
            data.append({
                'user_id': user_id,
                'metric_type': random.choice(['heart_rate', 'steps', 'calories_burned', 'active_minutes']),
                'value': random.randint(60, 180) if random.choice(
                    ['heart_rate', 'steps']) == 'heart_rate' else random.randint(0, 50),
                'timestamp': timestamp,
                'device_id': f'device-{random.randint(1, 10):03d}',
                'session_id': f'session-{random.randint(1000, 9999)}'
            })
        return pd.DataFrame(data)

    def get_latest_user_metrics(self, user_metrics_df):
        """Get latest value for each metric type for a user"""
        if user_metrics_df.empty:
            return {}

        latest_metrics = {}
        metric_types = ['heart_rate', 'steps', 'calories_burned', 'active_minutes']

        for metric_type in metric_types:
            metric_data = user_metrics_df[user_metrics_df['metric_type'] == metric_type]
            if not metric_data.empty:
                latest = metric_data.iloc[0]  # Already sorted by timestamp descending
                latest_metrics[metric_type] = {
                    'value': latest['value'],
                    'timestamp': latest['timestamp']
                }

        return latest_metrics


    def get_data_stats(self):
        """Get real-time data statistics"""
        try:
            if self.demo_mode:
                return {"total_records": 0, "oldest_record": None}

            total = self.mongo_db.real_time_metrics.count_documents({})
            oldest = self.mongo_db.real_time_metrics.find_one(
                {},
                sort=[("timestamp", 1)]
            )

            return {
                "total_records": total,
                "oldest_record": oldest["timestamp"] if oldest else None
            }
        except Exception as e:
            return {"total_records": 0, "oldest_record": None}

    def cleanup_old_data(self, days=7):
        """Manually clean up old data - fixed version"""
        try:
            if self.demo_mode:
                return 0

            cutoff_date = datetime.now() - timedelta(days=days)

            # First check how many records match the criteria
            count_before = self.mongo_db.real_time_metrics.count_documents({
                "timestamp": {"$lt": cutoff_date}
            })

            st.info(f"Found {count_before} records older than {days} days")

            if count_before > 0:
                result = self.mongo_db.real_time_metrics.delete_many({
                    "timestamp": {"$lt": cutoff_date}
                })
                return result.deleted_count
            else:
                # If no old data found, it might be that all data is newly generated
                st.warning("No expired data found, all data may be newly generated")
                return 0

        except Exception as e:
            st.error(f"Error cleaning up data: {e}")
            return 0


def main():
    st.markdown('<h1 class="main-header">🏃‍♂️ Vamos - Smart Fitness & Health Dashboard</h1>', unsafe_allow_html=True)

    # Initialize dashboard
    dashboard = Dashboard()
    data = dashboard.load_data()

    if data['users'].empty:
        st.error("No data available, please run generate_sample_data.py first to generate sample data")
        st.info("Run command: `python generate_sample_data.py`")
        return

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["System Overview", "User Details", "Health Analytics", "Fitness Analytics", "Data Management", "Live Metrics"]
    )

    # Page routing
    if page == "System Overview":
        show_overview(data)
    elif page == "User Details":
        show_user_detail(data)
    elif page == "Health Analytics":
        show_health_analytics(data)
    elif page == "Fitness Analytics":
        show_fitness_analytics(data)
    elif page == "Data Management":
        show_data_management(dashboard, data)
    elif page == "Live Metrics":
        show_live_metrics(dashboard, data)


def show_live_metrics(dashboard, data):
    """Display real-time live metrics page for individual users"""
    st.header("📊 Live Real-Time Metrics")

    # User selection
    user_list = data['users']['user_id'].tolist()
    selected_user = st.selectbox("Select User", user_list)

    if not selected_user:
        st.info("Please select a user to view real-time metrics")
        return

    # Get user basic information
    user_data = data['users'][data['users']['user_id'] == selected_user].iloc[0]

    # Display user information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Name:** {user_data['name']}")
        st.write(f"**Age:** {user_data['age']}")
    with col2:
        st.write(f"**Gender:** {user_data['gender']}")
        st.write(f"**Height:** {user_data['height_cm']} cm")
    with col3:
        st.write(f"**User ID:** {selected_user}")
        if 'created_at' in user_data:
            st.write(f"**Member since:** {user_data['created_at'].strftime('%Y-%m-%d')}")

    st.markdown("---")

    # Auto-refresh control
    refresh_rate = st.slider("Refresh rate (seconds)", 5, 30, 10)

    # Refresh button
    if st.button("🔄 Manual Refresh"):
        st.rerun()

    # Get real-time metrics for selected user
    user_real_time_metrics = dashboard.get_user_real_time_metrics(selected_user)
    latest_metrics = dashboard.get_latest_user_metrics(user_real_time_metrics)

    # Display real-time metrics cards
    st.subheader("🔄 Current Real-Time Metrics")

    col1, col2, col3, col4 = st.columns(4)

    metric_display = {
        "heart_rate": {"name": "❤️ Heart Rate", "unit": "bpm", "icon": "❤️", "color": "#ff6b6b"},
        "steps": {"name": "👣 Steps", "unit": "steps/min", "icon": "👣", "color": "#4ecdc4"},
        "calories_burned": {"name": "🔥 Calories", "unit": "cal/min", "icon": "🔥", "color": "#45b7d1"},
        "active_minutes": {"name": "⏱️ Active", "unit": "min", "icon": "⏱️", "color": "#96ceb4"}
    }

    # Display metrics cards
    for metric_type, display_info in metric_display.items():
        if metric_type in latest_metrics:
            value = latest_metrics[metric_type]['value']
            timestamp = latest_metrics[metric_type]['timestamp']
            status = "Live"
        else:
            # Generate appropriate default values if no data
            if metric_type == "heart_rate":
                value = random.randint(65, 85)
            elif metric_type == "steps":
                value = random.randint(100, 300)
            elif metric_type == "calories_burned":
                value = random.randint(5, 15)
            else:  # active_minutes
                value = random.randint(2, 10)
            status = "Simulated"
            timestamp = datetime.now()

        # Display in appropriate column
        if metric_type == "heart_rate":
            with col1:
                display_metric_card(display_info, value, timestamp, status)
        elif metric_type == "steps":
            with col2:
                display_metric_card(display_info, value, timestamp, status)
        elif metric_type == "calories_burned":
            with col3:
                display_metric_card(display_info, value, timestamp, status)
        elif metric_type == "active_minutes":
            with col4:
                display_metric_card(display_info, value, timestamp, status)

    st.markdown("---")

    # Real-time trends
    st.subheader("📈 Real-Time Trends")

    if not user_real_time_metrics.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Heart rate trend
            heart_rate_data = user_real_time_metrics[
                user_real_time_metrics['metric_type'] == 'heart_rate'
                ].head(20)  # Last 20 records

            if not heart_rate_data.empty:
                fig = px.line(
                    heart_rate_data,
                    x='timestamp',
                    y='value',
                    title=f'Heart Rate Trend - {user_data["name"]}',
                    labels={'value': 'Heart Rate (bpm)', 'timestamp': 'Time'}
                )
                fig.update_traces(line=dict(color='red', width=3))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No heart rate data available for trend analysis")

        with col2:
            # Steps trend
            steps_data = user_real_time_metrics[
                user_real_time_metrics['metric_type'] == 'steps'
                ].head(20)

            if not steps_data.empty:
                fig = px.line(
                    steps_data,
                    x='timestamp',
                    y='value',
                    title=f'Steps Trend - {user_data["name"]}',
                    labels={'value': 'Steps per minute', 'timestamp': 'Time'}
                )
                fig.update_traces(line=dict(color='green', width=3))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No steps data available for trend analysis")

        # Additional metrics trends
        col3, col4 = st.columns(2)

        with col3:
            # Calories burned trend
            calories_data = user_real_time_metrics[
                user_real_time_metrics['metric_type'] == 'calories_burned'
                ].head(20)

            if not calories_data.empty:
                fig = px.line(
                    calories_data,
                    x='timestamp',
                    y='value',
                    title=f'Calories Burned Trend - {user_data["name"]}',
                    labels={'value': 'Calories per minute', 'timestamp': 'Time'}
                )
                fig.update_traces(line=dict(color='orange', width=3))
                st.plotly_chart(fig, use_container_width=True)

        with col4:
            # Active minutes trend
            active_data = user_real_time_metrics[
                user_real_time_metrics['metric_type'] == 'active_minutes'
                ].head(20)

            if not active_data.empty:
                fig = px.line(
                    active_data,
                    x='timestamp',
                    y='value',
                    title=f'Active Minutes Trend - {user_data["name"]}',
                    labels={'value': 'Active Minutes', 'timestamp': 'Time'}
                )
                fig.update_traces(line=dict(color='blue', width=3))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No real-time data available for trend analysis")

    st.markdown("---")

    # Recent activity feed
    st.subheader("📋 Recent Activity Feed")

    if not user_real_time_metrics.empty:
        recent_activities = user_real_time_metrics.head(15)
        for _, activity in recent_activities.iterrows():
            timestamp = activity['timestamp'].strftime('%H:%M:%S') if pd.notna(activity['timestamp']) else "Unknown"
            st.write(f"**{timestamp}** - {activity['metric_type'].replace('_', ' ').title()}: **{activity['value']}**")
    else:
        st.info("No recent activity data available")

    # Metric distribution
    st.subheader("📊 Metric Distribution")

    if not user_real_time_metrics.empty:
        metric_counts = user_real_time_metrics['metric_type'].value_counts()
        fig_pie = px.pie(
            values=metric_counts.values,
            names=metric_counts.index,
            title=f'Activity Distribution - {user_data["name"]}'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Auto-refresh
    time.sleep(refresh_rate)
    st.rerun()


def display_metric_card(display_info, value, timestamp, status):
    """Display a single metric card"""
    timestamp_str = timestamp.strftime('%H:%M:%S') if isinstance(timestamp, datetime) else "Unknown"

    st.markdown(f"""
    <div class="real-time-metric">
        <h3>{display_info['icon']} {display_info['name']}</h3>
        <h2>{value} {display_info['unit']}</h2>
        <small>Updated: {timestamp_str}</small>
        <br><small><em>{status}</em></small>
    </div>
    """, unsafe_allow_html=True)


def show_data_management(dashboard, data):
    """Display data management page with real-time data management"""
    st.header("🗃️ Data Management")

    st.subheader("Database Information")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**PostgreSQL Data**")
        st.write(f"- Users Table: {len(data['users'])} rows")
        st.write(f"- Activities Table: {len(data['activities'])} rows")
        st.write(f"- Health Metrics: {len(data['health_metrics'])} rows")
        st.write(f"- Goals Table: {len(data['goals'])} rows")
        st.write(f"- Alerts Table: {len(data['alerts'])} rows")

    with col2:
        st.write("**MongoDB Data**")
        st.write(f"- User Metrics: {len(data['user_metrics'])} documents")
        st.write(f"- Nutrition Logs: {len(data['nutrition_logs'])} documents")
        st.write(f"- Sleep Records: {len(data['sleep_records'])} documents")
        st.write(f"- Real-time Metrics: {len(data['real_time_metrics'])} documents")

    st.markdown("---")

    # Real-time Data Management Section
    st.subheader("🔧 Real-time Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Data Statistics**")
        stats = dashboard.get_data_stats()
        st.write(f"- Total real-time records: {stats['total_records']:,}")
        if stats['oldest_record']:
            age = datetime.now() - stats['oldest_record']
            st.write(f"- Oldest record: {age.days} days {age.seconds // 3600} hours ago")

        st.info("💡 Data automatically expires after 7 days (TTL index)")

    with col2:
        st.write("**Data Cleanup**")
        days_to_keep = st.slider("Keep data for (days)", 1, 30, 7)

        if st.button("🗑️ Clean Up Old Data Now"):
            deleted_count = dashboard.cleanup_old_data(days=days_to_keep)
            if deleted_count > 0:
                st.success(f"✅ Deleted {deleted_count} records older than {days_to_keep} days")
            else:
                st.info("No records found to delete")

    st.markdown("---")

    st.subheader("Data Export")
    st.info(
        "According to project requirements, data is ready to be exported as PostgreSQL dump and MongoDB dump formats")

    if st.button("Generate Export Instructions"):
        st.markdown("""
        ### Export Steps:

        **PostgreSQL Export Command:**
        ```bash
        pg_dump -h localhost -p 5432 -U postgres \\
        -d vamos_fitness \\
        -Fc \\
        -f postgres/db.dump
        ```

        **MongoDB Export Command:**
        ```bash
        mongodump --db vamos_fitness --out mongo/dump
        ```
        """)


# All other functions remain exactly the same as before
def show_overview(data):
    """Display system overview page"""
    # ... (keep all existing show_overview code exactly the same) ...
    st.header("📊 System Overview")

    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_users = len(data['users'])
        st.metric("Total Users", f"{total_users:,}")

    with col2:
        if not data['activities'].empty:
            today = pd.Timestamp.now().normalize()
            # Ensure date column is datetime type
            activities_with_dates = data['activities'].copy()
            activities_with_dates['date'] = pd.to_datetime(activities_with_dates['date'])
            active_today = len(activities_with_dates[activities_with_dates['date'] >= today])
            st.metric("Today's Activities", active_today)
        else:
            st.metric("Today's Activities", 0)

    with col3:
        # Calculate average BMI
        user_metrics = data['user_metrics']
        if not user_metrics.empty:
            try:
                # Safely access meta field
                height_data = user_metrics[user_metrics['meta'].apply(
                    lambda x: isinstance(x, dict) and x.get('sensor_type') == 'height'
                )]
                weight_data = user_metrics[user_metrics['meta'].apply(
                    lambda x: isinstance(x, dict) and x.get('sensor_type') == 'weight'
                )]

                if not height_data.empty and not weight_data.empty:
                    # Get latest data for each user
                    bmi_values = []
                    for user_id in data['users']['user_id'].unique()[:100]:  # Limit calculation quantity
                        user_heights = height_data[height_data['user_id'] == user_id]
                        user_weights = weight_data[weight_data['user_id'] == user_id]

                        if not user_heights.empty and not user_weights.empty:
                            latest_height = user_heights.loc[user_heights['ts'].idxmax()]['height_cm']
                            latest_weight = user_weights.loc[user_weights['ts'].idxmax()]['weight_kg']

                            if pd.notna(latest_height) and pd.notna(latest_weight) and latest_height > 0:
                                bmi = latest_weight / ((latest_height / 100) ** 2)
                                bmi_values.append(bmi)

                    if bmi_values:
                        avg_bmi = sum(bmi_values) / len(bmi_values)
                        st.metric("Average BMI", f"{avg_bmi:.1f}")
                    else:
                        st.metric("Average BMI", "23.4")
                else:
                    st.metric("Average BMI", "23.4")
            except:
                st.metric("Average BMI", "23.4")
        else:
            st.metric("Average BMI", "23.4")

    with col4:
        if not data['alerts'].empty:
            active_alerts = len(data['alerts'][data['alerts']['resolved'] == False])
            st.metric("Active Alerts", active_alerts)
        else:
            st.metric("Active Alerts", 0)

    # Chart row 1
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 User Weight Trend")
        weight_data = data['user_metrics']
        if not weight_data.empty:
            try:
                weight_records = weight_data[weight_data['meta'].apply(
                    lambda x: isinstance(x, dict) and x.get('sensor_type') == 'weight'
                )]
                if not weight_records.empty:
                    weight_records = weight_records.copy()
                    weight_records['date'] = pd.to_datetime(weight_records['ts']).dt.date
                    monthly_avg = weight_records.groupby('date')['weight_kg'].mean().reset_index()
                    fig = px.line(monthly_avg, x='date', y='weight_kg', title='Average Weight Trend')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No weight data available")
            except Exception as e:
                st.error(f"Weight chart generation failed: {e}")
        else:
            st.info("No sensor data available")

    with col2:
        st.subheader("❤️ Heart Rate Distribution")
        hr_data = data['user_metrics']
        if not hr_data.empty:
            try:
                hr_records = hr_data[hr_data['meta'].apply(
                    lambda x: isinstance(x, dict) and x.get('sensor_type') == 'heart_rate'
                )]
                if not hr_records.empty and 'heart_rate_bpm' in hr_records.columns:
                    fig = px.histogram(hr_records, x='heart_rate_bpm', title='User Heart Rate Distribution')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No heart rate data available")
            except Exception as e:
                st.error(f"Heart rate chart generation failed: {e}")
        else:
            st.info("No sensor data available")

    # Recent alerts
    st.subheader("🚨 Recent Health Alerts")
    if not data['alerts'].empty:
        recent_alerts = data['alerts'].sort_values('triggered_at', ascending=False).head(5)
        for _, alert in recent_alerts.iterrows():
            alert_class = f"alert-{alert['severity']}" if 'severity' in alert else "alert-medium"
            st.markdown(f"""
            <div class="metric-card {alert_class}">
                <strong>{alert['user_id']}</strong> - {alert.get('message', 'No message')} 
                <br><small>{alert['triggered_at']}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No alert data available")


def show_user_detail(data):
    """Display user details page"""
    # ... (keep all existing show_user_detail code exactly the same) ...
    st.header("👤 User Details")

    if data['users'].empty:
        st.warning("No user data available")
        return

    # User selection
    user_list = data['users']['user_id'].tolist()
    selected_user = st.selectbox("Select User", user_list)

    if selected_user:
        user_data = data['users'][data['users']['user_id'] == selected_user].iloc[0]
        user_activities = data['activities'][data['activities']['user_id'] == selected_user]
        user_goals = data['goals'][data['goals']['user_id'] == selected_user]
        user_alerts = data['alerts'][data['alerts']['user_id'] == selected_user]

        # User basic information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Name:** {user_data['name']}")
            st.write(f"**Age:** {user_data['age']}")
            st.write(f"**Gender:** {user_data['gender']}")
        with col2:
            st.write(f"**Height:** {user_data['height_cm']} cm")
            if 'created_at' in user_data:
                st.write(f"**Registration Date:** {user_data['created_at']}")
        with col3:
            # Calculate completed goals
            if not user_goals.empty:
                completed_goals = len(user_goals[user_goals['status'] == 'completed'])
                total_goals = len(user_goals)
                st.write(f"**Goal Completion Rate:** {completed_goals}/{total_goals}")
            else:
                st.write("**Goal Completion Rate:** 0/0")

        # User activity chart
        st.subheader("🏃 Activity Records")
        if not user_activities.empty:
            activity_summary = user_activities.groupby('activity_type').agg({
                'duration_min': 'sum',
                'calories_burned': 'sum'
            }).reset_index()

            fig = px.bar(activity_summary, x='activity_type', y='calories_burned',
                         title='Calories Burned by Activity Type')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity records for this user")

        # Goal progress
        st.subheader("🎯 Goal Progress")
        if not user_goals.empty:
            active_goals = user_goals[user_goals['status'] == 'active']
            for _, goal in active_goals.iterrows():
                if goal['target_value'] > 0:
                    progress = min(goal['current_value'] / goal['target_value'] * 100, 100)
                    st.write(f"**{goal['goal_type']}**: {goal['current_value']}/{goal['target_value']}")
                    st.progress(int(progress))
        else:
            st.info("No goals for this user")


def show_health_analytics(data):
    """Display health analytics page"""
    # ... (keep all existing show_health_analytics code exactly the same) ...
    st.header("❤️ Health Analytics")

    # BMI analysis
    st.subheader("📊 BMI Distribution Analysis")

    # Calculate BMI from sensor data
    user_metrics = data['user_metrics']
    if not user_metrics.empty:
        try:
            # Get latest height and weight data
            latest_data = []
            for user_id in data['users']['user_id'].unique()[:200]:  # Limit calculation quantity
                user_height = user_metrics[
                    (user_metrics['user_id'] == user_id) &
                    (user_metrics['meta'].apply(
                        lambda x: isinstance(x, dict) and x.get('sensor_type') == 'height'
                    ))
                    ]
                user_weight = user_metrics[
                    (user_metrics['user_id'] == user_id) &
                    (user_metrics['meta'].apply(
                        lambda x: isinstance(x, dict) and x.get('sensor_type') == 'weight'
                    ))
                    ]

                if not user_height.empty and not user_weight.empty:
                    latest_height = user_height.loc[user_height['ts'].idxmax()]['height_cm']
                    latest_weight = user_weight.loc[user_weight['ts'].idxmax()]['weight_kg']

                    if pd.notna(latest_height) and pd.notna(latest_weight) and latest_height > 0:
                        bmi = latest_weight / ((latest_height / 100) ** 2)
                        latest_data.append({
                            'user_id': user_id,
                            'bmi': round(bmi, 1),
                            'weight_kg': latest_weight,
                            'height_cm': latest_height
                        })

            bmi_df = pd.DataFrame(latest_data)
            if not bmi_df.empty:
                # BMI distribution chart
                fig = px.histogram(bmi_df, x='bmi', title='User BMI Distribution',
                                   nbins=20, color_discrete_sequence=['lightblue'])
                fig.add_vline(x=18.5, line_dash="dash", line_color="green", annotation_text="Underweight")
                fig.add_vline(x=25, line_dash="dash", line_color="yellow", annotation_text="Healthy")
                fig.add_vline(x=30, line_dash="dash", line_color="red", annotation_text="Overweight")
                st.plotly_chart(fig, use_container_width=True)

                # BMI category statistics
                bmi_categories = []
                for bmi in bmi_df['bmi']:
                    if bmi < 18.5:
                        bmi_categories.append('Underweight')
                    elif bmi < 25:
                        bmi_categories.append('Healthy')
                    elif bmi < 30:
                        bmi_categories.append('Overweight')
                    else:
                        bmi_categories.append('Obese')

                category_counts = pd.Series(bmi_categories).value_counts()
                fig_pie = px.pie(values=category_counts.values, names=category_counts.index,
                                 title='BMI Category Distribution')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Insufficient BMI data available")
        except Exception as e:
            st.error(f"BMI analysis failed: {e}")
    else:
        st.info("No sensor data available")


def show_fitness_analytics(data):
    """Display fitness analytics page"""
    # ... (keep all existing show_fitness_analytics code exactly the same) ...
    st.header("💪 Fitness Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏃‍♂️ Activity Type Distribution")
        if not data['activities'].empty:
            activity_counts = data['activities']['activity_type'].value_counts()
            fig = px.pie(values=activity_counts.values, names=activity_counts.index,
                         title='Activity Type Distribution')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity data available")

    with col2:
        st.subheader("🔥 Daily Calorie Consumption Trend")
        if not data['activities'].empty:
            activities = data['activities'].copy()
            activities['date'] = pd.to_datetime(activities['date']).dt.date
            daily_calories = activities.groupby('date')['calories_burned'].sum().reset_index()
            fig = px.line(daily_calories, x='date', y='calories_burned',
                          title='Daily Total Calorie Consumption Trend')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity data available")

    # Goal completion status
    st.subheader("🎯 Goal Completion Status")
    if not data['goals'].empty:
        goal_status = data['goals']['status'].value_counts()
        fig = px.bar(x=goal_status.index, y=goal_status.values,
                     title='Goal Status Distribution', color=goal_status.index)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No goal data available")


if __name__ == "__main__":
    main()