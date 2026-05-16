document.querySelectorAll(".history-share-btn").forEach((button) => {
    button.addEventListener("click", () => {
        document.getElementById("historyShareSessionId").value = button.dataset.sessionId;
        document.getElementById("historyShareSessionLabel").textContent =
            `Share session from ${button.dataset.sessionDate}.`;
    });
});

document.querySelectorAll(".history-table form").forEach((form) => {
    form.addEventListener("submit", () => {
        const submitButton = form.querySelector("button[type='submit']");
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Deleting...";
        }
    });
});

const historyShareForm = document.querySelector("#historyShareModal form");
if (historyShareForm) {
    historyShareForm.addEventListener("submit", () => {
        const submitButton = historyShareForm.querySelector("button[type='submit']");
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Sharing...";
        }
    });
}
