let mouseBuffer = [];
let otpShown = false;

document.addEventListener("mousemove", (event) => {
    mouseBuffer.push({
        t: Date.now(),
        x: event.clientX,
        y: event.clientY
    });
});

setInterval(() => {
    if (mouseBuffer.length === 0) return;

    fetch("/collect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mouseBuffer)
    })
    .then(res => res.json())
    .then(data => {
        const statusDiv = document.getElementById("status");
        const otpBox = document.getElementById("otpBox");

        statusDiv.innerText = `Live Risk Score: ${data.risk}`;

        if (data.status === "AUTHENTICATED") {
            statusDiv.innerText += " — Authenticated";
            otpBox.style.display = "none";
            otpShown = false;
        }

        if (data.status === "OTP_REQUIRED" && !otpShown) {
            statusDiv.innerText += " — OTP Required";
            otpBox.style.display = "block";
            otpShown = true;
        }

        if (data.status === "BLOCKED") {
            statusDiv.innerText = "Access Blocked due to High Risk";
            otpBox.style.display = "none";
        }
    });

    mouseBuffer = [];
}, 3000);

function submitOTP() {
    const otp = document.getElementById("otpInput").value;

    fetch("/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ otp: otp })
    })
    .then(res => res.json())
    .then(result => {
        if (result.result === "OTP_VERIFIED") {
            alert("OTP Verified. Access Granted.");
            document.getElementById("otpBox").style.display = "none";
        } else {
            alert("Invalid OTP.");
        }
    });
}

function logout() {
    fetch("/logout", { method: "POST" })
    .then(() => {
        window.location.href = "/";
    });
}
