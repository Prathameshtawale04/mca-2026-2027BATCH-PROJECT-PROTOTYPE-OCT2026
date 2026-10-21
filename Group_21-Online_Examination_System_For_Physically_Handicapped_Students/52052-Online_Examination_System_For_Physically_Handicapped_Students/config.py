import os

class Config:
    SECRET_KEY = "your_secret_key"

    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "enter ur password"
    MYSQL_DB = "online_exam_dl"

    UPLOAD_FOLDER = "uploads"

    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "wav"}

    MODEL_FOLDER = "trained_models"

    DATASET_FOLDER = "dataset"

    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480