from flask import jsonify, request
from utils.logger import logger
from app import client
from bson import ObjectId
import pandas as pd

def recommendation():
    """Content-based filtering to give recommendations based on similar input features."""
    input_features = request.json  # assuming JSON input
    user_id = input_features.get("user_id")

    input_features_impact = {"limb_movement":0.29742103,"snoring_range":0.25524384,"sleep_duration":0.17544529,"blood_oxygen":0.16807567,"respiration_rate":0.03291568,"heart_rate":0.0273243,"age":0.01532486,"body_temperature":0.01414235,"weight":0.01410698}

    # print(input_features)

    # Get the required collection from mongodb
    db = client["test"]
    collection_parameters = db["userparameters"]
    collection_recommendations = db["userrecommendations"]

    # Count user parameter entries
    # user_entries_count = collection.count_documents({"userId": ObjectId(user_id)})

    pipeline = [
    {"$match": {"userId": ObjectId(user_id)}},
    {"$project": {"count": {"$size": "$parameters"}}}
    ]

    # Count of user's parameters
    result = list(collection_parameters.aggregate(pipeline))

    print(result)

    user_entries_count = result[0]['count'] if result else 0

    pipeline = [
    {"$match": {"userId": ObjectId(user_id)}},
    {"$project": {"parameters": 1}}  # Include the parameters array in the output
    ]

    # Array of user parameters
    user_previous_parameters = list(collection_parameters.aggregate(pipeline))

    pipeline = [
    {"$match": {"userId": ObjectId(user_id)}},
    {"$project": {"recommendations": 1}}  # Include the recommendations array in the output
    ]

    # Array of user parameters
    user_previous_recommendations = list(collection_recommendations.aggregate(pipeline))

    print(result)

    # user_entries_count = 60
    logger.info(user_entries_count)

    if user_entries_count >= 50:
        recommendations = generate_recommendations_content(input_features, input_features_impact, user_previous_parameters, user_previous_recommendations)
    else:
        recommendations = generate_cold_recommendations(input_features)
    

    return jsonify({
        "recommendations": recommendations
    })

def generate_recommendations_content(current_parameters, parameter_impact, user_previous_parameters, user_previous_recommendations):
    """
    Generate recommendations using content-based filtering.

    Parameters:
      current_parameters: dict
          The user's current parameter values (e.g., {'param1': 0.8, 'param2': 0.5, ...}).
      parameter_impact: dict
          Mapping of parameter names to their impact weights (e.g., {'param1': 0.7, 'param2': 0.3, ...}).
      user_previous_parameters: DataFrame
          User’s past parameter records, with at least a 'recordedAt' column and parameter columns.
      user_prevous_recommendations: DataFrame
          User’s past recommendations, with at least a 'recommendationDate' column, a 'Technique' column,
          and parameter columns corresponding to those in current_parameters.

    Returns:
      DataFrame
          A DataFrame containing the top 3 recommendations sorted by similarity, with columns 'Technique' and 'Similarity'.
    """
    logger.info("--------------------Generating content-based recommendations--------------------")

    # logger.debug(user_previous_recommendations)

    # Convert lists to DataFrames if necessary.
    # The expected structure is a list with a single document containing a "parameters" key.
    if isinstance(user_previous_parameters, list):
        if user_previous_parameters and 'parameters' in user_previous_parameters[0]:
            # Extract the list of parameter entries from the "parameters" field.
            user_previous_parameters = user_previous_parameters[0]['parameters']
        user_previous_parameters = pd.DataFrame(user_previous_parameters)
    if isinstance(user_previous_recommendations, list):
        if user_previous_recommendations and 'recommendations' in user_previous_recommendations[0]:
            # Extract the list of parameter entries from the "parameters" field.
            user_previous_recommendations = user_previous_recommendations[0]['recommendations']
        user_previous_recommendations = pd.DataFrame(user_previous_recommendations)

    # --- Sort and Aggregate User Parameters ---
    # Sort previous parameters by 'recordedAt' (most recent first)
    sorted_params = user_previous_parameters.sort_values(by="recordedAt", ascending=False)

    # Combine current parameters with the most recent previous parameters (if available)
    if not sorted_params.empty:
        recent_params = sorted_params.iloc[0]
        # Average the current and recent values for each parameter impacted
        combined_params = {}
        for param in parameter_impact.keys():
            current_val = current_parameters.get(param, 0)
            recent_val = recent_params.get(param, 0)
            combined_params[param] = (current_val + recent_val) / 2
    else:
        combined_params = current_parameters.copy()

    # --- Sort User Recommendations ---
    # Sort previous recommendations by 'recommendationDate' (most recent first)
    sorted_recs = user_previous_recommendations.sort_values(by="recommendationDate", ascending=False).copy()

    # --- Compute Similarity Score ---
    # For each recommendation, compute a similarity score based on how close its parameters are to the combined parameters.
    # This placeholder logic assumes parameter values are normalized between 0 and 1.
    def compute_similarity(row):
        similarity = 0
        for param, weight in parameter_impact.items():
            rec_val = row.get(param, 0)          # Get the recommendation's value for this parameter; default to 0 if missing.
            ref_val = combined_params.get(param, 0)  # The target value from combined parameters.
            # A simple similarity measure: the closer the recommendation's parameter is to the target value,
            # the higher the similarity. Multiply by the parameter's impact weight.
            similarity += weight * (1 - abs(rec_val - ref_val))
        return similarity

    sorted_recs['Similarity'] = sorted_recs.apply(compute_similarity, axis=1)

    # --- Final Sorting and Return ---
    # Sort recommendations by similarity (highest first)
    recommendations = sorted_recs.sort_values(by="Similarity", ascending=False)

    # logger.debug(sorted_recs)
    print("content based recoomdations : ")
    print(recommendations[['recommendationText', 'Similarity']].head(3).to_dict(orient='records'))
    logger.info("--------------------Successfully generated content-based recommendations--------------------")

    # Return top 3 recommendations with 'recommendationText' and 'Similarity'
    # return recommendations[['recommendationText', 'Similarity']].head(3).to_dict(orient='records')
    # Get the recommendation text array for the row with the highest similarity score
    best_recommendation_text = recommendations.loc[recommendations['Similarity'].idxmax(), 'recommendationText']

    return best_recommendation_text


def generate_cold_recommendations(input_data):
    """
    Generate personalized recommendations based on user parameters.
    
    Expected input_data keys used for recommendations and their ranges:
      - snoring_range: 0 to 100
      - respiration_rate: 10 to 25
      - body_temperature: 35 to 38 (°C)
      - limb_movement: 0 to 50
      - blood_oxygen: 80 to 100 (%)
      - sleep_duration: 1 to 18 (hours)
      - heart_rate: 40 to 120 (bpm)
      - weight: 40 to 180 (kg)

    Other keys (age, stress_level, deviceInfo, notes, etc.) are logged for context.
    """
    logger.info("--------------------Generating cold recommendations--------------------")
    logger.info(input_data)
    
    detailed_ranges = {
        "snoring_range": [
            (0, 5, "Your snoring is negligible. Maintain good sleep posture."),
            (5, 10, "Very low snoring detected. Keep up your healthy habits."),
            (10, 15, "Minimal snoring observed. Regular exercise can help maintain this level."),
            (15, 20, "Low snoring level. Ensure a balanced diet to support sleep quality."),
            (20, 25, "Slight snoring noted. Consider a pillow adjustment for improved airflow."),
            (25, 30, "Mild snoring observed. Avoid alcohol close to bedtime to reduce snoring."),
            (30, 35, "Mild to moderate snoring detected. Try sleeping on your side."),
            (35, 40, "Moderate snoring level. Consider using nasal strips to ease breathing."),
            (40, 45, "Moderate snoring. Check for allergies that might cause congestion."),
            (45, 50, "Intermediate snoring detected. Adjust your sleep schedule if needed."),
            (50, 55, "Slightly elevated snoring. A humidifier may help keep airways moist."),
            (55, 60, "Elevated snoring level. Monitor your sleep posture and breathing habits."),
            (60, 65, "Noticeable snoring. Consider consulting with a sleep specialist."),
            (65, 70, "Significant snoring. Ensure your sleeping environment is dust-free."),
            (70, 75, "Considerable snoring. Regular exercise might reduce snoring frequency."),
            (75, 80, "High snoring detected. Look into anti-snoring devices for better airflow."),
            (80, 85, "High snoring level. Evaluate your weight management strategies."),
            (85, 90, "Severe snoring. Reduce bedroom allergens and monitor symptoms."),
            (90, 95, "Very severe snoring. A sleep study may be advisable."),
            (95, 100, "Extremely high snoring. Seek professional medical advice immediately.")
        ],
        "respiration_rate": [
            (10, 10.75, "Very slow respiration rate. Check for signs of lethargy."),
            (10.75, 11.5, "Normal low range respiration. Maintain your routine."),
            (11.5, 12.25, "Normal respiration rate. Keep breathing steadily."),
            (12.25, 13, "Normal range respiration. Continue your regular activities."),
            (13, 13.75, "Upper normal respiration rate. Monitor your breathing patterns."),
            (13.75, 14.5, "Slightly elevated respiration. Consider relaxation techniques."),
            (14.5, 15.25, "Elevated respiration rate. Monitor for signs of stress."),
            (15.25, 16, "High respiration rate. Evaluate your breathing rhythm."),
            (16, 16.75, "Noticeably high respiration rate. Slow down and breathe deeply."),
            (16.75, 17.5, "High breathing rate. Consider calming exercises."),
            (17.5, 18.25, "Very high respiration rate. Seek to reduce physical stress."),
            (18.25, 19, "Extremely high respiration rate. Monitor for shortness of breath."),
            (19, 19.75, "Dangerously high respiration rate. Consult a physician promptly."),
            (19.75, 20.5, "Critically high respiration rate. Immediate attention is advised."),
            (20.5, 21.25, "Severely high respiration rate. Seek medical help immediately."),
            (21.25, 22, "Extremely abnormal respiration rate. Medical evaluation is needed."),
            (22, 22.75, "Life-threatening respiration rate. Immediate care is necessary."),
            (22.75, 23.5, "Critical breathing rate. Emergency response required."),
            (23.5, 24.25, "Grave respiration rate. Urgently consult a healthcare professional."),
            (24.25, 25, "Extremely grave respiration rate. Call emergency services immediately.")
        ],
        "body_temperature": [
            (35.0, 35.15, "Very low body temperature. Seek warmth immediately."),
            (35.15, 35.3, "Low body temperature. Consider warm fluids."),
            (35.3, 35.45, "Below normal temperature. Monitor your condition."),
            (35.45, 35.6, "Slightly below normal. Keep warm and monitor your health."),
            (35.6, 35.75, "Low normal body temperature. Maintain your routine."),
            (35.75, 35.9, "Normal body temperature. Keep up healthy habits."),
            (35.9, 36.05, "Normal temperature. Continue your balanced lifestyle."),
            (36.05, 36.2, "Optimal body temperature. Stay hydrated and healthy."),
            (36.2, 36.35, "Ideal body temperature. Maintain your routine."),
            (36.35, 36.5, "Normal high temperature. Monitor for any changes."),
            (36.5, 36.65, "Slightly elevated temperature. Consider light cooling measures."),
            (36.65, 36.8, "Moderate temperature elevation. Stay alert for symptoms."),
            (36.8, 36.95, "Elevated temperature. Monitor closely and rest."),
            (36.95, 37.1, "High temperature. Consider consulting a doctor if it persists."),
            (37.1, 37.25, "Feverish temperature. Take appropriate cooling measures."),
            (37.25, 37.4, "Moderate fever detected. Monitor additional symptoms."),
            (37.4, 37.55, "Elevated fever. Consider seeking medical advice."),
            (37.55, 37.7, "High fever. A medical evaluation is recommended."),
            (37.7, 37.85, "Very high fever. Immediate medical care advised."),
            (37.85, 38.0, "Critical body temperature. Seek emergency medical attention.")
        ],
        "limb_movement": [
            (0, 2.5, "Very stable sleep with minimal limb movement."),
            (2.5, 5.0, "Excellent stability. Minimal movement detected."),
            (5.0, 7.5, "Low limb movement. Sleep quality is good."),
            (7.5, 10.0, "Slight limb movement. Maintain a comfortable sleep environment."),
            (10.0, 12.5, "Moderate minimal movement. Adjust bedding if needed."),
            (12.5, 15.0, "Mild limb movement. Overall, a stable sleep pattern."),
            (15.0, 17.5, "Some limb movement observed. Monitor sleep quality."),
            (17.5, 20.0, "Moderate limb movement. Consider pre-sleep stretching."),
            (20.0, 22.5, "Noticeable limb movement. Check for sleep disturbances."),
            (22.5, 25.0, "Elevated limb movement. Evaluate your sleep conditions."),
            (25.0, 27.5, "High limb movement. Ensure a supportive sleep environment."),
            (27.5, 30.0, "Significant limb movement. Consider relaxation techniques."),
            (30.0, 32.5, "Very high limb movement. Monitor for sleep interruptions."),
            (32.5, 35.0, "High limb movement. Assess your sleep posture."),
            (35.0, 37.5, "Elevated limb movement. A sleep study might be beneficial."),
            (37.5, 40.0, "Noticeably high limb movement. Consider improving sleep stability."),
            (40.0, 42.5, "Excessive limb movement. Evaluate factors affecting your sleep."),
            (42.5, 45.0, "Very excessive limb movement. Consider relaxation exercises."),
            (45.0, 47.5, "Severely high limb movement. Seek improvements in sleep setup."),
            (47.5, 50.0, "Extreme limb movement. Consider professional advice for better sleep.")
        ],
        "blood_oxygen": [
            (80, 81, "Very low blood oxygen level. Consider increasing physical activity."),
            (81, 82, "Low blood oxygen. Ensure adequate iron intake in your diet."),
            (82, 83, "Slightly below optimal oxygen levels. Monitor your respiratory health."),
            (83, 84, "Borderline oxygen level. Practice deep breathing exercises."),
            (84, 85, "Low normal oxygen level. Stay active and well hydrated."),
            (85, 86, "Normal oxygen level. Keep up your current healthy lifestyle."),
            (86, 87, "Normal oxygen level. Maintain regular aerobic activities."),
            (87, 88, "Optimal oxygen level. Continue your balanced diet and exercise."),
            (88, 89, "Good oxygen level. Keep monitoring for consistency."),
            (89, 90, "Very good oxygen level. A slight improvement may help if needed."),
            (90, 91, "Excellent oxygen level. Maintain your healthy practices."),
            (91, 92, "Optimal oxygen saturation. Regular exercise will keep it stable."),
            (92, 93, "High oxygen level. Monitor if any symptoms arise."),
            (93, 94, "Very high oxygen level. Ensure you're not overexerting yourself."),
            (94, 95, "Extremely good oxygen level. Maintain your activity levels."),
            (95, 96, "Near perfect oxygen saturation. Continue with your routine."),
            (96, 97, "Outstanding oxygen level. Keep monitoring for any variations."),
            (97, 98, "Excellent oxygen level. Maintain a healthy diet and exercise."),
            (98, 99, "Almost perfect oxygen saturation. Regular check-ups are advised."),
            (99, 100, "Perfect oxygen level. Keep up the excellent health practices.")
        ],
        "heart_rate": [
            (40, 44, "Very low heart rate. Ensure adequate hydration and rest."),
            (44, 48, "Low heart rate. Maintain a healthy balance of exercise and rest."),
            (48, 52, "Slightly low heart rate. Monitor for any unusual symptoms."),
            (52, 56, "Low-normal heart rate. Keep up your regular exercise routine."),
            (56, 60, "Normal heart rate. Continue with your balanced lifestyle."),
            (60, 64, "Normal heart rate. Good job maintaining a steady rhythm."),
            (64, 68, "Normal heart rate. Continue engaging in moderate activities."),
            (68, 72, "Slightly elevated heart rate. Monitor your physical exertion."),
            (72, 76, "Moderate heart rate. Consider relaxation techniques if needed."),
            (76, 80, "Slightly elevated heart rate. Keep a check on your activity levels."),
            (80, 84, "Mildly high heart rate. Practice stress management techniques."),
            (84, 88, "High-normal heart rate. Regular exercise can help maintain balance."),
            (88, 92, "Elevated heart rate. Monitor your caffeine intake and stress levels."),
            (92, 96, "Moderately high heart rate. Consider mindfulness and relaxation."),
            (96, 100, "High heart rate. Watch your physical activities and rest well."),
            (100, 104, "Very high heart rate. Keep a close eye on your exertion levels."),
            (104, 108, "Extremely high heart rate. Monitor your health closely."),
            (108, 112, "High heart rate. Consider consulting a healthcare professional."),
            (112, 116, "Very high heart rate. Immediate evaluation may be needed if persistent."),
            (116, 120, "Extremely high heart rate. Seek professional advice promptly.")
        ],
        "sleep_duration": [
            # Mapping the original 7-9 hour intervals to the new range [1, 18] using a linear transformation:
            # new_value = 1 + (old_value - 7) * 8.5, where 7 maps to 1 and 9 maps to 18.
            (1, 1.85, "Sleep duration is very short. Consider extending your sleep for better rest."),
            (1.85, 2.7, "Short sleep duration. Aim to add a few minutes to your rest."),
            (2.7, 3.55, "Below optimal sleep. Try going to bed a bit earlier."),
            (3.55, 4.4, "Slightly short sleep. Adjust your schedule to allow more rest."),
            (4.4, 5.25, "Marginally short sleep. A consistent routine may help."),
            (5.25, 6.1, "Approaching optimal sleep. Maintain regular sleep habits."),
            (6.1, 6.95, "Normal sleep duration. Keep up your healthy sleep routine."),
            (6.95, 7.8, "Optimal sleep duration. Your sleep quality is on point."),
            (7.8, 8.65, "Ideal sleep duration. Maintain this habit for overall well-being."),
            (8.65, 9.5, "Great sleep duration. Continue your balanced lifestyle."),
            (9.5, 10.35, "Very good sleep duration. Keep up the routine for optimal health."),
            (10.35, 11.2, "Good sleep duration. A regular schedule benefits your body."),
            (11.2, 12.05, "Slightly extended sleep. Monitor if you feel overslept."),
            (12.05, 12.9, "Long sleep duration. Ensure your sleep quality remains high."),
            (12.9, 13.75, "Moderately long sleep. Maintain a conducive sleep environment."),
            (13.75, 14.6, "Long sleep duration. Balance sleep with daytime productivity."),
            (14.6, 15.45, "Extended sleep duration. Evaluate your overall restfulness."),
            (15.45, 16.3, "Very long sleep. Ensure you remain active during the day."),
            (16.3, 17.15, "Excessive sleep duration. Watch for signs of oversleeping."),
            (17.15, 18, "Excessively long sleep. Consider consulting a professional if needed.")
        ],
        "weight": [
            (40, 47, "Very low weight. Ensure you consume a nutritious, balanced diet."),
            (47, 54, "Low weight. Consider increasing protein and calorie intake for muscle mass."),
            (54, 61, "Below average weight. A balanced diet with healthy fats may help."),
            (61, 68, "Slightly below average weight. Incorporate nutrient-dense foods into your meals."),
            (68, 75, "Near lower normal weight. Maintain your balanced dietary habits."),
            (75, 82, "Normal weight. Continue your current exercise and eating regimen."),
            (82, 89, "Normal weight. Ensure a balanced intake of proteins, carbs, and fats."),
            (89, 96, "Normal weight. Keep monitoring your nutritional needs."),
            (96, 103, "Average weight. Maintain regular physical activity."),
            (103, 110, "Slightly above average weight. Consider portion control in your meals."),
            (110, 117, "Moderately above average weight. A balanced diet and exercise will help."),
            (117, 124, "Above average weight. Monitor your weight with regular exercise."),
            (124, 131, "Slightly high weight. Consider a nutritional consultation for tailored advice."),
            (131, 138, "High weight. Ensure a calorie-controlled diet with regular exercise."),
            (138, 145, "Above normal weight. Monitor portion sizes and engage in regular activity."),
            (145, 152, "High weight. Consider mixing cardio with strength training."),
            (152, 159, "Elevated weight. Maintain a balanced diet and consistent exercise routine."),
            (159, 166, "High weight. Monitor your trends and adjust your diet as needed."),
            (166, 173, "Very high weight. Consider professional guidance for weight management."),
            (173, 180, "Extremely high weight. Seek advice from a nutritionist or dietician.")
        ]
    }

    recommendations = []

    for param, ranges in detailed_ranges.items():
        value = input_data.get(param)
        if value is not None:
            found = False
            for low, high, advice in ranges:
                if low <= value < high:
                    recommendations.append(advice)
                    found = True
                    break
            if not found:
                recommendations.append(f"!!!Value {value} is out of expected range. Consider consulting a professional.")

    logger.info("--------------------Successfully generated cold recommendations--------------------")
    return recommendations


def recommend_technique(user_stress, user_sleep_impact):
    # Convert user profile into a feature vector
    user_profile = np.array([[user_stress, user_sleep_impact, 0.5]])  # Assume average duration

    # Compute cosine similarity between user profile & dataset
    similarity_scores = cosine_similarity(user_profile, df.iloc[:, 1:])[0]

    # Rank recommendations based on similarity scores
    df['Similarity'] = similarity_scores
    recommendations = df.sort_values(by='Similarity', ascending=False)

    return recommendations[['Technique', 'Similarity']].head(3)  # Return top 3 recommendations

# def generate_cold_recommendations(input_data):
#     """Generate general recommendations based on user parameters"""

#     recommendations = []

#     # Define ideal ranges for each parameter
#     ideal_ranges = {
#         "snoring_range": (0, 50),
#         "respiration_rate": (12, 20),
#         "body_temperature": (36.5, 37.5),
#         "limb_movement": (0, 20),
#         "blood_oxygen": (95, 100),
#         "heart_rate": (60, 100),
#         "sleep_duration": (7, 9),
#         "weight": (50, 90)  # Adjust as needed
#     }

#     # Check each parameter and generate recommendations
#     for param, (low, high) in ideal_ranges.items():
#         value = input_data.get(param)

#         if value is not None:
#             if value < low:
#                 recommendations.append(f"Consider increasing {param} to at least {low}.")
#             elif value > high:
#                 recommendations.append(f"Consider reducing {param} to below {high}.")

#     # Stress-level-based recommendations
#     stress_level = input_data.get("stress_level", 0)
#     if stress_level == 0:
#         recommendations.append("Your stress level is low. Keep up the good work!")
#     elif stress_level == 1:
#         recommendations.append("Your stress level is moderate. Try relaxation exercises like deep breathing or yoga.")
#     elif stress_level == 2:
#         recommendations.append("Your stress level is high. Consider regular physical activity and mindfulness practices.")
#     elif stress_level == 3:
#         recommendations.append("Your stress level is very high. Focus on reducing work pressure and getting enough rest.")
#     else:
#         recommendations.append("Your stress level is extremely high. It's essential to consult a healthcare professional.")

#     return recommendations

