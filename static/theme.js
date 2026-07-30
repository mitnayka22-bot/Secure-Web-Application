const btn = document.getElementById("theme-toggle");

function setTheme(theme) {

    // Bootstrap dark mode
    document.documentElement.setAttribute("data-bs-theme", theme);

    // Custom CSS
    document.documentElement.setAttribute("data-theme", theme);

    localStorage.setItem("theme", theme);

    btn.innerHTML = theme === "dark" ? "☀️" : "🌙";
}

const currentTheme = localStorage.getItem("theme") || "light";

setTheme(currentTheme);

btn.addEventListener("click", () => {

    const theme = document.documentElement.getAttribute("data-theme");

    if (theme === "dark") {
        setTheme("light");
    } else {
        setTheme("dark");
    }

});