(function () {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const panel = document.createElement("aside");
    panel.className = "site-voice-panel";
    panel.innerHTML = '<button type="button" id="siteVoiceToggle" aria-pressed="false">Voice commands: Off</button><span id="siteVoiceStatus" aria-live="polite">Say “turn on voice commands” or use the toggle.</span>';
    document.body.prepend(panel);
    document.body.classList.add("has-site-voice");

    const toggle = panel.querySelector("button");
    const status = panel.querySelector("span");
    let recognition = null;
    let enabled = sessionStorage.getItem("siteVoiceEnabled") === "true";
    let starting = false;
    let permissionBlocked = false;
    let ignoreUntil = 0;

    function updateToggle() {
        toggle.textContent = "Voice commands: " + (enabled ? "On" : "Off");
        toggle.setAttribute("aria-pressed", String(enabled));
        status.textContent = enabled
            ? "Listening. Say help for commands."
            : "Voice commands are off. Listening for “turn on voice commands”.";
    }

    window.siteSpeak = function (message) {
        status.textContent = message;
        if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(message);
        utterance.lang = "en-US";
        utterance.rate = 0.9;
        utterance.volume = 1;
        utterance.onstart = () => { ignoreUntil = Date.now() + Math.min(60000, Math.max(4000, message.length * 120)); };
        utterance.onend = () => { ignoreUntil = Date.now() + 600; };
        window.speechSynthesis.speak(utterance);
    };

    function pageHelp() {
        if (document.getElementById("loginForm")) return "Enter your email and password, then say login. Say register to create an account.";
        if (document.getElementById("registerForm")) return "Fill in your registration details, then say register to create your account.";
        if (document.getElementById("agree")) return "Say agree to check the instruction box, then say start exam to continue to face verification.";
        if (document.getElementById("verifyButton")) return "Say verify face to check your face and continue to the exam.";
        if (document.getElementById("startBtn") && document.getElementById("video")) return "Say start registration to capture your face. Keep only your face in the camera view.";
        if (document.querySelector("a[href='/start_exam']")) return "Say start exam, face registration, profile, results, or logout to navigate.";
        return "Say help to hear the available commands for this page.";
    }

    function navigate(href, message) {
        window.siteSpeak(message);
        window.setTimeout(() => { window.location.href = href; }, 800);
    }

    function setEnabled(value, announce = true) {
        enabled = value;
        sessionStorage.setItem("siteVoiceEnabled", String(enabled));
        updateToggle();
        if (announce) window.siteSpeak(enabled ? pageHelp() : "Voice commands are off. Say turn on voice commands to enable them again.");
        if (enabled) {
            permissionBlocked = false;
            createRecognition();
            beginListening();
        }
    }

    function handleCommand(raw) {
        const command = raw.toLowerCase().trim().replace(/[.!?]/g, "");
        if (/\b(?:turn|switch|enable|start|activate)\s+(?:the\s+)?(?:on\s+)?(?:voice commands?|voice control|voice assistance|voice recognition)(?:\s+(?:on|enabled?))?\b/.test(command) || /\b(?:voice commands?|voice control|voice assistance|voice recognition)\s+(?:on|enabled?)\b/.test(command)) {
            setEnabled(true);
            return;
        }
        if (/\b(?:turn|switch|disable|stop|deactivate)\s+(?:the\s+)?(?:off\s+)?(?:voice commands?|voice control|voice assistance|voice recognition)(?:\s+(?:off|disabled?))?\b/.test(command) || /\b(?:voice commands?|voice control|voice assistance|voice recognition)\s+(?:off|disabled?)\b/.test(command)) {
            setEnabled(false);
            return;
        }
        status.textContent = "Heard: " + command;
        if (!enabled) {
            if (/\b(help|commands)\b/.test(command)) {
                window.siteSpeak("Voice commands are off. Say turn on voice commands, or select the voice toggle.");
            }
            return;
        }
        if (/\b(help|commands)\b/.test(command)) {
            window.siteSpeak(pageHelp());
            return;
        }

        const loginForm = document.getElementById("loginForm");
        if (loginForm && /\b(login|log in|sign in|submit)\b/.test(command)) {
            if (loginForm.reportValidity()) loginForm.requestSubmit();
            else window.siteSpeak("Please fill in your email and password first.");
            return;
        }
        if (loginForm && /\b(register|create account)\b/.test(command)) {
            navigate("/register", "Opening registration.");
            return;
        }
        const registerForm = document.getElementById("registerForm");
        if (registerForm && /\b(register|create account|submit)\b/.test(command)) {
            if (registerForm.reportValidity()) registerForm.requestSubmit();
            else window.siteSpeak("Please complete the required registration fields first.");
            return;
        }

        const agree = document.getElementById("agree");
        if (agree && /\b(agree|accept|yes)\b/.test(command)) {
            agree.checked = true;
            agree.dispatchEvent(new Event("change", { bubbles: true }));
            window.siteSpeak("Instructions accepted. Say start exam when you are ready.");
            return;
        }
        if (agree && /\b(start|begin)\s*(the\s*)?(exam|test)\b/.test(command)) {
            if (!agree.checked) window.siteSpeak("Please say agree first to accept the instructions.");
            else window.startExam();
            return;
        }

        if (document.getElementById("verifyButton") && /\b(verify|verify face|check face)\b/.test(command)) {
            window.siteSpeak("Checking your face now.");
            window.verifyFace();
            return;
        }
        const registrationButton = document.getElementById("startBtn");
        if (registrationButton && document.getElementById("video") && /\b(start|begin|register)\s*(face\s*)?(registration|register)?\b/.test(command)) {
            window.siteSpeak("Starting face registration. Keep your face visible.");
            registrationButton.click();
            return;
        }

        if (/\b(face registration|register face)\b/.test(command)) return navigate("/face_registration", "Opening face registration.");
        if (/\b(start|begin)\s*(the\s*)?(exam|test)\b/.test(command)) return navigate("/start_exam", "Opening exam instructions.");
        if (/\b(profile|my profile)\b/.test(command)) return navigate("/profile", "Opening your profile.");
        if (/\b(results|history|exam history)\b/.test(command)) return navigate("/history", "Opening your exam results.");
        if (/\b(logout|log out|sign out)\b/.test(command)) return navigate("/logout", "Logging out.");
        if (/\b(dashboard|home)\b/.test(command) && !loginForm) return navigate("/dashboard", "Opening the dashboard.");

        if (/\b(show|hide)\s+password\b/.test(command)) {
            const password = document.getElementById("password");
            if (password) {
                password.type = command.includes("show") ? "text" : "password";
                window.siteSpeak(command.includes("show") ? "Password is visible." : "Password is hidden.");
                return;
            }
        }
        window.siteSpeak("I did not understand. Say help to hear the commands for this page.");
    }

    function beginListening() {
        if (!Recognition || !recognition || starting || permissionBlocked) return;
        starting = true;
        try { recognition.start(); }
        catch (error) {
            starting = false;
            status.textContent = "Could not start voice recognition. Select the voice toggle and allow microphone access.";
        }
    }

    function createRecognition() {
        if (!Recognition || recognition) return;
        recognition = new Recognition();
        recognition.lang = "en-US";
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.onstart = () => {
            starting = false;
            status.textContent = enabled ? "Listening for a command… Say help for options." : "Listening for ‘turn on voice commands’ or select the toggle.";
        };
        recognition.onresult = event => {
            for (let index = event.resultIndex; index < event.results.length; index += 1) {
                const result = event.results[index];
                if (!result.isFinal || window.speechSynthesis?.speaking || Date.now() < ignoreUntil) continue;
                handleCommand(result[0].transcript);
            }
        };
        recognition.onerror = event => {
            starting = false;
            if (event.error === "not-allowed" || event.error === "service-not-allowed") {
                permissionBlocked = true;
                status.textContent = "Allow microphone access, or select the voice toggle to try again.";
            } else if (event.error === "audio-capture") {
                permissionBlocked = true;
                status.textContent = "No microphone was found. Connect or enable a microphone, then select the voice toggle.";
            } else if (event.error === "network") {
                permissionBlocked = true;
                status.textContent = "Browser speech service is unavailable. Check your Internet connection and use Chrome or Edge, then select the voice toggle to retry.";
            } else if (event.error !== "no-speech" && event.error !== "aborted") {
                status.textContent = "Voice recognition error: " + event.error + ". Select the voice toggle to retry.";
            }
        };
        recognition.onend = () => {
            starting = false;
            if (!permissionBlocked) window.setTimeout(beginListening, 500);
        };
    }

    toggle.addEventListener("click", () => {
        if (!Recognition) {
            window.siteSpeak("Voice recognition is unavailable in this browser. Please use the buttons and links on the page.");
            return;
        }
        if (enabled && !permissionBlocked) {
            setEnabled(false);
        } else {
            permissionBlocked = false;
            createRecognition();
            setEnabled(true);
            beginListening();
        }
    });

    createRecognition();
    updateToggle();
    if (!Recognition) status.textContent = "Voice recognition is not supported in this browser. Use the page buttons or links.";
    beginListening();
})();
