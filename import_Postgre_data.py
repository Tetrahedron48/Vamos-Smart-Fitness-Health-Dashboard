import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()


def create_tables(cursor):
    """Create database tables if they don't exist"""
    print("Creating database tables...")

    tables_sql = [
        """CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(150),
            age INTEGER,
            gender VARCHAR(20),
            height_cm DECIMAL(5,2),
            created_at TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS coaches (
            coach_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            specialty VARCHAR(50),
            email VARCHAR(150)
        )""",

        """CREATE TABLE IF NOT EXISTS user_coach (
            user_id VARCHAR(50),
            coach_id VARCHAR(50),
            PRIMARY KEY (user_id, coach_id)
        )""",

        """CREATE TABLE IF NOT EXISTS goals (
            goal_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            goal_type VARCHAR(50),
            target_value DECIMAL(10,2),
            current_value DECIMAL(10,2),
            deadline DATE,
            status VARCHAR(20),
            created_at TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS activities (
            activity_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            activity_type VARCHAR(50),
            duration_min INTEGER,
            calories_burned INTEGER,
            distance_km DECIMAL(8,2),
            date TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS health_metrics (
            metric_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            metric_type VARCHAR(50),
            value TEXT,
            recorded_at TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS alerts (
            alert_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            alert_type VARCHAR(50),
            message TEXT,
            severity VARCHAR(20),
            triggered_at TIMESTAMP,
            resolved BOOLEAN
        )"""
    ]

    for sql in tables_sql:
        try:
            cursor.execute(sql)
            print(f"✅ Table created/verified")
        except Exception as e:
            print(f"❌ Table creation failed: {e}")


def import_data_manual():
    """Manually import data to PostgreSQL"""
    print("Manually importing data to PostgreSQL...")

    try:
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST', 'localhost'),
            port=int(os.getenv('PG_PORT', 5432)),
            dbname=os.getenv('PG_DB', 'vamos_fitness'),
            user=os.getenv('PG_USER', 'postgres'),
            password=os.getenv('PG_PASSWORD', 'password'),
            connect_timeout=5
        )
        cursor = conn.cursor()

        # Create tables first
        create_tables(cursor)
        conn.commit()

        # Import data for each table
        tables = ['users', 'coaches', 'user_coach', 'goals', 'activities', 'health_metrics', 'alerts']

        for table in tables:
            try:
                print(f"Importing {table} table...")

                # Check if CSV file exists
                csv_file = f'postgres/{table}.csv'
                if not os.path.exists(csv_file):
                    print(f"⚠️  CSV file not found: {csv_file}")
                    continue

                df = pd.read_csv(csv_file)

                # Clear table
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE")

                # Manually build INSERT statements
                for index, row in df.iterrows():
                    columns = ', '.join([f'"{col}"' for col in row.index])
                    placeholders = ', '.join(['%s'] * len(row))

                    sql = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'

                    # Process data values
                    values = []
                    for val in row.values:
                        if pd.isna(val):
                            values.append(None)
                        else:
                            # Convert datetime strings if needed
                            if isinstance(val, str) and ('T' in val or ' ' in val):
                                try:
                                    # Try to parse as datetime
                                    pd.to_datetime(val)
                                except:
                                    pass
                            values.append(val)

                    cursor.execute(sql, tuple(values))

                conn.commit()
                print(f"✅ {table} imported successfully ({len(df)} rows)")

            except Exception as e:
                print(f"❌ {table} import failed: {e}")
                conn.rollback()
                continue

        cursor.close()
        conn.close()
        print("✅ All data import completed!")
        return True

    except Exception as e:
        print(f"❌ Data import failed: {e}")
        return False


def check_data():
    """Check imported data"""
    print("\nChecking imported data...")

    try:
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST', 'localhost'),
            port=int(os.getenv('PG_PORT', 5432)),
            dbname=os.getenv('PG_DB', 'vamos_fitness'),
            user=os.getenv('PG_USER', 'postgres'),
            password=os.getenv('PG_PASSWORD', 'password'),
        )
        cursor = conn.cursor()

        tables = ['users', 'coaches', 'user_coach', 'goals', 'activities', 'health_metrics', 'alerts']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} rows")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Check failed: {e}")


def test_connection():
    """Test database connection"""
    print("Testing database connection...")

    try:
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST', 'localhost'),
            port=int(os.getenv('PG_PORT', 5432)),
            dbname=os.getenv('PG_DB', 'vamos_fitness'),
            user=os.getenv('PG_USER', 'postgres'),
            password=os.getenv('PG_PASSWORD', 'password'),
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connection successful: {version.split(',')[0]}")
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def create_database():
    """Create database if it doesn't exist"""
    try:
        # Connect to default postgres database to create our database
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST', 'localhost'),
            port=int(os.getenv('PG_PORT', 5432)),
            dbname='postgres',
            user=os.getenv('PG_USER', 'postgres'),
            password=os.getenv('PG_PASSWORD', 'password'),
            connect_timeout=5
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'vamos_fitness'")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("CREATE DATABASE vamos_fitness")
            print("✅ Database 'vamos_fitness' created")
        else:
            print("✅ Database 'vamos_fitness' already exists")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Vamos Fitness PostgreSQL Data Import Tool")
    print("=" * 50)

    # Test connection first
    if not test_connection():
        print("\n❌ Cannot connect to PostgreSQL")
        print("Please check:")
        print("1. PostgreSQL service is running")
        print("2. Password in .env file is correct")
        print("3. Username is 'postgres'")
        exit(1)

    # Create database if needed
    create_database()

    # Use manual import directly (no choice needed)
    if import_data_manual():
        check_data()
        print("\n🎉 PostgreSQL data import completed!")
        print("Now run MongoDB import: python import_mongo_data.py")
        print("Then run Dashboard: streamlit run app.py")
    else:
        print("\n❌ Data import failed. Please check the error messages above.")