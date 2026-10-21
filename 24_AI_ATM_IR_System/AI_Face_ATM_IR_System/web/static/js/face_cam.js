/**
 * Biometric Face Recognition & Webcam Controller
 */

class FaceCameraController {
    constructor(videoElemId, canvasElemId, statusElemId) {
        this.video = document.getElementById(videoElemId);
        this.canvas = document.getElementById(canvasElemId);
        this.statusElem = document.getElementById(statusElemId);
        this.stream = null;
        this.isVerifying = false;
        this.consecutiveSuccess = 0;
        this.requiredFrames = 5;
        this.onVerifiedCallback = null;
    }

    async startCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.updateStatus("Webcam not supported by browser. Use Simulation Mode.", "warning");
            return false;
        }

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }
            });
            this.video.srcObject = this.stream;
            this.updateStatus("Camera Active. Align face inside frame.", "info");
            return true;
        } catch (err) {
            console.warn("Camera access failed:", err);
            this.updateStatus("Camera inaccessible. Simulation Mode enabled.", "warning");
            return false;
        }
    }

    stopCamera() {
        this.isVerifying = false;
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    updateStatus(message, type = "info") {
        if (this.statusElem) {
            this.statusElem.innerText = message;
            this.statusElem.className = `hud-status-bar status-${type}`;
        }
    }

    captureFrameBase64() {
        if (!this.video || this.video.videoWidth === 0) return null;
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        const ctx = this.canvas.getContext("2d");
        ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        return this.canvas.toDataURL("image/jpeg", 0.85);
    }

    async startVerificationLoop(accountNumber, onVerified) {
        this.isVerifying = true;
        this.consecutiveSuccess = 0;
        this.onVerifiedCallback = onVerified;

        const loop = async () => {
            if (!this.isVerifying) return;

            const frameB64 = this.captureFrameBase64();
            if (frameB64) {
                const res = await apiPost("/api/auth/verify_face_frame", {
                    account_number: accountNumber,
                    image_data: frameB64
                });

                if (res.ok && res.data.face_detected) {
                    if (res.data.success) {
                        this.consecutiveSuccess++;
                        const pct = Math.round((this.consecutiveSuccess / this.requiredFrames) * 100);
                        this.updateStatus(`Verifying: ${this.consecutiveSuccess}/${this.requiredFrames} frames (${pct}%)`, "success");

                        if (this.consecutiveSuccess >= this.requiredFrames) {
                            this.isVerifying = false;
                            this.updateStatus("Biometric Match Confirmed!", "success");
                            if (this.onVerifiedCallback) {
                                this.onVerifiedCallback(res.data);
                            }
                            return;
                        }
                    } else {
                        this.consecutiveSuccess = Math.max(0, this.consecutiveSuccess - 1);
                        this.updateStatus(`Confidence low (${res.data.confidence_score}%). Hold still.`, "warning");
                    }
                } else {
                    this.updateStatus(res.data ? res.data.message : "Scanning for face...", "info");
                }
            }

            if (this.isVerifying) {
                setTimeout(loop, 400);
            }
        };

        loop();
    }
}
