import psycopg2
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


def check_all_data():
    print("Checking all data status...")

    # Check PostgreSQL
    try:
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST', 'localhost'),
            port=int(os.getenv('PG_PORT', 5432)),
            dbname=os.getenv('PG_DB', 'vamos_fitness'),
            user=os.getenv('PG_USER', 'postgres'),
            password=os.getenv('PG_PASSWORD', 'password')
        )
        cursor = conn.cursor()

        tables = ['users', 'activities', 'health_metrics', 'goals', 'alerts']
        print("\n📊 PostgreSQL Data:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} rows")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")

    # Check MongoDB
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['vamos_fitness']

        print("\n📊 MongoDB Data:")
        metrics_count = db.user_metrics.count_documents({})
        nutrition_count = db.nutrition_logs.count_documents({})
        sleep_count = db.sleep_records.count_documents({})

        print(f"   user_metrics: {metrics_count} documents")
        print(f"   nutrition_logs: {nutrition_count} documents")
        print(f"   sleep_records: {sleep_count} documents")

        client.close()

        if metrics_count > 0:
            print("\n✅ Sensor data is available!")
        else:
            print("\n❌ No sensor data found in MongoDB")

    except Exception as e:
        print(f"❌ MongoDB: {e}")


if __name__ == "__main__":
    check_all_data()