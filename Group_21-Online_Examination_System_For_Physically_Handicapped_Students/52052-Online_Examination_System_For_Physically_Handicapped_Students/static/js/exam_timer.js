let examTimerInterval = null;
let examDeadlineKey = null;

function initializeExamTimer() {
    const timeElement = document.getElementById("time");
    if (!timeElement) return;
    const studentId = document.body.dataset.studentId || "student";
    examDeadlineKey = "examDeadline_" + studentId;
    let deadline = Number(sessionStorage.getItem(examDeadlineKey));
    if (!deadline || deadline <= Date.now()) {
        deadline = Date.now() + 30 * 60 * 1000;
        sessionStorage.setItem(examDeadlineKey, String(deadline));
    }

    function updateTimer() {
        const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        timeElement.textContent = String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0");
        if (remaining === 0) {
            clearInterval(examTimerInterval);
            timeElement.textContent = "00:00";
            speak("Time is up. Your exam is being submitted now.");
            window.setTimeout(submitExam, 1000);
        }
    }

    updateTimer();
    examTimerInterval = window.setInterval(updateTimer, 1000);
}

function stopExamTimer() {
    if (examTimerInterval) window.clearInterval(examTimerInterval);
    examTimerInterval = null;
    if (examDeadlineKey) sessionStorage.removeItem(examDeadlineKey);
}
