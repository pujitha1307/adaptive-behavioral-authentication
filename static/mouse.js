let mouseBuffer = [];
let isSessionLocked = false;
let pointHistory = [];

// Canvas setup for live trail visualizer
const canvas = document.getElementById("trailCanvas");
let ctx = null;

if (canvas) {
    function resizeCanvas() {
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
    }
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    ctx = canvas.getContext("2d");
}

document.addEventListener("mousemove", (event) => {
    const now = Date.now();
    mouseBuffer.push({
        t: now,
        x: event.clientX,
        y: event.clientY
    });

    if (canvas && ctx) {
        const rect = canvas.getBoundingClientRect();
        const relativeX = event.clientX - rect.left;
        const relativeY = event.clientY - rect.top;
        pointHistory.push({ x: relativeX, y: relativeY, alpha: 1.0 });
        if (pointHistory.length > 60) pointHistory.shift();
    }
});

// Render trail loop
function drawTrail() {
    if (ctx && canvas) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (pointHistory.length > 1) {
            for (let i = 1; i < pointHistory.length; i++) {
                const p1 = pointHistory[i - 1];
                const p2 = pointHistory[i];
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.strokeStyle = `rgba(99, 102, 241, ${p2.alpha})`;
                ctx.lineWidth = 3;
                ctx.shadowColor = "#8b5cf6";
                ctx.shadowBlur = 8;
                ctx.stroke();
                p2.alpha *= 0.95;
            }
        }
    }
    requestAnimationFrame(drawTrail);
}
if (canvas) {
    drawTrail();
}

// Telemetry collection loop every 10 SECONDS
setInterval(() => {
    const count = mouseBuffer.length;
    const capturedEl = document.getElementById("capturedCount");
    if (capturedEl) capturedEl.innerText = count;

    if (count === 0) return;

    fetch("/collect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mouseBuffer)
    })
    .then(res => res.json())
    .then(data => {
        const statusDiv = document.getElementById("status");
        const progressBar = document.getElementById("progressBar");
        const modalBackdrop = document.getElementById("modalBackdrop");
        const modalCardContainer = document.getElementById("modalCardContainer");
        const confidenceValue = document.getElementById("confidenceValue");

        const risk = Math.min(100, Math.max(0, data.risk || 0));
        const confidence = Math.min(100, Math.max(0, data.confidence || 100 - risk));

        if (confidenceValue) {
            confidenceValue.innerText = `${confidence.toFixed(1)}%`;
        }

        if (progressBar) {
            progressBar.style.width = `${risk}%`;

            if (risk < 60) {
                progressBar.style.background = "linear-gradient(90deg, #10b981, #3b82f6)";
            } else if (risk < 90) {
                progressBar.style.background = "linear-gradient(90deg, #f59e0b, #ef4444)";
            } else {
                progressBar.style.background = "linear-gradient(90deg, #ef4444, #7f1d1d)";
            }
        }

        // 🔴 High Risk Warning (> 90%): Dropdown Specified Reason + Re-authentication Credentials Prompt
        if (data.status === "HIGH_RISK_WARNING" || risk >= 90) {
            isSessionLocked = true;

            if (statusDiv) {
                statusDiv.innerText = `Live Risk: ${risk}% | Confidence: ${confidence}% — ⚠️ High Risk Re-Authentication Required`;
                statusDiv.style.color = "#ef4444";
                statusDiv.style.background = "rgba(239, 68, 68, 0.15)";
                statusDiv.style.borderColor = "rgba(239, 68, 68, 0.4)";
            }

            if (modalBackdrop && modalCardContainer) {
                modalCardContainer.innerHTML = `
                    <div class="warning-title" style="font-size: 18px; color: #ef4444; margin-bottom: 6px;">
                        <span>⚠️ HIGH RISK WARNING (Risk: ${risk}% | Confidence: ${confidence}%)</span>
                    </div>
                    <p class="warning-desc" style="font-size: 13px; color: #fca5a5; margin-bottom: 16px; line-height: 1.4;">
                        Severe behavioral anomaly detected. To re-verify your identity, select a reason for this movement pattern and re-enter your login credentials.
                    </p>

                    <label class="form-label">Select Specified Reason:</label>
                    <select id="modalReasonSelect" style="margin-bottom: 12px;">
                        <option value="Using external trackpad / touchpad">Using external trackpad / touchpad</option>
                        <option value="High-DPI gaming mouse / custom DPI sensitivity">High-DPI gaming mouse / custom DPI sensitivity</option>
                        <option value="Hardware jitter or technical latency">Hardware jitter or technical latency</option>
                        <option value="Demonstrating application to colleague">Demonstrating application to colleague</option>
                        <option value="Other / Custom reason">Other / Custom reason (specify below)</option>
                    </select>

                    <label class="form-label">Additional Details (Optional):</label>
                    <input type="text" id="modalReasonDetails" placeholder="Optional details..." style="margin-bottom: 12px;" />

                    <div style="border-top: 1px solid rgba(255,255,255,0.1); margin: 12px 0; padding-top: 10px;">
                        <label class="form-label" style="color: #6366f1;">Re-enter Account Credentials:</label>
                        <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                            <input type="text" id="modalReAuthUser" value="user_01" placeholder="Username" style="flex:1;" />
                            <input type="password" id="modalReAuthPass" placeholder="Enter Password" style="flex:1;" />

                        </div>
                    </div>

                    <div class="action-row">
                        <button class="btn-submit-reason" onclick="submitReAuth()">Re-authenticate & Verify</button>
                        <button class="btn-warning-logout" onclick="logout()">Log Out</button>
                    </div>
                `;
                modalBackdrop.style.display = "flex";
            }
        }
        // 🟡 Step-Up OTP Required (>= 60%): Show PERSISTENT OTP modal until OTP is verified
        else if (data.status === "OTP_REQUIRED" || (risk >= 60 && !isSessionLocked)) {
            isSessionLocked = true;

            if (statusDiv) {
                statusDiv.innerText = `Live Risk: ${risk}% | Confidence: ${confidence}% — 🔐 OTP Required (>= 60%) [LOCKED]`;
                statusDiv.style.color = "#f59e0b";
                statusDiv.style.background = "rgba(245, 158, 11, 0.15)";
                statusDiv.style.borderColor = "rgba(245, 158, 11, 0.4)";
            }

            if (modalBackdrop && modalCardContainer) {
                modalCardContainer.innerHTML = `
                    <div class="warning-title" style="font-size: 18px; color: #f59e0b;">
                        <span>🔐 STEP-UP OTP REQUIRED (Risk: ${risk}% | Confidence: ${confidence}%)</span>
                    </div>
                    <p class="warning-desc" style="font-size: 13px; margin-top: 8px; margin-bottom: 16px; color: #fde68a;">
                        Behavioral risk score crossed 60%. A 6-digit OTP has been generated & logged securely to your terminal log. Enter OTP to unlock session:
                    </p>
                    <div class="input-group">
                        <input type="text" id="modalOtpInput" placeholder="Enter 6-digit OTP" maxLength="6" style="width:100%; padding:12px; font-size:16px; font-weight:bold; letter-spacing:2px; text-align:center; border-radius:10px; background:rgba(0,0,0,0.5); color:#fff; border:1px solid rgba(245,158,11,0.5); margin-bottom:14px; outline:none;" />
                        <div class="action-row">
                            <button class="btn-otp" style="width:100%; padding:12px; font-size:15px;" onclick="submitOTP('modalOtpInput')">Verify OTP & Unlock</button>
                        </div>
                    </div>
                `;
                modalBackdrop.style.display = "flex";
            }
        }
        // 🟢 Authenticated Normal (< 60%)
        else if (data.status === "AUTHENTICATED" && !isSessionLocked) {
            if (statusDiv) {
                statusDiv.innerText = `Live Risk Score: ${risk}% | Confidence: ${confidence}% — Authenticated (Normal)`;
                statusDiv.style.color = "#10b981";
                statusDiv.style.background = "rgba(16, 185, 129, 0.1)";
                statusDiv.style.borderColor = "rgba(16, 185, 129, 0.3)";
            }
            if (modalBackdrop) modalBackdrop.style.display = "none";
        }
    })
    .catch(err => {
        console.error("Error sending telemetry:", err);
    });

    mouseBuffer = [];
}, 10000);

function submitOTP(inputId = "modalOtpInput") {
    const otpInput = document.getElementById(inputId);
    const otp = otpInput ? otpInput.value.trim() : "";

    if (!otp) {
        alert("Please enter the 6-digit OTP.");
        return;
    }

    fetch("/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ otp: otp })
    })
    .then(res => res.json())
    .then(result => {
        if (result.result === "OTP_VERIFIED") {
            alert("✅ OTP Verified successfully. Session Unlocked!");
            isSessionLocked = false;
            const modalBackdrop = document.getElementById("modalBackdrop");
            if (modalBackdrop) modalBackdrop.style.display = "none";

            const statusDiv = document.getElementById("status");
            if (statusDiv) {
                statusDiv.innerText = "OTP Verified — Access Granted";
                statusDiv.style.color = "#10b981";
                statusDiv.style.background = "rgba(16, 185, 129, 0.1)";
            }
        } else {
            alert("❌ Invalid OTP. Please try again.");
        }
    })
    .catch(err => {
        console.error("Error verifying OTP:", err);
    });
}

function submitReAuth() {
    const reasonSelect = document.getElementById("modalReasonSelect");
    const reasonDetails = document.getElementById("modalReasonDetails");
    const userInput = document.getElementById("modalReAuthUser");
    const passInput = document.getElementById("modalReAuthPass");

    const reason = reasonSelect ? reasonSelect.value : "";
    const details = reasonDetails ? reasonDetails.value.trim() : "";
    const username = userInput ? userInput.value.trim() : "";
    const password = passInput ? passInput.value.trim() : "";

    if (!username || !password) {
        alert("Please enter both Username and Password to re-authenticate.");
        return;
    }

    fetch("/verify-credentials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username: username,
            password: password,
            reason: reason,
            details: details
        })
    })
    .then(res => res.json())
    .then(result => {
        if (result.result === "CREDENTIALS_VERIFIED") {
            alert("✅ Re-authentication Successful! Reason logged & session unlocked.");
            isSessionLocked = false;
            const modalBackdrop = document.getElementById("modalBackdrop");
            if (modalBackdrop) modalBackdrop.style.display = "none";

            const statusDiv = document.getElementById("status");
            if (statusDiv) {
                statusDiv.innerText = "Identity Re-verified — Monitoring Resumed";
                statusDiv.style.color = "#38bdf8";
                statusDiv.style.background = "rgba(56, 189, 248, 0.1)";
            }
        } else {
            alert("❌ Invalid Credentials. (Default user: user_01 / password: password123)");
        }
    })
    .catch(err => {
        console.error("Error verifying credentials:", err);
    });
}

function logout() {
    isSessionLocked = false;
    fetch("/logout", { method: "POST" })
    .then(() => {
        window.location.href = "/";
    })
    .catch(() => {
        window.location.href = "/";
    });
}
