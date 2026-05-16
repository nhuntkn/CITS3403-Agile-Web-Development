const newPassword = document.getElementById("newPassword");
const confirmPassword = document.getElementById("confirmPassword");

if (newPassword && confirmPassword) {
    const ruleLength = document.getElementById("rule-length");
    const ruleLetter = document.getElementById("rule-letter");
    const ruleSpecial = document.getElementById("rule-special");
    const matchMessage = document.getElementById("matchMessage");
    const resetBtn = document.querySelector("button[value='reset']");

    function setRule(element, valid, text) {
        element.classList.toggle("rule-valid", valid);
        element.classList.toggle("rule-invalid", !valid);
        element.textContent = `${valid ? "OK - " : "- "}${text}`;
    }

    function validatePassword() {
        const pw = newPassword.value;
        const cf = confirmPassword.value;

        setRule(ruleLength, pw.length >= 12, "At least 12 characters");
        setRule(ruleLetter, /[a-zA-Z]/.test(pw), "Contains at least one letter");
        setRule(ruleSpecial, /[!@#$%^&*]/.test(pw), "Contains at least one special character (!@#$%^&*)");

        if (cf === "") {
            matchMessage.textContent = "";
            matchMessage.className = "password-message";
        } else if (pw === cf) {
            matchMessage.textContent = "OK - Passwords match";
            matchMessage.className = "password-message rule-valid";
        } else {
            matchMessage.textContent = "Passwords do not match";
            matchMessage.className = "password-message rule-invalid";
        }

        const valid =
            pw.length >= 12 &&
            /[a-zA-Z]/.test(pw) &&
            /[!@#$%^&*]/.test(pw) &&
            pw === cf;

        if (resetBtn) resetBtn.disabled = !valid;
    }

    newPassword.addEventListener("input", validatePassword);
    confirmPassword.addEventListener("input", validatePassword);
    validatePassword();
}
