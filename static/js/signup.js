// Reads config from data attributes set by the template
const _cfg = document.getElementById("signup-config").dataset;
const CSRF_TOKEN             = _cfg.csrf;
const verifiedEmailFromServer = JSON.parse(_cfg.verifiedEmail);

// ── Email verification ────────────────────────────────────────────────────

const emailInput        = document.getElementById("emailInput");
const sendCodeBtn       = document.getElementById("sendCodeBtn");
const verifySection     = document.getElementById("verifySection");
const codeInput         = document.getElementById("codeInput");
const verifyCodeBtn     = document.getElementById("verifyCodeBtn");
const emailFeedback     = document.getElementById("emailFeedback");
const codeFeedback      = document.getElementById("codeFeedback");
const verifiedIndicator = document.getElementById("verifiedIndicator");

let emailVerified = false;

function showVerifiedState() {
    verifySection.classList.add("d-none");
    verifiedIndicator.classList.remove("d-none");
    sendCodeBtn.textContent = "Resend Code";
    emailVerified = true;
    checkFormValid();
}

function clearVerifiedState() {
    emailVerified = false;
    verifiedIndicator.classList.add("d-none");
    checkFormValid();
}

// Restore verified state after a server-side validation error re-renders the page
if (verifiedEmailFromServer) {
    showVerifiedState();
}

emailInput.addEventListener("input", () => {
    if (emailVerified && emailInput.value.trim() !== verifiedEmailFromServer) {
        clearVerifiedState();
    }
});

sendCodeBtn.addEventListener("click", async () => {
    const email = emailInput.value.trim();

    if (!email) {
        emailFeedback.textContent = "Please enter an email address";
        emailFeedback.className = "text-danger";
        return;
    }

    emailFeedback.textContent = "";
    sendCodeBtn.disabled = true;
    sendCodeBtn.textContent = "Sending...";

    try {
        const res = await fetch("/api/send_signup_code", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
            body: JSON.stringify({ email })
        });
        const data = await res.json();

        if (!res.ok) {
            emailFeedback.textContent = data.error || "Failed to send code";
            emailFeedback.className = "text-danger";
        } else {
            emailFeedback.textContent = "Code sent! Check your inbox.";
            emailFeedback.className = "text-success";
            verifySection.classList.remove("d-none");
            clearVerifiedState();
            codeInput.value = "";
            codeFeedback.textContent = "";
            codeInput.focus();
        }
    } catch {
        emailFeedback.textContent = "Network error. Please try again.";
        emailFeedback.className = "text-danger";
    }

    sendCodeBtn.disabled = false;
    sendCodeBtn.textContent = "Resend Code";
});

verifyCodeBtn.addEventListener("click", async () => {
    const code  = codeInput.value.trim();
    const email = emailInput.value.trim();

    if (!code) {
        codeFeedback.textContent = "Please enter the verification code";
        codeFeedback.className = "text-danger";
        return;
    }

    verifyCodeBtn.disabled = true;
    verifyCodeBtn.textContent = "Verifying...";

    try {
        const res = await fetch("/api/verify_signup_code", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
            body: JSON.stringify({ code, email })
        });
        const data = await res.json();

        if (!res.ok) {
            codeFeedback.textContent = data.error || "Invalid code";
            codeFeedback.className = "text-danger";
            verifyCodeBtn.disabled = false;
            verifyCodeBtn.textContent = "Verify";
        } else {
            emailFeedback.textContent = "";
            codeFeedback.textContent = "";
            showVerifiedState();
        }
    } catch {
        codeFeedback.textContent = "Network error. Please try again.";
        codeFeedback.className = "text-danger";
        verifyCodeBtn.disabled = false;
        verifyCodeBtn.textContent = "Verify";
    }
});

// ── Password validation ───────────────────────────────────────────────────

const pwd          = document.getElementById("password");
const confirmInput = document.getElementById("confirm");
const submitBtn    = document.getElementById("submitBtn");
const ruleLength   = document.getElementById("rule-length");
const ruleLetter   = document.getElementById("rule-letter");
const ruleSpecial  = document.getElementById("rule-special");

function setRule(el, valid) {
    el.classList.toggle("rule-valid", valid);
    el.classList.toggle("rule-invalid", !valid);
}

pwd.addEventListener("input", () => {
    const value = pwd.value;
    setRule(ruleLength, value.length >= 12);
    setRule(ruleLetter, /[A-Za-z]/.test(value));
    setRule(ruleSpecial, /[!@#$%^&*]/.test(value));
    checkFormValid();
});

confirmInput.addEventListener("input", () => {
    document.getElementById("confirmFeedback").innerText =
        confirmInput.value !== pwd.value ? "Passwords do not match" : "";
    checkFormValid();
});

// ── Username availability check ───────────────────────────────────────────

document.querySelector('input[name="username"]').addEventListener("blur", function () {
    if (!this.value) return;
    fetch(`/check_username?username=${this.value}`)
        .then(r => r.json())
        .then(data => {
            document.getElementById("usernameFeedback").innerText =
                data.exists ? "Username already exists" : "";
        });
});

// ── DOB max date ──────────────────────────────────────────────────────────

const dobInput = document.querySelector('input[name="dob"]');
if (dobInput) {
    dobInput.setAttribute("max", new Date().toISOString().split("T")[0]);
}

// ── Submit gate ───────────────────────────────────────────────────────────

function checkFormValid() {
    const value = pwd.value;
    submitBtn.disabled = !(
        value.length >= 12 &&
        /[A-Za-z]/.test(value) &&
        /[!@#$%^&*]/.test(value) &&
        confirmInput.value === value &&
        emailVerified
    );
}

submitBtn.disabled = true;
