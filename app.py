from flask import Flask, jsonify
from flask_cors import CORS
from config.mongodbConfig import MongoDBConfig
from routes.routes import routes  # Import the routes from the routes module
import sys
import os
import pandas as pd
import pickle

# Flask app initialization
app = Flask(__name__)
CORS(app)

# MongoDB configuration
mongo_config = MongoDBConfig()
client = mongo_config.get_client()

# Register the routes
app.register_blueprint(routes)

# Global variables
stress_level_model = None
data = None

# Function to load sample data
def load_sample_data():
    global data
    try:
        # Attempt to connect to MongoDB
        db = client.data_set
        collection = db.stress_data_set
        documents = collection.find()
        data = pd.DataFrame(list(documents))
        data.drop(columns=['_id'], inplace=True, errors='ignore')
        
        # Check if the first row is loaded correctly
        if not data.empty:
            print("First row of the dataset:")
            print(data.iloc[0])  # Print the first row
            print("Success: Data loaded correctly")
        else:
            raise ValueError("No data found in the MongoDB collection.")
    
    except errors.ConnectionError as e:
        # Handle the case where MongoDB is not connected
        print(f"Error: MongoDB connection failed. {e}")
        sys.exit(1)  # Terminate the app

    except Exception as e:
        # Handle other potential errors
        print(f"Error: {e}")
        sys.exit(1)  # Terminate the app


    
# Function to load trained models
def load_models():
    global stress_level_model
    model_path = 'models/random_forest.pkl'

    # Check if the model file exists
    if os.path.exists(model_path):
        # Check if the file is non-empty
        if os.path.getsize(model_path) > 0:
            try:
                # Load the model from the pickle file
                with open(model_path, 'rb') as f:
                    stress_level_model = pickle.load(f)
                print("Model loaded successfully.")
            except EOFError:
                print("Model file is empty. Retraining model...")
        else:
            print("Model file is empty. Retraining model...")
    else:
        print("Model file not found. Retraining model...")
        
        
@app.route('/')
def index():
    """Root endpoint."""
    return jsonify({
        "message": "Stress Detection Flask Application",
        "endpoints": {
            "/predict_stress_level": "Predict stress level using input features",
            "/recommendation": "Get recommendations based on similar inputs",
            "/train_stress_level": "Retrain Random Forest model for stress level",
            # "/train_content_based": "Retrain Content-Based model"
            "/adddata":"add the previous data to the original database"
        }
    })

if __name__ == '__main__':
    # Load the models and data before running the app
    # load_sample_data()
    # load_models()

    # Start the Flask app
    port = int(os.environ.get("PORT", 5000))  # Render sets the PORT environment variable
    app.run(host="0.0.0.0", port=port)
