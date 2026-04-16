"""
MongoDB connection and database management for BidSentry.
Uses motor (async MongoDB driver) for non-blocking operations.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "bidsentry")


class Database:
    """Singleton database connection manager."""
    
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB."""
        cls.client = AsyncIOMotorClient(MONGODB_URL)
        cls.db = cls.client[MONGODB_DB_NAME]
        
        # Create indexes
        await cls.db.tenders.create_index("created_at")
        await cls.db.bidders.create_index("tender_id")
        await cls.db.evaluations.create_index([("tender_id", 1), ("bidder_id", 1)])
        await cls.db.audit_logs.create_index("timestamp")
        await cls.db.audit_logs.create_index([("entity_type", 1), ("entity_id", 1)])
        await cls.db.llm_cache.create_index("prompt_hash", unique=True)
        
        print(f"✅ Connected to MongoDB: {MONGODB_DB_NAME}")

    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB."""
        if cls.client:
            cls.client.close()
            print("🔌 Disconnected from MongoDB")

    @classmethod
    def get_db(cls):
        """Get database instance."""
        return cls.db

    @classmethod
    def get_collection(cls, name: str):
        """Get a specific collection."""
        return cls.db[name]
