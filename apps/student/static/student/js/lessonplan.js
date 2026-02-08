document.addEventListener("DOMContentLoaded", () => {

    /* ===============================
       HARD RESET (IMPORTANT)
       =============================== */
    document.querySelectorAll(".lesson-details").forEach(d => {
        d.classList.remove("visible");
    });

    document.querySelectorAll(".lesson-plan-content").forEach(c => {
        c.classList.remove("visible");
    });

    document.querySelectorAll(".toggle-icon").forEach(i => {
        i.textContent = "▶";
    });


    /* ===============================
       MODULE TOGGLE
       =============================== */
    document.querySelectorAll(".module-header").forEach(header => {
        header.addEventListener("click", (e) => {
            e.stopPropagation();

            const moduleCard = header.closest(".module-card");
            const content = moduleCard.querySelector(".lesson-plan-content");
            const icon = header.querySelector(".toggle-icon");

            const isOpen = content.classList.contains("visible");

            // Close ALL modules + ALL session plans
            document.querySelectorAll(".lesson-plan-content.visible").forEach(open => {
                open.classList.remove("visible");
            });

            document.querySelectorAll(".lesson-details.visible").forEach(open => {
                open.classList.remove("visible");
            });

            document.querySelectorAll(".toggle-icon").forEach(i => {
                i.textContent = "▶";
            });

            // Open current module ONLY if it was closed
            if (!isOpen) {
                content.classList.add("visible");
                icon.textContent = "▼";
            }
        });
    });


    /* ===============================
       SESSION → LESSON PLAN TOGGLE
       =============================== */
    document.querySelectorAll(".lesson-item").forEach(item => {
        item.addEventListener("click", (e) => {
            e.stopPropagation();

            const moduleContent = item.closest(".lesson-plan-content");
            const details = item.nextElementSibling;

            if (!details || !details.classList.contains("lesson-details")) return;

            const isOpen = details.classList.contains("visible");

            // Close ALL session plans in THIS module
            moduleContent.querySelectorAll(".lesson-details.visible").forEach(open => {
                open.classList.remove("visible");
            });

            // Toggle clicked session
            if (!isOpen) {
                details.classList.add("visible");
            }
        });
    });

});
