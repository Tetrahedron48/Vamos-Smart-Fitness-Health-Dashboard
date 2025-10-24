import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


def import_mongo_data():
    """Import data to MongoDB"""
    print("Importing data to MongoDB...")

    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['vamos_fitness']

        # Clear existing collections
        db.user_metrics.drop()
        db.nutrition_logs.drop()
        db.sleep_records.drop()

        # Import user_metrics data
        print("Importing user_metrics...")
        count_metrics = 0
        with open('mongo/user_metrics.json', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        doc = json.loads(line)
                        db.user_metrics.insert_one(doc)
                        count_metrics += 1
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        continue

        print(f"✅ user_metrics imported: {count_metrics} documents")

        # Import nutrition_logs data
        print("Importing nutrition_logs...")
        count_nutrition = 0
        with open('mongo/nutrition_logs.json', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        doc = json.loads(line)
                        db.nutrition_logs.insert_one(doc)
                        count_nutrition += 1
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        continue

        print(f"✅ nutrition_logs imported: {count_nutrition} documents")

        # Import sleep_records data
        print("Importing sleep_records...")
        count_sleep = 0
        with open('mongo/sleep_records.json', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        doc = json.loads(line)
                        db.sleep_records.insert_one(doc)
                        count_sleep += 1
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        continue

        print(f"✅ sleep_records imported: {count_sleep} documents")

        client.close()
        print("🎉 MongoDB data import completed!")
        return True

    except Exception as e:
        print(f"❌ MongoDB import failed: {e}")
        return False


def check_mongo_data():
    """Check MongoDB data"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['vamos_fitness']

        metrics_count = db.user_metrics.count_documents({})
        nutrition_count = db.nutrition_logs.count_documents({})
        sleep_count = db.sleep_records.count_documents({})

        print(f"\n📊 MongoDB Data Summary:")
        print(f"   user_metrics: {metrics_count} documents")
        print(f"   nutrition_logs: {nutrition_count} documents")
        print(f"   sleep_records: {sleep_count} documents")

        client.close()
        return metrics_count > 0

    except Exception as e:
        print(f"❌ MongoDB check failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("MongoDB Data Import Tool")
    print("=" * 50)

    if import_mongo_data():
        if check_mongo_data():
            print("\n🎉 MongoDB data is ready! Now you can run: streamlit run app.py")
        else:
            print("\n❌ MongoDB data import may have issues")
    else:
        print("\n❌ MongoDB data import failed")