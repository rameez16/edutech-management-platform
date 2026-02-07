document.addEventListener("DOMContentLoaded", () => {
    const moduleHeaders = document.querySelectorAll(".module-header");

    moduleHeaders.forEach(header => {
        header.addEventListener("click", () => {
            const moduleCard = header.closest(".module-card");
            const content = moduleCard.querySelector(".lesson-plan-content");
            const icon = header.querySelector(".toggle-icon");

            // Toggle visibility
            if (content.classList.contains("visible")) {
                content.classList.remove("visible");
                icon.textContent = "▶";
            } else {
                // Optional: close other modules for accordion effect
                document.querySelectorAll(".lesson-plan-content.visible").forEach(openContent => {
                    openContent.classList.remove("visible");
                    openContent.closest(".module-card")
                        .querySelector(".toggle-icon").textContent = "▶";
                });

                content.classList.add("visible");
                icon.textContent = "▼";
            }
        });
    });
});
