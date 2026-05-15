const newPassword = document.getElementById("newPassword");
const confirmPassword = document.getElementById("confirmPassword");

if (newPassword && confirmPassword) {
    const ruleLength = document.getElementById("rule-length");
    const ruleLetter = document.getElementById("rule-letter");
    const ruleSpecial = document.getElementById("rule-special");
    const matchMessage = document.getElementById("matchMessage");
    const resetBtn = document.querySelector("button[value='reset']");

    function validatePassword() {
        const pw = newPassword.value;

        if (pw.length >= 12) {
            ruleLength.style.color = "green";
            ruleLength.innerHTML = "OK - At least 12 characters";
        } else {
            ruleLength.style.color = "red";
            ruleLength.innerHTML = "- At least 12 characters";
        }

        if (/[a-zA-Z]/.test(pw)) {
            ruleLetter.style.color = "green";
            ruleLetter.innerHTML = "OK - Contains at least one letter";
        } else {
            ruleLetter.style.color = "red";
            ruleLetter.innerHTML = "- Contains at least one letter";
        }

        if (/[!@#$%^&*]/.test(pw)) {
            ruleSpecial.style.color = "green";
            ruleSpecial.innerHTML = "OK - Contains at least one special character (!@#$%^&*)";
        } else {
            ruleSpecial.style.color = "red";
            ruleSpecial.innerHTML = "- Contains at least one special character (!@#$%^&*)";
        }

        checkMatch();
    }

    function checkMatch() {
        const pw = newPassword.value;
        const cf = confirmPassword.value;

        if (cf === "") {
            matchMessage.innerHTML = "";
        } else if (pw === cf) {
            matchMessage.style.color = "green";
            matchMessage.innerHTML = "OK - Passwords match";
        } else {
            matchMessage.style.color = "red";
            matchMessage.innerHTML = "X - Passwords do not match";
        }

        const valid =
            pw.length >= 12 &&
            /[a-zA-Z]/.test(pw) &&
            /[!@#$%^&*]/.test(pw) &&
            pw === cf;

        if (resetBtn) resetBtn.disabled = !valid;
    }

    newPassword.addEventListener("keyup", validatePassword);
    confirmPassword.addEventListener("keyup", checkMatch);
}
