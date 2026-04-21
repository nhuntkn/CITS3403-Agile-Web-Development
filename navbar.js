function loadNavbar(activePage) {
    const container = document.getElementById('navbar');
    if (!container) return;

    const links = [
        { label: 'Dashboard', href: 'dashboard.html', key: 'dashboard' },
        { label: 'Profile', href: 'profile.html', key: 'profile' },
        { label: 'Ranking', href: 'ranking.html', key: 'ranking' },
    ];

    const navLinks = links.map(link => `
        <a href = "${link.href}" class = "ep-nav-link ${activePage === link.key ? 'active' : ''}">
        ${link.label}
        </a>
    `).join('');

    container.innerHTML = `
        <nav class = "ep-navbar">
            <a href = "dashboard.html"  class = "ep-brand">EP</a>
            ${navLinks}
            <a href = "exercise.html" class = "ep-nav-link create-btn ${activePage === 'exercise' ? 'active' : ''}">
                Create Exercise
            </a>
        </nav>
    `;
}