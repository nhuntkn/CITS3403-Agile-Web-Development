const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
const csrfJsonHeaders = {
    "Content-Type": "application/json",
    "X-CSRFToken": csrfToken
};

/* ================= PROFILE ================= */

document.getElementById("editToggle").addEventListener("click", function () {
    const s = document.getElementById("editSection");
    s.style.display = s.style.display === "none" ? "block" : "none";
});

document.getElementById("passwordToggle").addEventListener("click", function () {
    const s = document.getElementById("passwordSection");
    s.style.display = s.style.display === "none" ? "block" : "none";
});

document.querySelector('input[name="avatar"]').addEventListener("change", function (event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
        const img = document.getElementById("previewBox");
        img.src = e.target.result;
        img.style.display = "block";
    };
    reader.readAsDataURL(file);
});

const newPassword = document.getElementById("newPassword");
const confirmPassword = document.getElementById("confirmPassword");

function validatePassword() {
    const pw = newPassword.value;
    const len = document.getElementById("rule-length");
    const lettr = document.getElementById("rule-letter");
    const special = document.getElementById("rule-special");

    if (pw.length >= 12) {
        len.style.color = "green";
        len.innerHTML = "OK - At least 12 characters";
    } else {
        len.style.color = "red";
        len.innerHTML = "- At least 12 characters";
    }

    if (/[a-zA-Z]/.test(pw)) {
        lettr.style.color = "green";
        lettr.innerHTML = "OK - Contains at least one letter";
    } else {
        lettr.style.color = "red";
        lettr.innerHTML = "- Contains at least one letter";
    }

    if (/[!@#$%^&*]/.test(pw)) {
        special.style.color = "green";
        special.innerHTML = "OK - Contains at least one special character (!@#$%^&*)";
    } else {
        special.style.color = "red";
        special.innerHTML = "- Contains at least one special character (!@#$%^&*)";
    }

    checkMatch();
}

function checkMatch() {
    const pw = newPassword.value;
    const cf = confirmPassword.value;
    const msg = document.getElementById("matchMessage");

    if (cf === "") {
        msg.innerHTML = "";
    } else if (pw === cf) {
        msg.style.color = "green";
        msg.innerHTML = "OK - Passwords match";
    } else {
        msg.style.color = "red";
        msg.innerHTML = "X - Passwords do not match";
    }

    const valid =
        pw.length >= 12 &&
        /[a-zA-Z]/.test(pw) &&
        /[!@#$%^&*]/.test(pw) &&
        pw === cf;

    document.querySelector("#passwordSection button").disabled = !valid;
}

newPassword.addEventListener("keyup", validatePassword);
confirmPassword.addEventListener("keyup", checkMatch);


/* ================= SECTION SWITCH ================= */

function showSection(type) {
    document.getElementById("profileSection").style.display = (type === "profile") ? "block" : "none";
    document.getElementById("addSection").style.display = (type === "add") ? "block" : "none";

    const btns = document.querySelectorAll(".col-md-2 .btn");
    btns.forEach(btn => {
        btn.classList.remove("btn-secondary");
        btn.classList.add("btn-light");
    });

    if (type === "profile") {
        btns[0].classList.remove("btn-light");
        btns[0].classList.add("btn-secondary");
    }
    if (type === "add") {
        btns[1].classList.remove("btn-light");
        btns[1].classList.add("btn-secondary");
    }
}

document.getElementById("profileSidebarBtn").addEventListener("click", () => showSection("profile"));
document.getElementById("addSidebarBtn").addEventListener("click", () => showSection("add"));


/* ================= ADD FRIEND ================= */

let pending = [];
let friends = [];

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

function searchUsers() {
    const keyword = document.getElementById("searchInput").value;
    if (!keyword.trim()) return;

    fetch(`/api/search_users?query=${keyword}`)
        .then(res => res.json())
        .then(data => renderSearch(data));
}

document.getElementById("searchBtn").addEventListener("click", searchUsers);
document.getElementById("searchInput").addEventListener("keyup", function (e) {
    if (e.key === "Enter") searchUsers();
});

function renderSearch(list) {
    const box = document.getElementById("searchResults");
    box.innerHTML = "";

    if (list.length === 0) {
        box.innerHTML = "<div class='account-empty-message'>No users found</div>";
        return;
    }

    list.forEach(u => {
        const row = document.createElement("div");
        row.className = "d-flex justify-content-between border-bottom py-2";
        row.appendChild(userLine(u));

        const button = document.createElement("button");
        button.className = "btn btn-save btn-sm";
        button.textContent = "Add";
        button.addEventListener("click", () => addFriend(u.username, button));
        row.appendChild(button);

        box.appendChild(row);
    });
}

function addFriend(username, button) {
    fetch("/api/add_friend", {
        method: "POST",
        headers: csrfJsonHeaders,
        body: JSON.stringify({ username: username })
    })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            if (button && data.message === "request sent") {
                button.innerText = "Requested";
                button.disabled = true;
            }
            if (button && data.message === "friend added") {
                button.innerText = "Friends";
                button.disabled = true;
            }
            loadFriends();
        });
}

function renderPending() {
    const box = document.getElementById("pendingList");
    box.innerHTML = "";

    pending.forEach(u => {
        const row = document.createElement("div");
        row.className = "d-flex justify-content-between border-bottom py-2";
        row.appendChild(userLine(u));

        const actions = document.createElement("div");

        const accept = document.createElement("button");
        accept.className = "btn btn-success btn-sm";
        accept.textContent = "Accept";
        accept.addEventListener("click", () => acceptFriend(u.username));

        const reject = document.createElement("button");
        reject.className = "btn btn-danger btn-sm ms-2";
        reject.textContent = "Reject";
        reject.addEventListener("click", () => rejectFriend(u.username));

        actions.appendChild(accept);
        actions.appendChild(reject);
        row.appendChild(actions);
        box.appendChild(row);
    });
}

function acceptFriend(username) {
    fetch("/api/accept_friend", {
        method: "POST",
        headers: csrfJsonHeaders,
        body: JSON.stringify({ username: username })
    }).then(() => loadFriends());
}

function rejectFriend(username) {
    fetch("/api/reject_friend", {
        method: "POST",
        headers: csrfJsonHeaders,
        body: JSON.stringify({ username: username })
    }).then(() => loadFriends());
}

function loadFriends() {
    fetch("/api/friends")
        .then(res => res.json())
        .then(data => {
            pending = data.pending || [];
            friends = data.friends || [];
            renderPending();
            renderFriends();
        });
}

function deleteFriend(username) {
    if (!confirm("Are you sure you want to delete this friend?")) return;

    fetch("/api/delete_friend", {
        method: "POST",
        headers: csrfJsonHeaders,
        body: JSON.stringify({ username: username })
    })
        .then(res => res.json())
        .then(data => {
            alert(data.message || data.error);
            loadFriends();
        });
}

function renderFriends() {
    const box = document.getElementById("friendsList");
    box.innerHTML = "";

    friends.forEach(u => {
        const row = document.createElement("div");
        row.className = "d-flex justify-content-between align-items-center border-bottom py-2";
        row.appendChild(userLine(u));

        const button = document.createElement("button");
        button.className = "btn btn-danger btn-sm";
        button.textContent = "Delete";
        button.addEventListener("click", () => deleteFriend(u.username));

        row.appendChild(button);
        box.appendChild(row);
    });
}

loadFriends();
