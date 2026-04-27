function loadNavbar(activePage) {
    const container = document.getElementById('navbar');
    if (!container) return;

    const links = [
        { label: 'Dashboard', href: 'dashboard.html', key: 'dashboard' },
        { label: 'Ranking', href: 'ranking.html', key: 'ranking' },
        { label: 'History', href: 'history.html', key: 'history' },
    ];

    const navLinks = links.map(link => `
        <a href = "${link.href}" class = "ep-nav-link ${activePage === link.key ? 'active' : ''}">
        ${link.label}
        </a>
    `).join('');

    container.innerHTML = `
        <nav class = "ep-navbar">
            <a href = "dashboard.html"  class = "ep-brand">
                <img src = "/static/images/logo.png') }}" alt="EP">
            </a>
            ${navLinks}
            <a href = "exercise.html" class = "ep-nav-link create-btn ${activePage === 'exercise' ? 'active' : ''}">
                Create Exercise
            </a>
            <div class = "ep-nav-spacer"></div>
            <div class = "ep-user-menu">
                <div class = "ep-user-avatar">J</div>
                <div class = "ep-user-dropdown">
                    <a href = "#" class = "ep-dropdown-item">Profile</a>
                    <a href = "#" class = "ep-dropdown-item">Settings</a>
                    <a href = "/login" class = "ep-dropdown-item">Logout</a>
                </div>
            </div>
        </nav>
    `;
}