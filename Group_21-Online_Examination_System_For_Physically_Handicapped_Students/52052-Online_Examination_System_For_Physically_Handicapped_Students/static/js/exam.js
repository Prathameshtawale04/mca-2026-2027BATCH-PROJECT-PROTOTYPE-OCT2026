let currentQuestion = 0;
let questionBoxes = [];
let totalQuestions = 0;
let answersLocked = {};

function initializeExam() {
    questionBoxes = Array.from(document.querySelectorAll(".question-box"));
    totalQuestions = questionBoxes.length;
    questionBoxes.forEach(box => box.classList.remove("active"));
    questionBoxes.forEach((box, index) => {
        box.querySelectorAll("input[type='radio']").forEach(radio => {
            radio.addEventListener("change", () => {
                if (answersLocked[index]) {
                    radio.checked = radio.value === answersLocked[index];
                    speak("This answer is locked. Say previous question or next question to continue.");
                }
            });
        });
    });
    if (totalQuestions) questionBoxes[0].classList.add("active");
    updateProgress();
}

function updateProgress() {
    const current = document.getElementById("currentQuestion");
    if (current && totalQuestions) current.textContent = currentQuestion + 1;
}

function chooseOption(option) {
    const box = questionBoxes[currentQuestion];
    if (!box || answersLocked[currentQuestion]) {
        speak("This answer is locked. Say previous question or next question to continue.");
        return;
    }
    const radio = box.querySelector("input[value='" + option + "']");
    if (!radio) return;
    // Trigger the native interaction first, then enforce the checked state for
    // browsers that do not update hidden or assistive-technology-triggered radios.
    radio.click();
    if (!radio.checked) {
        radio.checked = true;
        radio.dispatchEvent(new Event("change", { bubbles: true }));
    }
    updateVoiceStatus("Option " + option + " selected");
    speak("Option " + option + " selected");
}

function lockAnswer() {
    const box = questionBoxes[currentQuestion];
    if (!box) return false;
    const selected = box.querySelector("input[type='radio']:checked");
    if (!selected) {
        speak("Please select an option first.");
        return false;
    }
    answersLocked[currentQuestion] = selected.value;
    box.classList.add("locked");
    const option = selected.value;
    updateVoiceStatus("Option " + option + " locked");
    const optionText = selected.closest("label")?.innerText.trim() || ("Option " + option);
    speak(optionText + " locked for this question.");
    return true;
}

function showQuestion(index, shouldRead = true) {
    if (index < 0 || index >= totalQuestions) return false;
    questionBoxes[currentQuestion]?.classList.remove("active");
    currentQuestion = index;
    questionBoxes[currentQuestion].classList.add("active");
    updateProgress();
    if (shouldRead) readCurrentQuestion();
    return true;
}

function nextQuestion() {
    if (currentQuestion >= totalQuestions - 1) {
        speak("You are on the last question. Say submit exam when you are ready.");
        return;
    }
    showQuestion(currentQuestion + 1);
}

function previousQuestion() {
    if (currentQuestion === 0) {
        speak("You are on the first question.");
        return;
    }
    showQuestion(currentQuestion - 1);
}

function readCurrentQuestion() {
    const box = questionBoxes[currentQuestion];
    if (!box) return;
    const question = box.querySelector(".question-text")?.innerText.trim() || "";
    const labels = Array.from(box.querySelectorAll("label"));
    const options = labels.map(label => label.innerText.trim()).join(". ");
    speak("Question " + (currentQuestion + 1) + ". " + question + ". Options are. " + options);
}

function readOptions() {
    const box = questionBoxes[currentQuestion];
    if (!box) return;
    const options = Array.from(box.querySelectorAll("label"))
        .map(label => label.innerText.trim()).join(". ");
    speak("Options are. " + options);
}

function askSubmitConfirmation() {
    if (!totalQuestions) return;
    if (window.waitingForSubmit) {
        speak("Submission confirmation is already waiting. Say yes to submit or no to cancel.");
        return;
    }
    window.waitingForSubmit = true;
    speak("Are you sure you want to submit your examination? Say yes to submit or no to cancel.");
}

function submitExam() {
    const form = document.getElementById("examForm");
    if (!form || form.dataset.submitting === "true") return;
    form.dataset.submitting = "true";
    if (typeof stopExamTimer === "function") stopExamTimer();
    window.waitingForSubmit = false;
    speak("Submitting your examination now.");
    window.setTimeout(() => form.requestSubmit(), 900);
}

function updateVoiceStatus(message) {
    const status = document.getElementById("voiceStatus");
    if (status) status.textContent = message;
}
