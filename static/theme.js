
const savedTheme = localStorage.getItem("theme");

if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
}

const themeButton = document.getElementById("theme-toggle");

function updateThemeButton() {
    if (document.body.classList.contains("dark-mode")) {
        themeButton.textContent = "☀️ Light mode";
    } else {
        themeButton.textContent = "🌙 Dark mode";
    }
}

updateThemeButton();

themeButton.addEventListener("click", function () {
    const isDark = document.body.classList.toggle("dark-mode");

    localStorage.setItem("theme", isDark ? "dark" : "light");

    updateThemeButton();
});
