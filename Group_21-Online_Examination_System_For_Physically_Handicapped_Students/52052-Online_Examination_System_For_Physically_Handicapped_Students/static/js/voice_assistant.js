const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let voiceEnabled = true;
let recognitionStarting = false;
let recognitionAvailable = Boolean(SpeechRecognition);
let ignoreVoiceUntil = 0;
let recognitionRetryCount = 0;
let recognitionRetryTimer = null;
let voiceCommandsEnabled = sessionStorage.getItem("siteVoiceEnabled") === "true";
let voiceListeningActive = true;
// Keep the exam recognizer on the locale that previously handled option commands.
let recognitionLanguage = "en-US";
window.waitingForSubmit = false;

function updateVoiceToggle() {
    const button = document.getElementById("voiceStartButton");
    if (button) {
        button.textContent = "Voice commands: " + (voiceCommandsEnabled ? "On" : "Off");
        button.setAttribute("aria-pressed", String(voiceCommandsEnabled));
    }
}

function toggleVoiceCommands() {
    if (voiceCommandsEnabled && !voiceEnabled) {
        voiceEnabled = true;
        startVoice();
        speak("Retrying voice recognition. Please allow microphone access if your browser asks.");
        return;
    }
    voiceCommandsEnabled = !voiceCommandsEnabled;
    sessionStorage.setItem("siteVoiceEnabled", String(voiceCommandsEnabled));
    updateVoiceToggle();
    if (voiceCommandsEnabled) {
        startVoice();
        speak("Voice commands are on. Say help to hear the exam commands.");
    } else {
        speak("Voice commands are off. Say turn on voice commands to enable them again.");
    }
}

function speak(text) {
    updateVoiceStatus(text);
    if (!("speechSynthesis" in window) || !window.SpeechSynthesisUtterance) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.88;
    utterance.pitch = 1;
    utterance.volume = 1;
    utterance.lang = "en-US";
    utterance.onstart = () => { ignoreVoiceUntil = 0; };
    utterance.onend = () => { ignoreVoiceUntil = Date.now() + 500; };
    window.speechSynthesis.speak(utterance);
}

function speakWarning(text) {
    if (!("speechSynthesis" in window) || window.speechSynthesis.speaking) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.volume = 1;
    utterance.lang = "en-US";
    utterance.onstart = () => { ignoreVoiceUntil = Date.now() + 5000; };
    utterance.onend = () => { ignoreVoiceUntil = Date.now() + 900; };
    window.speechSynthesis.speak(utterance);
}

function greetStudent(name) {
    speak("Welcome " + name + ". Voice assistance is ready. Say help to hear the commands, or say repeat question.");
}

function startVoice() {
    voiceEnabled = true;
    voiceListeningActive = true;
    if (!recognitionAvailable) {
        updateVoiceStatus("Voice recognition is unavailable in this browser. Use the exam buttons.");
        speak("Voice recognition is unavailable. You can use the buttons on the page.");
        return;
    }
    if (recognition) {
        startListening();
        updateVoiceToggle();
        return;
    }
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = recognitionLanguage;
    recognition.onstart = () => {
        recognitionStarting = false;
        recognitionRetryCount = 0;
        updateVoiceStatus("Listening for a command…");
        updateVoiceToggle();
    };
    recognition.onresult = event => {
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
            const result = event.results[index];
            if (!result.isFinal) continue;
            const command = normalizeExamCommand(result[0].transcript);
            if (!command) continue;
            const explicitOptionSelection = /\b(?:select|choose|pick|mark)\s+(?:the\s+)?option\s+(?:a|b|c|d)\b/.test(command);
            const wakeVoiceCommand = isVoiceToggleCommand(command, true);
            if ((window.speechSynthesis?.speaking || Date.now() < ignoreVoiceUntil) &&
                !explicitOptionSelection && !wakeVoiceCommand) {
                updateVoiceStatus("Heard “" + command + "”. Wait until the assistant finishes speaking, then say it again.");
                continue;
            }
            updateVoiceStatus("Heard: " + command);
            handleCommand(command);
        }
    };
    recognition.onerror = event => {
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            voiceEnabled = false;
            updateVoiceStatus("Microphone permission is needed for voice commands. Use the exam buttons.");
            voiceListeningActive = false;
            const button = document.getElementById("voiceStartButton");
            if (button) {
                button.textContent = "Enable microphone access";
                button.setAttribute("aria-pressed", "false");
            }
        } else if (event.error === "language-not-supported" && recognitionLanguage !== "en-US") {
            recognitionLanguage = "en-US";
            recognition.lang = recognitionLanguage;
            updateVoiceStatus("Switching speech recognition language and restarting…");
        } else if (event.error === "network") {
            // Repeatedly restarting on a speech-service failure creates an
            // endless buffering loop. Surface the actual issue and wait for retry.
            voiceEnabled = false;
            voiceListeningActive = false;
            updateVoiceStatus("Voice recognition unavailable. Retry.");
            const button = document.getElementById("voiceStartButton");
            if (button) button.textContent = "Retry";
        } else if (["no-speech", "aborted"].includes(event.error)) {
            // Silence and browser-initiated stops are recoverable; onend restarts
            // recognition while preserving the command mode.
            recognitionRetryCount = Math.min(recognitionRetryCount + 1, 4);
            updateVoiceStatus("No speech detected. Listening again—speak after the assistant finishes.");
        } else {
            updateVoiceStatus("Speech recognition error: " + event.error + ". Tap the voice button to retry.");
            voiceEnabled = false;
            voiceListeningActive = false;
            const button = document.getElementById("voiceStartButton");
            if (button) button.textContent = "Retry voice commands";
        }
    };
    recognition.onend = () => {
        recognitionStarting = false;
        if (voiceListeningActive && !recognitionRetryTimer) {
            const delay = Math.min(8000, 700 * (2 ** recognitionRetryCount));
            recognitionRetryTimer = window.setTimeout(() => {
                recognitionRetryTimer = null;
                startListening();
            }, delay);
        }
    };
    startListening();
}

function startListening() {
    if (!recognition || !voiceEnabled || recognitionStarting) return;
    recognitionStarting = true;
    try {
        recognition.start();
    } catch (error) {
        recognitionStarting = false;
        recognitionRetryCount = Math.min(recognitionRetryCount + 1, 4);
        updateVoiceStatus("Could not start listening. Retry.");
        window.setTimeout(startListening, Math.min(8000, 700 * (2 ** recognitionRetryCount)));
    }
}

function handleCommand(command) {
    command = normalizeExamCommand(command);
    if (isVoiceToggleCommand(command, true)) {
        if (!voiceCommandsEnabled) toggleVoiceCommands();
        else speak("Voice commands are already on. Say help for commands.");
        return;
    }
    if (isVoiceToggleCommand(command, false)) {
        if (voiceCommandsEnabled) toggleVoiceCommands();
        else speak("Voice commands are already off. Say turn on voice commands to enable them.");
        return;
    }
    if (!voiceCommandsEnabled) {
        updateVoiceStatus("Heard: " + command + ". Voice commands are off. Say turn on voice commands, or select the voice toggle.");
        return;
    }
    if (window.waitingForSubmit) {
        if (/\b(yes|yeah|yep|sure|confirm|confirmed|affirmative|correct|go ahead|do it|submit it)\b/.test(command)) {
            submitExam();
        } else if (/\b(no|nope|cancel|don't|do not|not now|keep working)\b/.test(command)) {
            window.waitingForSubmit = false;
            speak("Submission cancelled. Your answers are still here.");
        } else {
            speak("Please say yes to submit or no to cancel.");
        }
        return;
    }

    if (/\b(help|commands|what can i say|voice commands)\b/.test(command)) {
        speak("Say option A, B, C, or D to select an answer. Say lock answer, next question, previous question, repeat question, read options, or submit exam. Submission asks you to say yes or no.");
    } else if (matchesExplicitOptionCommand(command, "A") || matchesOptionCommand(command, "a")) chooseOption("A");
    else if (matchesExplicitOptionCommand(command, "B") || matchesOptionCommand(command, "b")) chooseOption("B");
    else if (matchesExplicitOptionCommand(command, "C") || matchesOptionCommand(command, "c")) chooseOption("C");
    else if (matchesExplicitOptionCommand(command, "D") || matchesOptionCommand(command, "d")) chooseOption("D");
    else if (/\b(lock|save)\s*(my\s*)?(answer|option)?\b/.test(command)) lockAnswer();
    else if (/\b(next|go forward)\s*(question)?\b/.test(command)) nextQuestion();
    else if (/\b(previous|back)\s*(question)?\b/.test(command)) previousQuestion();
    else if (/\b(repeat|read)\s*(the\s*)?question\b/.test(command)) readCurrentQuestion();
    else if (/\b(read|repeat)\s*(the\s*)?options\b/.test(command)) readOptions();
    else if (isSubmitCommand(command)) askSubmitConfirmation();
    else {
        speak("I did not understand that. Say help to hear available commands.");
    }
}

function isVoiceToggleCommand(command, turnOn) {
    const terms = "voice commands?|voice control|voice assistance|voice recognition";
    if (turnOn) {
        return new RegExp("\\b(?:turn|switch|enable|start|activate)\\s+(?:the\\s+)?(?:on\\s+)?(?:" + terms + ")(?:\\s+(?:on|enable|enabled))?\\b").test(command) ||
            new RegExp("\\b(?:" + terms + ")\\s+(?:on|enable|enabled)\\b").test(command);
    }
    return new RegExp("\\b(?:turn|switch|disable|stop|deactivate)\\s+(?:the\\s+)?(?:off\\s+)?(?:" + terms + ")(?:\\s+(?:off|disable|disabled))?\\b").test(command) ||
        new RegExp("\\b(?:" + terms + ")\\s+(?:off|disable|disabled)\\b").test(command);
}

function matchesExplicitOptionCommand(command, letter) {
    const expression = new RegExp("\\b(?:select|choose|pick|mark)\\s+(?:the\\s+)?option\\s+" + letter.toLowerCase() + "\\b");
    return expression.test(command);
}

function normalizeExamCommand(transcript) {
    return String(transcript || "")
        .toLowerCase()
        .replace(/[’']/g, "'")
        .replace(/[^a-z0-9'\s]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function matchesOptionCommand(command, letter) {
    const spokenForms = {
        a: "(?:a|ay|eh|alpha|one|1)",
        b: "(?:b|bee|be|bravo|two|2)",
        c: "(?:c|see|sea|charlie|three|3)",
        d: "(?:d|dee|delta|four|4)"
    }[letter];
    const bareForms = {
        a: "(?:a|ay|eh|alpha)",
        b: "(?:b|bee|be|bravo)",
        c: "(?:c|see|sea|charlie)",
        d: "(?:d|dee|delta)"
    }[letter];
    const prefix = "(?:(?:select|choose|pick|mark|answer|option|choice)\\s+(?:(?:the|option|choice|answer|number|letter|is)\\s+)*)";
    const full = new RegExp("(?:^|\\b)" + prefix + spokenForms + "(?:\\b|$)");
    const short = new RegExp("^(?:" + bareForms + ")$");
    return full.test(command) || short.test(command);
}

function isSubmitCommand(command) {
    return /\b(?:submit|finish|end|turn in|hand in)\b/.test(command) &&
        /\b(?:exam|test|answers?|assessment)\b|^(?:submit|finish|end)$/.test(command);
}
