let video;

let canvas;

let context;
let overlay;
let overlayContext;

let monitoringStarted = false;
let frameInFlight = false;
let lastWarningTime = 0;
let lastWarning = "";

const WARNING_INTERVAL = 10000;

async function startCamera(){

    video = document.getElementById("video");

    canvas = document.getElementById("canvas");

    context = canvas.getContext("2d");
    overlay = document.getElementById("overlay");
    overlayContext = overlay ? overlay.getContext("2d") : null;

    try{

        const stream =
        await navigator.mediaDevices.getUserMedia({

            video:{
                width:{ideal:1280},
                height:{ideal:720},
                frameRate:{ideal:15,max:24}
            },

            audio:false

        });

        video.srcObject = stream;

        await video.play();
        startVerification();
        document.getElementById("cameraStatus").innerHTML =
        "Camera Active";

        if(!monitoringStarted){

            monitoringStarted = true;

            sendFrame();
            setInterval(sendFrame,4000);

        }

    }

    catch(error){

        console.error(error);

        document.getElementById("cameraStatus").innerHTML =
        "Camera Error : " + error.name;

    }

}

function drawDetections(detections, faceCount = 0){
    if(!overlay || !overlayContext || !video.videoWidth || !video.videoHeight) return;
    overlay.width = video.videoWidth;
    overlay.height = video.videoHeight;
    overlayContext.clearRect(0, 0, overlay.width, overlay.height);
    (detections || []).forEach(detection => {
        if(!detection.box || detection.box.length !== 4) return;
        const [x1, y1, x2, y2] = detection.box;
        const color = detection.kind === "face"
            ? (faceCount > 1 ? "#ef4444" : "#22c55e")
            : "#f59e0b";
        overlayContext.strokeStyle = color;
        overlayContext.lineWidth = Math.max(3, overlay.width / 180);
        overlayContext.strokeRect(x1, y1, x2 - x1, y2 - y1);
        const confidence = Number.isFinite(detection.confidence)
            ? " " + Math.round(detection.confidence * 100) + "%" : "";
        const label = (detection.label || "Detected") + confidence;
        overlayContext.font = "bold 18px Arial";
        const textWidth = overlayContext.measureText(label).width;
        const labelY = Math.max(22, y1 - 8);
        overlayContext.fillStyle = color;
        overlayContext.fillRect(x1, labelY - 20, textWidth + 10, 24);
        overlayContext.fillStyle = "#111827";
        overlayContext.fillText(label, x1 + 5, labelY - 3);
    });
}

function sendFrame(){

    if(!video.srcObject || frameInFlight){
        return;
    }

    if(video.readyState !== 4){
        return;
    }

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    let image = canvas.toDataURL("image/jpeg");
    frameInFlight = true;

    fetch("/camera_frame",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            image:image
        })

    })

    .then(response => {
        if(!response.ok) throw new Error("Camera detection request failed (" + response.status + ").");
        return response.json();
    })

    .then(data => {

        drawDetections(data.detections || [], data.face_count || 0);

        document.getElementById("cameraStatus").innerHTML =

            "Status : " +

            data.status +

            "<br>Warnings : " +

            data.warnings;

        const monitor = document.getElementById("monitorStatus");

        if(monitor){

            monitor.innerHTML =

                "Monitoring : " +

                data.status;

            monitor.innerHTML += data.objects && data.objects.length > 0
                ? "<br>Detected: " + data.objects.join(", ")
                : "<br>Detected: no objects in this frame";

        }

        if(data.suspicious && data.warnings > 0){

    const currentTime = Date.now();

    if(
        data.status !== lastWarning ||
        currentTime - lastWarningTime > WARNING_INTERVAL
    ){

        lastWarning = data.status;
        lastWarningTime = currentTime;

       if(!window.warningSpeaking){

    window.warningSpeaking = true;

    speakWarning("Warning. " + data.status);

    setTimeout(function(){

        window.warningSpeaking = false;

    },4000);

}

    }

}
else{

    lastWarning = "";

}

    })

    .catch(error => {

        console.log(error);
        const cameraStatus = document.getElementById("cameraStatus");
        if(cameraStatus) cameraStatus.textContent = "Detection unavailable: " + error.message;

    })
    .finally(() => {
        frameInFlight = false;
    });

}
