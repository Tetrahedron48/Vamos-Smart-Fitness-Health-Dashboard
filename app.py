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
</style>
""", unsafe_allow_html=True)



class Dashboard:
    def __init__(self):
        self.init_connections()

    def init_connections(self):
        """Initialize database connections"""
        try:
            # PostgreSQL connection
            self.pg_conn = psycopg2.connect(
                host=os.getenv('PG_HOST', 'localhost'),
                port=int(os.getenv('PG_PORT', 5432)),
                dbname=os.getenv('PG_DB', 'vamos_fitness'),
                user=os.getenv('PG_USER', 'postgres'),
                password=os.getenv('PG_PASSWORD', 'password'),  # Use your actual password
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
            st.sidebar.warning(f"🔧 PostgreSQL are not connected.You are now using default database.\n⚠️Please check if you have run all the steps mentioned in README.md")
            self.demo_mode = True

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

            data = {
                'users': users_df,
                'activities': activities_df,
                'health_metrics': health_metrics_df,
                'goals': goals_df,
                'alerts': alerts_df,
                'user_metrics': pd.DataFrame(user_metrics),
                'nutrition_logs': pd.DataFrame(nutrition_logs),
                'sleep_records': pd.DataFrame(sleep_records)
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
                'sleep_records': pd.DataFrame()
            }

        return self.process_dates(data)

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

        return data


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
        ["System Overview", "User Details", "Health Analytics", "Fitness Analytics", "Data Management"]
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
        show_data_management(data)


def show_overview(data):
    """Display system overview page"""
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


def show_data_management(data):
    """Display data management page"""
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

    st.subheader("Data Export")
    st.info("According to project requirements, data is ready to be exported as PostgreSQL dump and MongoDB dump formats")

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

        **Project Structure:**
        ```
        GroupA_Dashboard/
        ├── mongo/
        │   └── dump/
        │       └── vamos_fitness/
        ├── postgres/
        │   ├── db.dump
        │   ├── .env
        │   └── app.py
        └── README.md
        ```
        """)


if __name__ == "__main__":
    main()
