let verificationInterval;

function startVerification(){

    setTimeout(function(){

        verifyStudent();

    }, 2000);

    verificationInterval = setInterval(function(){

        verifyStudent();

    }, 60000);

}

function verifyStudent(){

    const canvas = document.createElement("canvas");

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    context.drawImage(video, 0, 0);

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

        if(typeof drawDetections === "function"){
            drawDetections(data.detections || data.faces || [], data.face_count || 0);
        }

        if(!data.success){

    const message = data.face_count > 1
        ? "Multiple faces detected. Please make sure you are alone in view."
        : data.face_count === 0
            ? "Face not detected. Please stay in the camera view."
            : "Face verification failed.";
    document.getElementById("monitorStatus").textContent =
        data.warning > 0 ? "Warning " + data.warning + ": " + message : message;

    if(data.warning > 0){
        speak("Warning " + data.warning + ". " + message);
    }

    if(data.terminated){

        speak(

            "Three warnings reached. Exam will be submitted."

        );

        setTimeout(function(){

            document.getElementById("examForm").submit();

        },3000);

    }

}

        else{

            document.getElementById("monitorStatus").innerHTML =
            "Face verified successfully.";

        }

    })

    .catch(error => {

        console.log(error);

    });

}
