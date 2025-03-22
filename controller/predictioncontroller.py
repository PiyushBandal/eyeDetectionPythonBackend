import joblib
from app import client
from flask import jsonify, request
from utils.logger import logger

# Load the trained model (assuming the model is saved as 'random_forest_model.pkl')
model = joblib.load('models/random_forest.pkl')

def predict_stress_level():
    """Predict stress level based on input features."""
    logger.info("--------------------Predicting stress level--------------------")
    try:
        # Extract data from the incoming request (expecting JSON format)
        input_features = request.json  # Expecting a dictionary with the feature values

        # Validate input (ensure all required fields are provided)
        required_fields = [
            'snoring_range', 'respiration_rate', 'body_temperature', 
            'limb_movement', 'blood_oxygen', 'heart_rate', 
            'sleep_duration', 'age', 'weight'
        ]
        
        # Check if all required fields are in the input data
        for field in required_fields:
            if field not in input_features:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Prepare the input data for prediction (ensure correct order and format)
        features = [
            input_features.get('snoring_range'),
            input_features.get('respiration_rate'),
            input_features.get('body_temperature'),
            input_features.get('limb_movement'),
            input_features.get('blood_oxygen'),
            input_features.get('heart_rate'),
            input_features.get('sleep_duration'),
            input_features.get('age'),
            input_features.get('weight')
        ]
        
        # Convert to a 2D array (model expects 2D array for prediction)
        features = [features]  # The model expects the data in a 2D array format
        
        # Make the prediction using the trained model
        prediction = model.predict(features)
        predicted_stress_level = int(prediction[0])
        
        input_features['stress_level'] = predicted_stress_level
        
        db = client.data_set
        collection = db.stress_data_set_temp
        
        # Save the data (input features + prediction) into MongoDB
        collection.insert_one(input_features)

        # Return the prediction in the response
        logger.info("--------------------Stress level predicted successfully--------------------")
        return jsonify({"predicted_stress_level": predicted_stress_level})

    except Exception as e:
        # Handle any errors (e.g., malformed input data)
        logger.error("Some error occured while predicting stress level")
        return jsonify({"error": str(e)}), 500
