const video = document.getElementById("video");
const overlay = document.getElementById("faceOverlay");
const overlayContext = overlay.getContext("2d");
const verifyButton = document.getElementById("verifyButton");
sessionStorage.removeItem("examDeadline_" + (document.body.dataset.studentId || "student"));

navigator.mediaDevices.getUserMedia({
    video: true
})
.then(function(stream){

    video.srcObject = stream;

});

function verifyFace() {
    if (verifyButton.disabled || !video.videoWidth || !video.videoHeight) return;
    verifyButton.disabled = true;
    document.getElementById("message").textContent = "Checking your face…";

    const canvas = document.createElement("canvas");

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    context.drawImage(
        video,
        0,
        0
    );

    const image = canvas.toDataURL("image/jpeg");

    fetch("/verify_student_face", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            image: image

        })

    })

    .then(response => response.json())

    .then(data => {

        drawDetections(data.detections || data.faces || [], data.face_count || 0);

        if (data.success) {
            document.getElementById("message").textContent = "Face verified. Starting your exam…";
            window.siteSpeak?.("Face verified. Starting your exam.");
            window.setTimeout(() => window.location.href = "/exam", 2300);

        }

        else {

            document.getElementById("message").textContent = data.face_count > 1
                ? "More than one face detected. Please make sure only you are in the camera view."
                : data.face_count === 0
                    ? "No face detected. Move into the camera view and try again."
                    : "Face verification failed. Please adjust your position and try again.";
            window.siteSpeak?.(document.getElementById("message").textContent);

        }

        if (!data.success) verifyButton.disabled = false;

    })
    .catch(() => {
        document.getElementById("message").textContent = "Could not verify the camera image. Please try again.";
        verifyButton.disabled = false;
    });

}

function drawDetections(detections, faceCount) {
    if (!video.videoWidth || !video.videoHeight) return;
    overlay.width = video.videoWidth;
    overlay.height = video.videoHeight;
    overlayContext.clearRect(0, 0, overlay.width, overlay.height);
    detections.forEach(detection => {
        const [x1, y1, x2, y2] = detection.box;
        overlayContext.strokeStyle = detection.kind === "face"
            ? (faceCount > 1 ? "#ef4444" : "#22c55e")
            : "#f59e0b";
        overlayContext.lineWidth = Math.max(3, overlay.width / 180);
        overlayContext.strokeRect(x1, y1, x2 - x1, y2 - y1);
        overlayContext.font = "bold 18px Arial";
        overlayContext.fillStyle = overlayContext.strokeStyle;
        const confidence = Number.isFinite(detection.confidence)
            ? " " + Math.round(detection.confidence * 100) + "%" : "";
        overlayContext.fillText((detection.label || "Detected") + confidence, x1 + 4, Math.max(22, y1 - 8));
    });
}
