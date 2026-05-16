const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
const csrfJsonHeaders = {
    "Content-Type": "application/json",
    "X-CSRFToken": csrfToken
};

const accountNotice = document.getElementById("accountNotice");
const profileSection = document.getElementById("profileSection");
const addSection = document.getElementById("addSection");
const editToggle = document.getElementById("editToggle");
const passwordToggle = document.getElementById("passwordToggle");
const editSection = document.getElementById("editSection");
const passwordSection = document.getElementById("passwordSection");
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");

let pending = [];
let friends = [];
let searchTimer = null;

function showAccountNotice(message, type = "info") {
    if (!accountNotice || !message) return;

    accountNotice.className = `account-notice alert alert-${type}`;
    accountNotice.textContent = message;
}

function setButtonLoading(button, isLoading, loadingText = "Working...") {
    if (!button) return;

    if (isLoading) {
        button.dataset.originalText = button.textContent;
        button.textContent = loadingText;
        button.disabled = true;
    } else {
        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
    }
}

function togglePanel(panel, button) {
    const isHidden = panel.classList.toggle("account-hidden");
    button.textContent = isHidden ? "Show" : "Hide";
    button.setAttribute("aria-expanded", String(!isHidden));
}

editToggle.addEventListener("click", () => togglePanel(editSection, editToggle));
passwordToggle.addEventListener("click", () => togglePanel(passwordSection, passwordToggle));

const avatarInput = document.querySelector('input[name="avatar"]');
if (avatarInput) {
    avatarInput.addEventListener("change", (event) => {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.type.startsWith("image/")) {
            showAccountNotice("Please choose an image file for your profile picture.", "danger");
            event.target.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.getElementById("previewBox");
            img.src = e.target.result;
            img.classList.remove("account-hidden");
            showAccountNotice("Avatar preview updated. Save changes to keep it.", "info");
        };
        reader.readAsDataURL(file);
    });
}

const editForm = document.getElementById("editSection");
if (editForm) {
    editForm.addEventListener("submit", () => {
        setButtonLoading(editForm.querySelector("button[type='submit']"), true, "Saving...");
    });
}

const newPassword = document.getElementById("newPassword");
const confirmPassword = document.getElementById("confirmPassword");
const passwordSubmit = passwordSection.querySelector("button[type='submit']");

function setPasswordRule(element, valid, text) {
    element.classList.toggle("rule-valid", valid);
    element.classList.toggle("rule-invalid", !valid);
    element.textContent = `${valid ? "OK - " : "- "}${text}`;
}

function validatePassword() {
    const pw = newPassword.value;
    const cf = confirmPassword.value;
    const len = document.getElementById("rule-length");
    const letter = document.getElementById("rule-letter");
    const special = document.getElementById("rule-special");
    const msg = document.getElementById("matchMessage");

    setPasswordRule(len, pw.length >= 12, "At least 12 characters");
    setPasswordRule(letter, /[a-zA-Z]/.test(pw), "Contains at least one letter");
    setPasswordRule(special, /[!@#$%^&*]/.test(pw), "Contains at least one special character (!@#$%^&*)");

    if (!cf) {
        msg.textContent = "";
        msg.className = "password-message";
    } else if (pw === cf) {
        msg.textContent = "OK - Passwords match";
        msg.className = "password-message rule-valid";
    } else {
        msg.textContent = "Passwords do not match";
        msg.className = "password-message rule-invalid";
    }

    const valid =
        pw.length >= 12 &&
        /[a-zA-Z]/.test(pw) &&
        /[!@#$%^&*]/.test(pw) &&
        pw === cf;

    passwordSubmit.disabled = !valid;
}

newPassword.addEventListener("input", validatePassword);
confirmPassword.addEventListener("input", validatePassword);
passwordSubmit.disabled = true;
passwordSection.addEventListener("submit", () => {
    setButtonLoading(passwordSubmit, true, "Updating...");
});

function showSection(type) {
    profileSection.classList.toggle("account-hidden", type !== "profile");
    addSection.classList.toggle("account-hidden", type !== "add");

    const btns = document.querySelectorAll(".account-sidebar .btn");
    btns.forEach(btn => {
        btn.classList.remove("btn-secondary");
        btn.classList.add("btn-light");
    });

    if (type === "profile") {
        btns[0].classList.remove("btn-light");
        btns[0].classList.add("btn-secondary");
    } else {
        btns[1].classList.remove("btn-light");
        btns[1].classList.add("btn-secondary");
    }
}

document.getElementById("profileSidebarBtn").addEventListener("click", () => showSection("profile"));
document.getElementById("addSidebarBtn").addEventListener("click", () => showSection("add"));

function avatarNode(user) {
    const avatar = document.createElement(user.avatar_url ? "img" : "span");
    avatar.className = user.avatar_url ? "user-avatar-small" : "user-avatar-small user-avatar-fallback";
    if (user.avatar_url) {
        avatar.src = user.avatar_url;
        avatar.alt = user.username;
    } else {
        avatar.textContent = user.username ? user.username[0].toUpperCase() : "?";
    }
    return avatar;
}

function userLine(user) {
    const wrapper = document.createElement("div");
    wrapper.className = "account-user-line";
    wrapper.appendChild(avatarNode(user));

    const name = document.createElement("span");
    name.textContent = user.username;
    wrapper.appendChild(name);

    return wrapper;
}

function emptyMessage(text) {
    const message = document.createElement("div");
    message.className = "account-empty-message";
    message.textContent = text;
    return message;
}

function searchUsers() {
    const keyword = searchInput.value.trim();
    const box = document.getElementById("searchResults");

    if (!keyword) {
        box.replaceChildren(emptyMessage("Type a username to search."));
        return;
    }

    setButtonLoading(searchBtn, true, "Searching...");
    box.replaceChildren(emptyMessage("Searching..."));

    fetch(`/api/search_users?query=${encodeURIComponent(keyword)}`)
        .then(res => res.json())
        .then(data => renderSearch(data))
        .catch(() => {
            box.replaceChildren(emptyMessage("Search failed. Please try again."));
        })
        .finally(() => setButtonLoading(searchBtn, false));
}

searchBtn.addEventListener("click", searchUsers);
searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(searchUsers, 350);
});
searchInput.addEventListener("keyup", (event) => {
    if (event.key === "Enter") searchUsers();
});

function renderSearch(list) {
    const box = document.getElementById("searchResults");
    box.replaceChildren();

    if (list.length === 0) {
        box.appendChild(emptyMessage("No users found."));
        return;
    }

    list.forEach(user => {
        const row = document.createElement("div");
        row.className = "account-list-row";
        row.appendChild(userLine(user));

        const button = document.createElement("button");
        button.className = "btn btn-save btn-sm";
        button.type = "button";
        button.textContent = "Add";
        button.addEventListener("click", () => addFriend(user.username, button));
        row.appendChild(button);

        box.appendChild(row);
    });
}

function addFriend(username, button) {
    setButtonLoading(button, true, "Adding...");

    fetch("/api/add_friend", {
        method: "POST",
        headers: csrfJsonHeaders,
        body: JSON.stringify({ username })
    })
        .then(res => res.json())
        .then(data => {
            const message = data.message || data.error || "Request completed.";
            const isSuccess = data.message === "request sent" || data.message === "friend added";
            showAccountNotice(message, isSuccess ? "success" : "warning");

            if (isSuccess) {
                button.textContent = data.message === "friend added" ? "Friends" : "Requested";
                button.disabled = true;
            } else {
                setButtonLoading(button, false);
            }

            loadFriends();
        })
        .catch(() => {
            showAccountNotice("Could not send the friend request. Please try again.", "danger");
            setButtonLoading(button, false);
        });
}

function renderPending() {
    const box = document.getElementById("pendingList");
    box.replaceChildren();

    if (pending.length === 0) {
        box.appendChild(emptyMessage("No pending friend requests."));
        return;
    }

    pending.forEach(user => {
        const row = document.createElement("div");
        row.className = "account-list-row";
        row.appendChild(userLine(user));

        const actions = document.createElement("div");
        actions.className = "account-row-actions";

        const accept = document.createElement("button");
        accept.className = "btn btn-success btn-sm";
        accept.type = "button";
        accept.textContent = "Accept";
        accept.addEventListener("click", () => acceptFriend(user.username, accept));

        const reject = document.createElement("button");
        reject.className = "btn btn-danger btn-sm";
        reject.type = "button";
        reject.textContent = "Reject";
        reject.addEventListener("click", () => rejectFriend(user.username, reject));

        actions.append(accept, reject);
        row.appendChild(actions);
        box.appendChild(row);
    });
}

function acceptFriend(username, button) {
    setButtonLoading(button, true, "Accepting...");
    fetch("/api/accept_friend", {
        method: "POST",
        headers: csrfJsonHeaders,
        body: JSON.stringify({ username })
    })
        .then(() => {
            showAccountNotice("Friend request accepted.", "success");
            loadFriends();
        })
        .catch(() => {
            showAccountNotice("Could not accept the request. Please try again.", "danger");
            setButtonLoading(button, false);
        });
}

function rejectFriend(username, button) {
    setButtonLoading(button, true, "Rejecting...");
    fetch("/api/reject_friend", {
        method: "POST",
        headers: csrfJsonHeaders,
        body: JSON.stringify({ username })
    })
        .then(() => {
            showAccountNotice("Friend request rejected.", "info");
            loadFriends();
        })
        .catch(() => {
            showAccountNotice("Could not reject the request. Please try again.", "danger");
            setButtonLoading(button, false);
        });
}

function loadFriends() {
    fetch("/api/friends")
        .then(res => res.json())
        .then(data => {
            pending = data.pending || [];
            friends = data.friends || [];
            renderPending();
            renderFriends();
        })
        .catch(() => {
            showAccountNotice("Could not load friend data. Please refresh the page.", "danger");
        });
}

function deleteFriend(username, button) {
    if (!confirm("Are you sure you want to delete this friend?")) return;

    setButtonLoading(button, true, "Deleting...");
    fetch("/api/delete_friend", {
        method: "POST",
        headers: csrfJsonHeaders,
        body: JSON.stringify({ username })
    })
        .then(res => res.json())
        .then(data => {
            const message = data.message || data.error || "Friend list updated.";
            showAccountNotice(message, data.error ? "warning" : "success");
            loadFriends();
        })
        .catch(() => {
            showAccountNotice("Could not delete this friend. Please try again.", "danger");
            setButtonLoading(button, false);
        });
}

function renderFriends() {
    const box = document.getElementById("friendsList");
    box.replaceChildren();

    if (friends.length === 0) {
        box.appendChild(emptyMessage("No friends yet. Search for a username above to add one."));
        return;
    }

    friends.forEach(user => {
        const row = document.createElement("div");
        row.className = "account-list-row";
        row.appendChild(userLine(user));

        const button = document.createElement("button");
        button.className = "btn btn-danger btn-sm";
        button.type = "button";
        button.textContent = "Delete";
        button.addEventListener("click", () => deleteFriend(user.username, button));

        row.appendChild(button);
        box.appendChild(row);
    });
}

loadFriends();
