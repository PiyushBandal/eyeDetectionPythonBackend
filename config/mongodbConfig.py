from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBConfig:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")  # Read MongoDB URI from environment
        self.client = None

    def connect(self):
        try:
            self.client = MongoClient(self.mongo_uri)  # Connect without specifying a DB
            print("Connected to MongoDB successfully!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")

    def get_client(self):
        if self.client is None:
            self.connect()
        return self.client  # Return the MongoDB client

# Usage Example
if __name__ == "__main__":
    mongo_config = MongoDBConfig()
    mongo_config.connect()
    client = mongo_config.get_client()
    print("Databases:", client.list_database_names())  # List all available databases
