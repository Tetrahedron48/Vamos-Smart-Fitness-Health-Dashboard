# 🏃‍♂️ Vamos - Smart Fitness & Health Dashboard

A Streamlit-based intelligent fitness and health data visualization dashboard with PostgreSQL and MongoDB dual database support, featuring real-time monitoring and analytics.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- MongoDB 4.4+

### Installation & Setup

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure environment**
```bash
# Edit .env with your database credentials
PG_HOST=localhost
PG_PORT=5432
PG_DB=vamos_fitness
PG_USER=postgres
PG_PASSWORD=your_password
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=vamos_fitness
```
**Important:** Replace **your_password** with your real PostgreSQL password.

3. **Generate & import data**
```bash
python generate_sample_data.py    # Generate sample data
python import_Postgre_data.py    # Import to PostgreSQL
python import_mongo_data.py      # Import to MongoDB
```

4. **Launch dashboard**
```bash
streamlit run app.py
```

## 📊 Dashboard Features

### Core Pages
- **📊 System Overview** - Key metrics, weight trends, heart rate distribution
- **👤 User Details** - Individual user profiles and goal tracking
- **❤️ Health Analytics** - BMI analysis and health metrics
- **💪 Fitness Analytics** - Activity patterns and calorie trends
- **🗃️ Data Management** - Database monitoring and export tools
- **⚡ Live Metrics** - Real-time user activity monitoring

### Real-time Features (NEW!)
- Live heart rate, steps, calories, and active minutes tracking
- Auto-refresh (2-10 seconds configurable)
- Real-time trend charts and activity feeds
- Visual indicators with pulsing animations

## 🗂️ Data Structure

### PostgreSQL (Structured Data)
- `users` - 500 user profiles
- `activities` - 2,500+ workout records
- `health_metrics` - Basic health measurements
- `goals` - 500+ fitness targets
- `alerts` - 100+ health notifications

### MongoDB (Sensor & Real-time Data)
- `user_metrics` - 6,000+ sensor readings
- `nutrition_logs` - 7,500+ food records
- `sleep_records` - 10,000+ sleep patterns
- `real_time_metrics` - Continuous live activity data

## 🔧 Data Management

### Automatic Cleanup
- **TTL Index**: Data auto-expires after 7 days
- **Manual Cleanup**: Remove old data via Data Management page
- **Performance**: Optimized for high-volume real-time data

### Export Commands
```bash
# PostgreSQL
pg_dump -h localhost -p 5432 -U postgres -d vamos_fitness -Fc -f postgres/db.dump

# MongoDB
mongodump --db vamos_fitness --out mongo/dump
```

## 🛠️ Technical Stack

- **Frontend**: Streamlit 1.28.0
- **Visualization**: Plotly 5.15.0
- **Databases**: PostgreSQL (Psycopg2), MongoDB (PyMongo)
- **Data Processing**: Pandas 2.0.3
- **Real-time**: Auto-refresh with configurable intervals

## 🎯 Key Benefits

- **Dual Database**: Leverages both SQL and NoSQL strengths
- **Real-time Monitoring**: Live user activity tracking
- **Scalable Architecture**: Handles high-volume sensor data
- **Automated Maintenance**: TTL-based data cleanup
- **Comprehensive Analytics**: Health and fitness insights

## 📈 Performance Features

- **High-speed Data Generation**: 2,000+ records/second capability
- **Batch Processing**: Efficient MongoDB bulk inserts
- **Smart Data Retention**: 7-day automatic expiration
- **Optimized Queries**: Indexed for real-time performance


