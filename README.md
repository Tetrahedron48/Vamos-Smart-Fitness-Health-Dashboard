# 🏃‍♂️ Vamos - Smart Fitness & Health Dashboard

A Streamlit-based intelligent fitness and health data visualization dashboard with PostgreSQL and MongoDB dual database support.

## 📋 Project Overview

Vamos is a comprehensive fitness and health data management platform that provides:

- 📊 **System Overview** - Key metrics and health alerts monitoring
- 👤 **User Details** - Personal activity records and goal progress tracking
- ❤️ **Health Analytics** - BMI analysis and heart rate distribution
- 💪 **Fitness Analytics** - Activity type distribution and calorie consumption trends
- 🗃️ **Data Management** - Database status monitoring and data export

## 🏗️ Project Structure

```
Vamos/
├── app.py                          # Main application file
├── generate_sample_data.py         # Generate sample data
├── import_mongo_data.py           # Import MongoDB data
├── import_Postgre_data.py           # Import PostgreSQL data (includes table creation)
├── check_data_status.py           # Check data status
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── postgres/                     # PostgreSQL data files
│   ├── users.csv
│   ├── activities.csv
│   ├── health_metrics.csv
│   ├── goals.csv
│   ├── alerts.csv
│   ├── coaches.csv
│   └── user_coach.csv
└── mongo/                        # MongoDB data files
    ├── user_metrics.json
    ├── nutrition_logs.json
    └── sleep_records.json
```

## 🚀 Complete Usage Manual

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- MongoDB 4.4+

### Step-by-Step Setup Guide

#### Step 1: Environment Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create environment configuration file
echo "PG_HOST=localhost" > .env
echo "PG_PORT=5432" >> .env
echo "PG_DB=vamos_fitness" >> .env
echo "PG_USER=postgres" >> .env
echo "PG_PASSWORD=your_password" >> .env
echo "MONGO_HOST=localhost" >> .env
echo "MONGO_PORT=27017" >> .env
echo "MONGO_DB=vamos_fitness" >> .env
```

**Edit the `.env` file and replace `your_password` with your actual PostgreSQL password.**

#### Step 2: Generate Sample Data

```bash
# Generate sample data files (CSV and JSON)
python generate_sample_data.py
```

This creates comprehensive sample data including:
- 500 users with demographic information
- 2,500+ activity records across 6 activity types
- 6,000+ sensor measurements
- 7,500+ nutrition logs
- 10,000+ sleep records
- 500+ fitness goals
- 100+ health alerts

#### Step 3: Import Data to PostgreSQL

```bash
# This will automatically create database and tables, then import data
python import_Postgre_data.py
```

The script automatically:
- Tests database connection
- Creates the `vamos_fitness` database if needed
- Creates all required tables
- Imports data from CSV files
- Verifies the imported data

#### Step 4: Import Data to MongoDB

```bash
# Import JSON data to MongoDB collections
python import_mongo_data.py
```

#### Step 5: Verify Data Import

```bash
# Check data status in both databases
python check_data_status.py
```

Expected output showing data counts in all tables and collections.

#### Step 6: Launch Dashboard

```bash
# Start the Streamlit application
streamlit run app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

## 📊 Dashboard Features Guide

### System Overview Page
- **Key Metrics**: Total users, today's activities, average BMI, active alerts
- **Weight Trend Chart**: Average user weight progression over time
- **Heart Rate Distribution**: Histogram of user heart rate measurements
- **Recent Health Alerts**: Latest unresolved alerts with severity indicators

### User Details Page
- **User Selection**: Dropdown to select individual users
- **Basic Information**: Demographic and registration details
- **Activity Records**: Bar chart showing calories burned by activity type
- **Goal Progress**: Progress bars for active fitness goals

### Health Analytics Page
- **BMI Distribution**: Histogram with healthy range indicators
- **BMI Category Analysis**: Pie chart showing underweight/healthy/overweight/obese distribution
- **Real-time Calculations**: BMI computed from latest sensor data

### Fitness Analytics Page
- **Activity Type Distribution**: Pie chart of different exercise types
- **Calorie Consumption Trend**: Line chart of daily total calories burned
- **Goal Status Distribution**: Bar chart showing completed vs active goals

### Data Management Page
- **Database Information**: Row counts for all tables and collections
- **Export Instructions**: Commands for database backup and export
- **Project Structure**: Recommended file organization for deployment


## 🗂️ Data Export Procedures

### PostgreSQL Export
```bash
pg_dump -h localhost -p 5432 -U postgres -d vamos_fitness -Fc -f postgres/db.dump
```

### MongoDB Export
```bash
mongodump --db vamos_fitness --out mongo/dump
```


## 🛠️ Technical Specifications

- **Frontend Framework**: Streamlit 1.28.0
- **Data Visualization**: Plotly 5.15.0
- **Database ORM**: Psycopg2 2.9.7 (PostgreSQL), PyMongo 4.5.0 (MongoDB)
- **Data Processing**: Pandas 2.0.3
- **Environment Management**: python-dotenv 1.0.0
- **Sample Data Generation**: Faker 19.6.2

## 📈 Data Schema Overview

### PostgreSQL (Structured Data)
- **users**: User demographics and profiles (500 records)
- **activities**: Exercise and workout records (2,500+ records)
- **health_metrics**: Basic health measurements
- **goals**: User fitness targets and progress (500+ records)
- **alerts**: System-generated health notifications (100+ records)
- **coaches**: Trainer information
- **user_coach**: User-trainer relationships

### MongoDB (Sensor & Log Data)
- **user_metrics**: Real-time sensor data (height, weight, heart rate) - 6,000+ documents
- **nutrition_logs**: Food intake and calorie tracking - 7,500+ documents
- **sleep_records**: Sleep patterns and quality metrics - 10,000+ documents

## 🎯 Quick Start Summary

1. **Setup**: `pip install -r requirements.txt` + configure `.env`
2. **Generate Data**: `python generate_sample_data.py`
3. **Import PostgreSQL**: `python import_Postgre_data.py`
4. **Import MongoDB**: `python import_mongo_data.py`
5. **Launch**: `streamlit run app.py`

