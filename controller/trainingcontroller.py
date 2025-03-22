from flask import jsonify
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from config.mongodbConfig import MongoDBConfig
from utils.logger import logger
mongo_config = MongoDBConfig()
client = mongo_config.get_client()

def train_stress_level():
    """Train or retrain Random Forest model for stress level prediction."""
    logger.info("--------------------Training Random forest for detecting stress level--------------------")
    try:
        # Fetch the data from MongoDB
        db = client.data_set
        collection = db.stress_data_set
        logger.info("Getting all documents from db")
        documents = collection.find()
        data = pd.DataFrame(list(documents))
        data.drop(columns=['_id'], inplace=True, errors='ignore')
        # Check if the data is available
        if data.empty:
            logger.info("No data found in db! Cannot train model on no data!")
            return jsonify({
                "message": "No data found in the MongoDB collection.",
                "accuracy": None
            })

        # Prepare the features (X) and target (y)
        # Assuming 'stress_level' is the target column
        X = data.drop(columns=['stress_level'])
        y = data['stress_level']

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Initialize and train the Random Forest model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Make predictions and evaluate accuracy
        logger.info("Making predictions and evaluating accuracy")
        # y_pred = model.predict(X_test)
        # accuracy = accuracy_score(y_test, y_pred)
        # logger.info("Accuracy of mode: ",accuracy)

        # Optionally, save the model for future use (using joblib or pickle)
        logger.info("Saving the trained model")
        joblib.dump(model, 'models/random_forest.pkl')

        logger.info("--------------------Random Forest trained successfully--------------------")
        return jsonify({
            "message": "Random Forest model retrained successfully!",
            # "accuracy": accuracy
        })
    except Exception as e:
        # Handle any exceptions (e.g., MongoDB connection issues)
        logger.error("Some error occured while training Random Forest")
        return jsonify({"error": str(e)}), 500


def train_content_based():
    """Train or retrain Content-Based model."""
    # message = train_content_based_model()
    message :"helllo"
    return jsonify({
        "message": message
    })
