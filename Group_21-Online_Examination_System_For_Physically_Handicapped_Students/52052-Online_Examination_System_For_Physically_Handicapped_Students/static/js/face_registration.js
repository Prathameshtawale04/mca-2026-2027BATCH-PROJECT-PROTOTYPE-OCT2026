
const video = document.getElementById("video");
const statusText = document.getElementById("status");
const startBtn = document.getElementById("startBtn");

let stream = null;

function wait(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

startBtn.onclick = async function () {

    startBtn.disabled = true;

    try {
        statusText.textContent = "Opening camera...";
        window.siteSpeak?.("Opening the camera. Keep your face clearly visible.");

        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "user",
                width: { ideal: 640 },
                height: { ideal: 480 }
            },
            audio: false
        });

        video.srcObject = stream;
        await video.play();

        statusText.textContent = "Get ready. Keep your face clearly visible.";
        window.siteSpeak?.("Get ready. Face registration will capture thirty images.");
        await wait(3000);

        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const context = canvas.getContext("2d");
        const images = [];

        for (let i = 0; i < 30; i++) {
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            images.push(canvas.toDataURL("image/jpeg", 0.85));

            statusText.textContent =
                `Capturing images: ${i + 1}/30`;

            await wait(200);
        }

        statusText.textContent = "Uploading images...";
        window.siteSpeak?.("Images captured. Uploading them now.");

        const response = await fetch("/save_face_images", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ images: images })
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || "Upload failed.");
        }

        statusText.textContent = result.message;
        window.siteSpeak?.(result.message);

    } catch (error) {
        statusText.textContent = error.message || "Camera or upload failed.";
        window.siteSpeak?.(error.message || "Camera or upload failed. Please try again.");
        console.error(error);

    } finally {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }

        video.srcObject = null;
        startBtn.disabled = false;
    }
};
