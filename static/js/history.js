document.querySelectorAll(".history-share-btn").forEach((button) => {
    button.addEventListener("click", () => {
        document.getElementById("historyShareSessionId").value = button.dataset.sessionId;
        document.getElementById("historyShareSessionLabel").textContent =
            `Share session from ${button.dataset.sessionDate}.`;
    });
});
