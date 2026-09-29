(function () {
    var STORAGE_KEY = "sgot-theme";
    var LIGHT = "light";
    var DARK = "classic-dark";

    function readStoredTheme() {
        try {
            return window.localStorage.getItem(STORAGE_KEY);
        } catch (error) {
            return null;
        }
    }

    function writeStoredTheme(theme) {
        try {
            window.localStorage.setItem(STORAGE_KEY, theme);
        } catch (error) {
            /* Private mode or blocked storage: theme still applies for this page. */
        }
    }

    function resolveTheme() {
        var saved = readStoredTheme();
        if (saved === LIGHT || saved === DARK) {
            return saved;
        }
        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            return DARK;
        }
        return LIGHT;
    }

    function syncToggleLabel(theme) {
        var button = document.getElementById("sgot-theme-toggle");
        if (!button) {
            return;
        }
        var label = theme === DARK ? "Cambiar a tema claro" : "Cambiar a tema oscuro";
        button.setAttribute("aria-label", label);
        button.setAttribute("title", label);
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        syncToggleLabel(theme);
    }

    applyTheme(resolveTheme());

    function toggleTheme() {
        var current = document.documentElement.getAttribute("data-theme");
        var next = current === DARK ? LIGHT : DARK;
        writeStoredTheme(next);
        applyTheme(next);
    }

    document.addEventListener("DOMContentLoaded", function () {
        var button = document.getElementById("sgot-theme-toggle");
        if (button) {
            syncToggleLabel(document.documentElement.getAttribute("data-theme"));
            button.addEventListener("click", toggleTheme);
        }
    });
})();
