import iris
from app.config import IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME, IRIS_PASSWORD

def get_connection():
    return iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME, IRIS_PASSWORD)
