from pymongo import MongoClient
from .settings import MONGO_URI, DB_NAME

# Initialize MongoDB connection
client = None
db = None
users_collection = None
jobs_collection = None
applications_collection = None
sessions_collection = None
MONGO_CONNECTED = False

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Collections
    users_collection = db['users']
    jobs_collection = db['jobs']
    applications_collection = db['applications']
    sessions_collection = db['sessions']
    
    # Create indexes for better performance
    users_collection.create_index('email', unique=True)
    jobs_collection.create_index('status')
    jobs_collection.create_index('department')
    applications_collection.create_index('job_id')
    applications_collection.create_index('email')
    sessions_collection.create_index('token', unique=True)
    sessions_collection.create_index('expires_at', expireAfterSeconds=0)
    
    # Test connection
    client.admin.command('ping')
    MONGO_CONNECTED = True
    print(f"✅ Connected to MongoDB: {MONGO_URI}")
    print(f"📁 Database: {DB_NAME}")
except Exception as e:
    MONGO_CONNECTED = False
    print(f"❌ MongoDB connection failed: {e}")
    print("⚠️  Make sure MongoDB is running on localhost:27017")
