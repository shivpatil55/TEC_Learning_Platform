(function () {
    const root = document.documentElement;
    const saved = localStorage.getItem("tec-theme") || "day";
    root.setAttribute("data-theme", saved);

    function updateButton() {
        const btn = document.getElementById("themeToggleBtn");
        if (!btn) return;
        const current = root.getAttribute("data-theme");
        btn.innerHTML = current === "night" ? "☀️ Day Mode" : "🌙 Night Mode";
    }

    window.toggleTheme = function () {
        const current = root.getAttribute("data-theme");
        const next = current === "night" ? "day" : "night";
        root.setAttribute("data-theme", next);
        localStorage.setItem("tec-theme", next);
        updateButton();
    };

    document.addEventListener("DOMContentLoaded", updateButton);
})();
