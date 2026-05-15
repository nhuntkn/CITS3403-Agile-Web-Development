const pwd = document.getElementById("password");
const confirmInput = document.getElementById("confirm");
const ruleLength = document.getElementById("rule-length");
const ruleLetter = document.getElementById("rule-letter");
const ruleSpecial = document.getElementById("rule-special");
const submitBtn = document.querySelector("button[type='submit']");

function checkRules() {
    const value = pwd.value;
    ruleLength.style.color = value.length >= 12 ? "green" : "red";
    ruleLetter.style.color = /[A-Za-z]/.test(value) ? "green" : "red";
    ruleSpecial.style.color = /[!@#$%^&*]/.test(value) ? "green" : "red";
}

function checkFormValid() {
    const value = pwd.value;
    const valid =
        value.length >= 12 &&
        /[A-Za-z]/.test(value) &&
        /[!@#$%^&*]/.test(value) &&
        confirmInput.value === value;
    submitBtn.disabled = !valid;
}

pwd.addEventListener("input", () => {
    checkRules();
    checkFormValid();
    const feedback = document.getElementById("confirmFeedback");
    feedback.innerText = confirmInput.value && confirmInput.value !== pwd.value
        ? "Passwords do not match" : "";
});

confirmInput.addEventListener("input", () => {
    const feedback = document.getElementById("confirmFeedback");
    feedback.innerText = confirmInput.value !== pwd.value ? "Passwords do not match" : "";
    checkFormValid();
});

document.querySelector('input[name="username"]').addEventListener("blur", function () {
    const username = this.value;
    if (!username) return;
    fetch(`/check_username?username=${encodeURIComponent(username)}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById("usernameFeedback").innerText =
                data.exists ? "Username already exists" : "";
        });
});

const dobInput = document.querySelector('input[name="dob"]');
if (dobInput) {
    dobInput.setAttribute("max", new Date().toISOString().split("T")[0]);
}

submitBtn.disabled = true;
