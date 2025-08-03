#!/usr/bin/env python3
"""
Database optimization script for Medical Cabinet Management System
Creates indexes for better query performance
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/cabinet_medical')
client = MongoClient(MONGO_URL)
db = client.get_database()

def optimize_database():
    """Create indexes for better query performance"""
    
    print("🔧 Starting database optimization...")
    
    # Patients collection indexes
    patients_collection = db['patients']
    print("📋 Creating patients indexes...")
    
    # Index for patient search by name
    patients_collection.create_index([('nom', ASCENDING), ('prenom', ASCENDING)])
    print("  ✅ Created: nom + prenom index")
    
    # Index for date_naissance queries (birthday reminders)
    patients_collection.create_index([('date_naissance', ASCENDING)])
    print("  ✅ Created: date_naissance index")
    
    # Index for WhatsApp queries
    patients_collection.create_index([('numero_whatsapp', ASCENDING)])
    print("  ✅ Created: numero_whatsapp index")
    
    # Appointments collection indexes
    appointments_collection = db['appointments']
    print("📅 Creating appointments indexes...")
    
    # Index for date queries (most common)
    appointments_collection.create_index([('date', DESCENDING)])
    print("  ✅ Created: date index")
    
    # Compound index for patient appointments
    appointments_collection.create_index([('patient_id', ASCENDING), ('date', DESCENDING)])
    print("  ✅ Created: patient_id + date index")
    
    # Index for status queries
    appointments_collection.create_index([('statut', ASCENDING)])
    print("  ✅ Created: statut index")
    
    # Index for payment status
    appointments_collection.create_index([('paye', ASCENDING)])
    print("  ✅ Created: paye index")
    
    # Consultations collection indexes
    consultations_collection = db['consultations']
    print("🩺 Creating consultations indexes...")
    
    # Index for patient consultations
    consultations_collection.create_index([('patient_id', ASCENDING), ('date', DESCENDING)])
    print("  ✅ Created: patient_id + date index")
    
    # Index for appointment linkage
    consultations_collection.create_index([('appointment_id', ASCENDING)])
    print("  ✅ Created: appointment_id index")
    
    # Index for vaccine reminders
    consultations_collection.create_index([('rappel_vaccin', ASCENDING), ('date_vaccin', ASCENDING)])
    print("  ✅ Created: rappel_vaccin + date_vaccin index")
    
    # Payments collection indexes
    payments_collection = db['payments']
    print("💰 Creating payments indexes...")
    
    # Index for date queries (billing reports)
    payments_collection.create_index([('date', DESCENDING)])
    print("  ✅ Created: date index")
    
    # Index for patient payments
    payments_collection.create_index([('patient_id', ASCENDING), ('date', DESCENDING)])
    print("  ✅ Created: patient_id + date index")
    
    # Index for payment status
    payments_collection.create_index([('statut', ASCENDING)])
    print("  ✅ Created: statut index")
    
    # Index for insurance queries
    payments_collection.create_index([('assure', ASCENDING)])
    print("  ✅ Created: assure index")
    
    # Users collection indexes
    users_collection = db['users']
    print("👤 Creating users indexes...")
    
    # Index for username (login queries)
    users_collection.create_index([('username', ASCENDING)], unique=True)
    print("  ✅ Created: username unique index")
    
    # Index for role queries
    users_collection.create_index([('role', ASCENDING)])
    print("  ✅ Created: role index")
    
    # Phone messages collection indexes
    phone_messages_collection = db['phone_messages']
    print("📞 Creating phone_messages indexes...")
    
    # Index for date queries
    phone_messages_collection.create_index([('date', DESCENDING)])
    print("  ✅ Created: date index")
    
    # Index for direction and recipient queries
    phone_messages_collection.create_index([('direction', ASCENDING), ('recipient_role', ASCENDING)])
    print("  ✅ Created: direction + recipient_role index")
    
    # Index for priority queries
    phone_messages_collection.create_index([('priority', DESCENDING)])
    print("  ✅ Created: priority index")
    
    print("\n✅ Database optimization completed successfully!")
    
    # Print collection statistics
    print("\n📊 Collection Statistics:")
    collections = ['patients', 'appointments', 'consultations', 'payments', 'users', 'phone_messages']
    
    for collection_name in collections:
        collection = db[collection_name]
        count = collection.count_documents({})
        indexes = list(collection.list_indexes())
        print(f"  {collection_name}: {count} documents, {len(indexes)} indexes")

def analyze_slow_queries():
    """Analyze and suggest optimizations for slow queries"""
    print("\n🔍 Analyzing query patterns...")
    
    # Enable profiling for slow operations (>100ms)
    db.set_profiling_level(1, slow_ms=100)
    print("  ✅ Enabled database profiling for slow queries (>100ms)")
    
    print("  💡 Monitor slow queries in MongoDB logs")
    print("  💡 Use db.system.profile.find() to see profiling data")

if __name__ == "__main__":
    try:
        optimize_database()
        analyze_slow_queries()
        
        print("\n🚀 Database is now optimized for production!")
        print("  📈 Improved query performance")
        print("  🔍 Query profiling enabled")
        print("  💾 Indexes created for all collections")
        
    except Exception as e:
        print(f"❌ Error during optimization: {str(e)}")
        
    finally:
        client.close()