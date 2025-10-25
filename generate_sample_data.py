import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker
import psycopg2
from pymongo import MongoClient
import time

fake = Faker()

# Create data directories
os.makedirs('postgres', exist_ok=True)
os.makedirs('mongo/dump/smart_fitness', exist_ok=True)

print("Starting to generate sample data...")


# PostgreSQL data generation (unchanged)
def generate_postgres_data():
    print("Generating PostgreSQL data...")

    # User data
    users = []
    for i in range(1, 501):
        users.append({
            'user_id': f'user-{i:04d}',
            'name': fake.name(),
            'email': fake.email(),
            'age': random.randint(18, 70),
            'gender': random.choice(['Male', 'Female']),
            'height_cm': round(random.uniform(150, 190), 1),
            'created_at': fake.date_time_between(start_date='-2y', end_date='now')
        })

    # Coach data
    coaches = []
    specialties = ['Weight Loss', 'Cardio', 'Strength', 'Yoga', 'Nutrition', 'General Fitness']
    for i in range(1, 51):
        coaches.append({
            'coach_id': f'coach-{i:03d}',
            'name': fake.name(),
            'specialty': random.choice(specialties),
            'email': fake.email()
        })

    # User-coach relationships
    user_coach = []
    for user in users[:400]:  # 80% of users have coaches
        user_coach.append({
            'user_id': user['user_id'],
            'coach_id': random.choice(coaches)['coach_id']
        })

    # Goal data
    goals = []
    goal_types = ['weight_loss', 'muscle_gain', 'endurance', 'flexibility', 'general_health']
    for user in users:
        for _ in range(random.randint(1, 3)):
            goal_type = random.choice(goal_types)
            if goal_type == 'weight_loss':
                target = round(random.uniform(50, 90), 1)
            elif goal_type == 'muscle_gain':
                target = round(random.uniform(60, 100), 1)
            else:
                target = round(random.uniform(1, 100), 1)

            goals.append({
                'goal_id': f'goal-{len(goals) + 1:05d}',
                'user_id': user['user_id'],
                'goal_type': goal_type,
                'target_value': target,
                'current_value': round(target * random.uniform(0.3, 1.2), 1),
                'deadline': fake.date_between(start_date='today', end_date='+1y'),
                'status': random.choice(['active', 'completed', 'cancelled']),
                'created_at': fake.date_time_between(start_date='-1y', end_date='now')
            })

    # Activity data
    activities = []
    activity_types = ['running', 'walking', 'cycling', 'swimming', 'yoga', 'weight_training']
    for user in users:
        for _ in range(random.randint(3, 8)):
            activity_type = random.choice(activity_types)
            duration = random.randint(15, 120)
            base_calories = {'running': 10, 'walking': 4, 'cycling': 8, 'swimming': 12, 'yoga': 3, 'weight_training': 6}
            calories = int(duration * base_calories[activity_type] * random.uniform(0.8, 1.2))

            activities.append({
                'activity_id': f'act-{len(activities) + 1:06d}',
                'user_id': user['user_id'],
                'activity_type': activity_type,
                'duration_min': duration,
                'calories_burned': calories,
                'distance_km': round(duration * random.uniform(0.08, 0.15), 2) if activity_type in ['running',
                                                                                                    'walking',
                                                                                                    'cycling'] else 0,
                'date': fake.date_time_between(start_date='-90d', end_date='now')
            })

    # Health metrics
    health_metrics = []
    metric_types = ['weight', 'heart_rate', 'blood_pressure', 'sleep_quality', 'steps']
    for user in users:
        user_height = user['height_cm']
        base_weight = (user_height - 100) * 0.9  # Rough estimate of healthy weight

        for _ in range(random.randint(5, 15)):
            metric_type = random.choice(metric_types)
            if metric_type == 'weight':
                value = round(base_weight * random.uniform(0.8, 1.2), 1)
            elif metric_type == 'heart_rate':
                value = random.randint(60, 100)
            elif metric_type == 'blood_pressure':
                value = f"{random.randint(110, 130)}/{random.randint(70, 85)}"
            elif metric_type == 'sleep_quality':
                value = random.randint(1, 100)
            elif metric_type == 'steps':
                value = random.randint(2000, 15000)

            health_metrics.append({
                'metric_id': f'metric-{len(health_metrics) + 1:06d}',
                'user_id': user['user_id'],
                'metric_type': metric_type,
                'value': value,
                'recorded_at': fake.date_time_between(start_date='-90d', end_date='now')
            })

    # Alert data
    alerts = []
    alert_types = ['high_heart_rate', 'low_activity', 'weight_change', 'sleep_issue', 'goal_achieved']
    for user in users[:100]:  # 20% of users have alerts
        alert_type = random.choice(alert_types)
        if alert_type == 'high_heart_rate':
            message = "Resting heart rate consistently above 100 bpm"
            severity = 'high'
        elif alert_type == 'low_activity':
            message = "Daily steps below target for 7 consecutive days"
            severity = 'medium'
        elif alert_type == 'weight_change':
            message = "Significant weight change detected (>5% in one month)"
            severity = 'medium'
        elif alert_type == 'sleep_issue':
            message = "Poor sleep quality detected (score < 30 for 3+ days)"
            severity = 'low'
        else:
            message = "Congratulations! You've achieved your fitness goal"
            severity = 'info'

        alerts.append({
            'alert_id': f'alert-{len(alerts) + 1:05d}',
            'user_id': user['user_id'],
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'triggered_at': fake.date_time_between(start_date='-30d', end_date='now'),
            'resolved': random.choice([True, False])
        })

    return {
        'users': users,
        'coaches': coaches,
        'user_coach': user_coach,
        'goals': goals,
        'activities': activities,
        'health_metrics': health_metrics,
        'alerts': alerts
    }


def _generate_realistic_value(user_id, metric_type):
    """Generate realistic values based on metric type and user ID"""
    user_num = int(user_id.split('-')[1])
    base = (user_num % 40) + 60  # Base value based on user ID

    if metric_type == 'heart_rate':
        return random.randint(base, base + 20)
    elif metric_type == 'steps':
        return random.randint(max(0, base - 40), base)
    elif metric_type == 'calories_burned':
        return random.randint(max(1, base // 15), base // 8)
    elif metric_type == 'active_minutes':
        return random.randint(max(1, base // 30), base // 20)
    return 0


# MongoDB data generation with improved real-time data
def generate_mongo_data():
    print("Generating MongoDB data...")

    user_metrics = []
    nutrition_logs = []
    sleep_records = []
    real_time_metrics = []

    # User metrics data (sensor data) - unchanged
    for user_id in [f'user-{i:04d}' for i in range(1, 501)]:
        # Height and weight data
        base_height = random.uniform(150, 190)
        base_weight = (base_height - 100) * 0.9

        for _ in range(random.randint(3, 8)):
            # Height sensor data
            user_metrics.append({
                'sensor_id': 'height-001',
                'user_id': user_id,
                'meta': {
                    'sensor_type': 'height',
                    'measurement_unit': 'cm',
                    'device_model': 'HealthTrack Pro',
                    'firmware_version': '2.1.0'
                },
                'ts': fake.date_time_between(start_date='-90d', end_date='now'),
                'height_cm': round(base_height + random.uniform(-0.5, 0.5), 1),
                'measurement_quality': random.choice(['high', 'medium', 'low']),
                'status': 'completed'
            })

            # Weight sensor data
            user_metrics.append({
                'sensor_id': 'weight-001',
                'user_id': user_id,
                'meta': {
                    'sensor_type': 'weight',
                    'measurement_unit': 'kg',
                    'device_model': 'SmartScale X1',
                    'firmware_version': '1.5.2'
                },
                'ts': fake.date_time_between(start_date='-90d', end_date='now'),
                'weight_kg': round(base_weight * random.uniform(0.9, 1.1), 1),
                'body_fat_percentage': round(random.uniform(15, 35), 1),
                'measurement_quality': random.choice(['high', 'medium', 'low']),
                'status': 'completed'
            })

            # Heart rate data
            user_metrics.append({
                'sensor_id': 'hr-001',
                'user_id': user_id,
                'meta': {
                    'sensor_type': 'heart_rate',
                    'measurement_unit': 'bpm',
                    'device_model': 'FitBand Pro',
                    'firmware_version': '3.2.1'
                },
                'ts': fake.date_time_between(start_date='-90d', end_date='now'),
                'heart_rate_bpm': random.randint(60, 100),
                'measurement_quality': random.choice(['high', 'medium', 'low']),
                'status': 'completed'
            })

    # Nutrition logs - unchanged
    meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
    foods = ['Chicken Breast', 'Salmon', 'Brown Rice', 'Broccoli', 'Apple', 'Greek Yogurt', 'Almonds', 'Eggs']

    for user_id in [f'user-{i:04d}' for i in range(1, 501)]:
        for _ in range(random.randint(5, 15)):
            nutrition_logs.append({
                'log_id': f'nutr-{len(nutrition_logs) + 1:06d}',
                'user_id': user_id,
                'meal_type': random.choice(meal_types),
                'food_item': random.choice(foods),
                'calories': random.randint(100, 600),
                'protein_g': round(random.uniform(5, 40), 1),
                'carbs_g': round(random.uniform(10, 80), 1),
                'fat_g': round(random.uniform(2, 30), 1),
                'timestamp': fake.date_time_between(start_date='-30d', end_date='now')
            })

    # Sleep records - unchanged
    for user_id in [f'user-{i:04d}' for i in range(1, 501)]:
        for _ in range(random.randint(10, 20)):
            sleep_duration = random.uniform(4, 9)
            sleep_quality = random.randint(50, 95)

            sleep_records.append({
                'record_id': f'sleep-{len(sleep_records) + 1:06d}',
                'user_id': user_id,
                'date': fake.date_between(start_date='-30d', end_date='now'),
                'sleep_duration_hours': round(sleep_duration, 1),
                'sleep_quality_score': sleep_quality,
                'deep_sleep_minutes': int(sleep_duration * 60 * 0.2 * random.uniform(0.8, 1.2)),
                'light_sleep_minutes': int(sleep_duration * 60 * 0.6 * random.uniform(0.8, 1.2)),
                'rem_sleep_minutes': int(sleep_duration * 60 * 0.2 * random.uniform(0.8, 1.2)),
                'times_awakened': random.randint(0, 5)
            })

    # IMPROVED: Real-time metrics data with better distribution
    print("Generating real-time metrics data...")
    now = datetime.now()

    # Generate substantial data for better demo experience
    for user_index, user_id in enumerate([f'user-{i:04d}' for i in range(1, 501)]):
        # Generate more data for first 100 users
        records_per_user = 100 if user_index < 100 else 30

        for i in range(records_per_user):
            timestamp = now - timedelta(minutes=random.randint(0, 60))  # Data from last hour
            for metric_type in ['heart_rate', 'steps', 'calories_burned', 'active_minutes']:
                real_time_metrics.append({
                    'user_id': user_id,
                    'metric_type': metric_type,
                    'value': _generate_realistic_value(user_id, metric_type),
                    'timestamp': timestamp - timedelta(seconds=random.randint(0, 59)),
                    'device_id': f'device-{random.randint(1, 10):03d}',
                    'session_id': f'session-{random.randint(1000, 9999)}'
                })

    print(f"✅ Generated {len(real_time_metrics)} real-time records")
    return {
        'user_metrics': user_metrics,
        'nutrition_logs': nutrition_logs,
        'sleep_records': sleep_records,
        'real_time_metrics': real_time_metrics
    }


# Save data as JSON files (for subsequent import)
def save_data(postgres_data, mongo_data):
    print("Saving data to files...")

    # Save PostgreSQL data
    for table_name, data in postgres_data.items():
        df = pd.DataFrame(data)
        df.to_csv(f'postgres/{table_name}.csv', index=False)

    # Save MongoDB data
    with open('mongo/user_metrics.json', 'w') as f:
        for doc in mongo_data['user_metrics']:
            f.write(json.dumps(doc, default=str) + '\n')

    with open('mongo/nutrition_logs.json', 'w') as f:
        for doc in mongo_data['nutrition_logs']:
            f.write(json.dumps(doc, default=str) + '\n')

    with open('mongo/sleep_records.json', 'w') as f:
        for doc in mongo_data['sleep_records']:
            f.write(json.dumps(doc, default=str) + '\n')

    # Save real-time metrics data
    with open('mongo/real_time_metrics.json', 'w') as f:
        for doc in mongo_data['real_time_metrics']:
            f.write(json.dumps(doc, default=str) + '\n')

    print("Data generation completed!")
    print(f"PostgreSQL table data saved to postgres/ directory")
    print(f"MongoDB document data saved to mongo/ directory")


# NEW: High-performance real-time data generator
def start_fast_data_generation():
    """Start high-performance real-time data generation"""
    print("🚀 Starting high-performance real-time data generation...")
    print("📊 Generating data for all 500 users every second")
    print("🗑️  Data auto-expires after 7 days (TTL index)")
    print("Press Ctrl+C to stop\n")

    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['vamos_fitness']

        # Setup TTL index for automatic cleanup
        db.real_time_metrics.create_index(
            "timestamp",
            expireAfterSeconds=7 * 24 * 60 * 60  # 7 days
        )

        batch_count = 0
        start_time = time.time()

        while True:
            batch_start = time.time()
            batch_data = []
            current_time = datetime.now()

            # Generate data for all users in batch
            for user_id in [f'user-{i:04d}' for i in range(1, 501)]:
                for metric_type in ['heart_rate', 'steps', 'calories_burned', 'active_minutes']:
                    batch_data.append({
                        'user_id': user_id,
                        'metric_type': metric_type,
                        'value': _generate_realistic_value(user_id, metric_type),
                        'timestamp': current_time,
                        'device_id': f'device-{random.randint(1, 10):03d}',
                        'session_id': f'session-{batch_count:06d}'
                    })

            # Batch insert for performance
            if batch_data:
                db.real_time_metrics.insert_many(batch_data)
                batch_count += 1

                elapsed = time.time() - batch_start
                total_elapsed = time.time() - start_time
                records_per_second = len(batch_data) / elapsed

                print(f"Batch {batch_count}: Inserted {len(batch_data):,} records "
                      f"in {elapsed:.2f}s ({records_per_second:,.0f} records/sec) "
                      f"Total: {batch_count * len(batch_data):,} records")

            # Wait for next second
            time.sleep(max(0, 1.0 - (time.time() - batch_start)))

    except KeyboardInterrupt:
        print(f"\n🛑 Stopped after {batch_count} batches")
        total_records = batch_count * 2000  # 500 users * 4 metrics
        print(f"📈 Total records generated: {total_records:,}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    # Generate sample data
    postgres_data = generate_postgres_data()
    mongo_data = generate_mongo_data()
    save_data(postgres_data, mongo_data)

    print("\n" + "=" * 60)
    print("🚀 Data Generation Options")
    print("=" * 60)

    print("1. Start HIGH-PERFORMANCE real-time data generator (recommended)")
    print("   - Generates data for all 500 users every second")
    print("   - 2,000 records per second (4 metrics × 500 users)")
    print("   - Data auto-expires after 7 days")
    print("2. Exit (data already generated for demo)")

    response = input("\nSelect option : ").strip()

    if response == '1':
        start_fast_data_generation()
    else:
        print("✅ Sample data generation completed!")
        print("🎯 Run 'streamlit run app.py' to start the dashboard")