
import os
import base64
import cv2
from database import get_connection
from deep_learning.face.register_face import FaceRegistration
import numpy as np
from deep_learning.face.verify_face import FaceVerifier
from deep_learning.face.mtcnn_detector import FaceDetector
from deep_learning.monitoring.warning_manager import WarningManager
from deep_learning.object_detection import detect_objects

from flask import (    Blueprint, render_template, session, redirect,  request,  jsonify)


face = Blueprint("face", __name__)
face_detector = FaceDetector()
DATASET_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset", "students")

face_verifier = None


@face.route("/face_registration")
def face_registration():
    if "student_id" not in session:
        return redirect("/login")

    return render_template("face_registration.html")


@face.route("/save_face_images", methods=["POST"])
def save_face_images():
    if "student_id" not in session:
        return jsonify({   "success": False,  "message": "Please log in first."  }), 401

    data = request.get_json(silent=True)

    if not data or not isinstance(data.get("images"), list):
        return jsonify({  "success": False,  "message": "No images received." }), 400

    images = data["images"]

    if len(images) != 30:
        return jsonify({    "success": False,    "message": "Exactly 30 images are required."  }), 400

    student_id = str(session["student_id"])
    student_folder = os.path.join(DATASET_FOLDER, student_id)

    os.makedirs(student_folder, exist_ok=True)

    try:
        for index, image_data in enumerate(images, start=1):
            if not isinstance(image_data, str):
                raise ValueError("Invalid image data.")

            if not image_data.startswith( "data:image/jpeg;base64," ):
                raise ValueError("Invalid image format.")

            encoded_data = image_data.split(",", 1)[1]
            image_bytes = base64.b64decode( encoded_data, validate=True   )

            image_path = os.path.join(  student_folder,   f"{index}.jpg" )

            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)

    except (ValueError, base64.binascii.Error):
        return jsonify({  "success": False, "message": "Invalid image data. Please try again."  }), 400

    student_id = session["student_id"]

    registration = FaceRegistration()

    success, message = registration.register_student(student_id)

    if not success:
        return jsonify({  "success": False,   "message": message  }), 400
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE students
        SET face_registered = TRUE
        WHERE student_id = %s
        """,   (student_id,)   )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({  "success": True, "message": " face registered successfully." })

@face.route("/verify_student_face", methods=["POST"])
def verify_student_face():

    if "student_id" not in session:
        return jsonify({     "success": False,     "message": "Login required."   }), 401

    data = request.get_json(silent=True) or {}
    image = data.get("image", "")
    if not isinstance(image, str) or "," not in image:
        return jsonify({"success": False, "message": "A valid camera image is required."}), 400

    try:
        image_bytes = base64.b64decode(image.split(",", 1)[1], validate=True)
    except (ValueError, base64.binascii.Error):
        return jsonify({"success": False, "message": "Invalid camera image data."}), 400

    image_array = np.frombuffer(   image_bytes,   dtype=np.uint8  )

    frame = cv2.imdecode(  image_array,   cv2.IMREAD_COLOR    )
    if frame is None:
        return jsonify({"success": False, "message": "Could not read the camera image."}), 400

    global face_verifier
    if face_verifier is None:
        face_verifier = FaceVerifier()

    faces = face_detector.detect_faces(frame)
    object_result = detect_objects(frame)
    face_boxes = [  {"box": [x, y, x + w, y + h], "kind": "face", "label": "Face"}
        for x, y, w, h in faces  ]

    detections = face_boxes + object_result.get("detections", [])
    if len(faces) == 1:
        verified, similarity = face_verifier.verify_student(frame, session["student_id"])
    else:
        verified, similarity = False, 0.0

    if not verified:
        manager = WarningManager()
        if len(faces) == 1:
            warning = manager.add_warning(session["student_id"], "Face Verification Failed")
        else:
            warning = manager.current_count(session["student_id"])
        exam_terminated = len(faces) == 1 and warning >= 3

        return jsonify({ "success": False,
            "warning": warning,
            "terminated": exam_terminated,
            "similarity": float(similarity),
            "face_count": len(faces),
            "faces": face_boxes,
            "detections": detections,
            "objects": object_result["objects"]     })

    WarningManager.clear_candidate(session["student_id"])
    session["exam_face_verified"] = True
    return jsonify({"success": True,
        "face_count": 1,
        "faces": [{**face_boxes[0], "label": "Verified face"}],
        "detections": [{**item, "label": "Verified face"} if item.get("kind") == "face" else item for item in detections],
        "objects": object_result["objects"],
        "warning": 0,
        "terminated": False,
        "similarity": float(similarity)  })

@face.route("/validate_face_images", methods=["GET"])
def validate_face_images():
    if "student_id" not in session:
        return redirect("/login")

    student_id = str(session["student_id"])
    student_folder = os.path.join(
        DATASET_FOLDER,
        student_id
    )

    if not os.path.isdir(student_folder):
        return jsonify({
            "success": False,
            "message": "No registered images found."
        }), 404

    detected_count = 0
    total_count = 30

    for index in range(1, total_count + 1):
        image_path = os.path.join(
            student_folder,
            f"{index}.jpg"
        )

        if not os.path.isfile(image_path):
            continue

        image = cv2.imread(image_path)

        if image is None:
            continue

        detected_faces = face_detector.detect_faces(image)
        if len(detected_faces) == 1:
            detected_count += 1

    if detected_count >= 24:
        return jsonify({
            "success": True,
            "message": "Face image validation passed.",
            "detected_images": detected_count,
            "total_images": total_count
        })

    return jsonify({
        "success": False,
        "message": (
            "Face validation failed. Each image must show only "
            "your face in good lighting. Please capture again."
        ),
        "detected_images": detected_count,
        "total_images": total_count
    }), 400

@face.route("/camera_frame", methods=["POST"])
def camera_frame():

    if "student_id" not in session:
        return jsonify({  "status": "Login Required",    "warnings": 0,  "suspicious": False    }), 401

    data = request.get_json(silent=True) or {}
    image = data.get("image", "")
    if not isinstance(image, str) or "," not in image:
        return jsonify({"status": "Invalid camera image", "warnings": 0, "suspicious": False}), 400
    try:
        image_bytes = base64.b64decode(image.split(",", 1)[1], validate=True)
    except (ValueError, base64.binascii.Error):
        return jsonify({"status": "Invalid camera image", "warnings": 0, "suspicious": False}), 400

    image_array = np.frombuffer(   image_bytes,    dtype=np.uint8  )

    frame = cv2.imdecode(    image_array, cv2.IMREAD_COLOR  )
    if frame is None:
        return jsonify({"status": "Invalid camera image", "warnings": 0, "suspicious": False}), 400

    object_result = detect_objects(frame)
    faces = face_detector.detect_faces(frame)
    if len(faces) > 1:
        object_result["suspicious"] = True
        object_result["objects"].append("Multiple Faces Detected")

    status = "Monitoring"

    warning = 0

    if len(faces) > 1:
        status = "Multiple Faces Detected"
    elif "cell phone" in object_result["objects"]:
        status = "Cell Phone Detected"
    elif object_result["suspicious"]:

        status = "Suspicious Object Detected"

    if object_result["suspicious"]:

        manager = WarningManager()

        warning = manager.add_warning( session["student_id"],   status)

    else:
        WarningManager.clear_candidate(session["student_id"])

    face_detections = [     {"box": [x, y, x + w, y + h], "kind": "face", "label": "Face"}
        for x, y, w, h in faces]

    detections = face_detections + object_result.get("detections", [])

    return jsonify({ "status": status,
        "warnings": warning,
        "objects": object_result["objects"],
        "detections": detections,
        "face_count": len(faces),
        "suspicious": object_result["suspicious"],  })
