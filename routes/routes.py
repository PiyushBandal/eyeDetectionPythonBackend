from flask import Blueprint

# Create Blueprint object
routes = Blueprint('routes', __name__)

# Define the routes and import controller functions within each
@routes.route('/predict_stress_level', methods=['POST'])
def predict_stress_level():
    from controller.predictioncontroller import predict_stress_level
    return predict_stress_level()

@routes.route('/recommendation', methods=['POST'])
def recommendation():
    from controller.reccomdationcontroller import recommendation
    return recommendation()

@routes.route('/addData', methods=['POST'])
def adddata():
    from controller.adddatacontroller import adddata
    return adddata()

@routes.route('/train_stress_level', methods=['GET'])
def train_stress_level():
    from controller.trainingcontroller import train_stress_level
    return train_stress_level()

@routes.route('/train_content_based', methods=['GET'])
def train_content_based():
    from controller.trainingcontroller import train_content_based
    return train_content_based()
