from flask import jsonify
from app import client  # Use the existing MongoDB client
from utils.logger import logger
from config.mongodbConfig import MongoDBConfig

def adddata():
    """Move dataset from temporary collection to the main collection and delete the temporary collection"""
    logger.info("--------------------Adding new data into db--------------------")
    try:
        # Connect to the database and the collections
        mongo_config = MongoDBConfig()
        client = mongo_config.get_client()
        db = client.data_set
        temp_collection = db.stress_data_set_temp
        main_collection = db.stress_data_set
        
        # Fetch all documents from the temp collection
        logger.info("Getting all documents from temp collection")
        temp_data = list(temp_collection.find())


        print(temp_data)

        # Insert documents into the main collection
        logger.info("Inserting temp documents into main collection")
        main_collection.insert_many(temp_data)
        
        # After inserting, delete the temp collection
        logger.info("Deleting temp collection")
        temp_collection.drop()

        logger.info("--------------------Data successfullt added data into db--------------------")
        return jsonify({
            "message": "Data successfully moved from temp to main collection and temp collection deleted."
        })
    
    except Exception as e:
        # Handle any exceptions (e.g., MongoDB connection issues)
        logger.error("Some error occured while adding data into db")
        return jsonify({"error": str(e)}), 500
