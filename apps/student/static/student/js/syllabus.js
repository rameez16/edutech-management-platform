document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("moduleToggle");
    const content = document.getElementById("moduleContent");
    const arrow = document.getElementById("arrowIcon");

    toggle.addEventListener("click", function () {
        if (content.style.display === "none" || content.style.display === "") {
            content.style.display = "block";
            arrow.classList.add("rotate");
        } else {
            content.style.display = "none";
            arrow.classList.remove("rotate");
        }
    });
});