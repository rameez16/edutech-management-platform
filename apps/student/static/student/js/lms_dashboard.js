/* ═══════════════════════════════════════════════════════════
   LMS DASHBOARD — lms_dashboard.js
   ═══════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", function () {

    /* ─────────────────────────────────────────────────────────
       1. STAT COUNTER ANIMATION
       Counts up from 0 to the real value on page load
    ───────────────────────────────────────────────────────── */
    const statNumbers = document.querySelectorAll(".lms-stat-number");

    statNumbers.forEach((el, index) => {
        const target = parseInt(el.textContent.trim(), 10);
        if (isNaN(target) || target === 0) return;

        el.textContent = "0";
        let current = 0;
        const duration = 600;
        const steps = 30;
        const increment = Math.ceil(target / steps);
        const delay = index * 80; // stagger each card

        setTimeout(() => {
            const counter = setInterval(() => {
                current = Math.min(current + increment, target);
                el.textContent = current;
                if (current >= target) clearInterval(counter);
            }, duration / steps);
        }, delay);
    });


    /* ─────────────────────────────────────────────────────────
       2. STAT CARD ENTRANCE ANIMATION
    ───────────────────────────────────────────────────────── */
    const statCards = document.querySelectorAll(".lms-stat-card");

    statCards.forEach((card, i) => {
        card.style.opacity = "0";
        card.style.transform = "translateY(18px)";
        card.style.transition = `opacity 0.4s ease ${i * 70}ms, transform 0.4s ease ${i * 70}ms`;

        // Trigger reflow then animate in
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                card.style.opacity = "1";
                card.style.transform = "translateY(0)";
            });
        });
    });


    /* ─────────────────────────────────────────────────────────
       3. MATERIAL CARD SCROLL ANIMATION (IntersectionObserver)
    ───────────────────────────────────────────────────────── */
    const materialCards = document.querySelectorAll(".lms-material-card");

    if ("IntersectionObserver" in window && materialCards.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = "1";
                    entry.target.style.transform = "translateY(0)";
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.06 });

        materialCards.forEach((card, i) => {
            card.style.opacity = "0";
            card.style.transform = "translateY(14px)";
            card.style.transition = `opacity 0.35s ease ${(i % 8) * 40}ms, transform 0.35s ease ${(i % 8) * 40}ms`;
            observer.observe(card);
        });
    }


    /* ─────────────────────────────────────────────────────────
       4. FILTER TABS — instant active feedback before navigation
       The server renders the correct active class via Django,
       but this gives visual feedback while the page loads.
    ───────────────────────────────────────────────────────── */
    const filterBtns = document.querySelectorAll(".lms-filter-btn");

    filterBtns.forEach(btn => {
        btn.addEventListener("click", function () {
            filterBtns.forEach(b => b.classList.remove("active"));
            this.classList.add("active");
        });
    });


    /* ─────────────────────────────────────────────────────────
       5. STICKY FILTER TABS on scroll
       Sticks the filter tab row to top with frosted glass effect
    ───────────────────────────────────────────────────────── */
    const filterTabsEl = document.querySelector(".lms-filter-tabs");

    if (filterTabsEl) {
        // Record natural position before any stickiness
        const stickyThreshold = filterTabsEl.getBoundingClientRect().top + window.scrollY - 16;

        window.addEventListener("scroll", function () {
            if (window.scrollY > stickyThreshold) {
                filterTabsEl.classList.add("lms-filters-sticky");
            } else {
                filterTabsEl.classList.remove("lms-filters-sticky");
            }
        }, { passive: true });
    }


    /* ─────────────────────────────────────────────────────────
       6. VIEW TRACKING — POST to track-view endpoint on button click
       Attach to all .lms-btn-primary that have data-material-id
       (Add data-material-id="{{ material.id }}" to buttons in HTML)
    ───────────────────────────────────────────────────────── */
    document.querySelectorAll(".lms-btn-primary[data-material-id]").forEach(btn => {
        btn.addEventListener("click", function () {
            const id = this.dataset.materialId;
            if (!id) return;
            fetch(`/student/lms/material/${id}/track-view/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCookie("csrftoken") },
                keepalive: true,
            }).catch(() => {});
        });
    });


    /* ─────────────────────────────────────────────────────────
       7. DOWNLOAD TRACKING — POST to track-download endpoint
    ───────────────────────────────────────────────────────── */
    document.querySelectorAll(".lms-btn-secondary[data-material-id]").forEach(btn => {
        btn.addEventListener("click", function () {
            const id = this.dataset.materialId;
            if (!id) return;
            fetch(`/student/lms/material/${id}/track-download/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCookie("csrftoken") },
                keepalive: true,
            }).catch(() => {});
        });
    });


    /* ─────────────────────────────────────────────────────────
       8. DESCRIPTION EXPAND / COLLAPSE
       Clicking a truncated .lms-material-desc expands it fully
    ───────────────────────────────────────────────────────── */
    document.querySelectorAll(".lms-material-desc").forEach(desc => {
        // Check if text is actually truncated (overflowing)
        if (desc.scrollWidth > desc.offsetWidth || desc.scrollHeight > desc.offsetHeight) {
            desc.style.cursor = "pointer";
            desc.setAttribute("title", "Click to read more");

            desc.addEventListener("click", function () {
                const expanded = this.dataset.expanded === "true";

                if (expanded) {
                    this.style.whiteSpace = "";
                    this.style.overflow = "";
                    this.style.webkitLineClamp = "";
                    this.style.display = "";
                    this.dataset.expanded = "false";
                    this.setAttribute("title", "Click to read more");
                } else {
                    this.style.whiteSpace = "normal";
                    this.style.overflow = "visible";
                    this.style.webkitLineClamp = "unset";
                    this.style.display = "block";
                    this.dataset.expanded = "true";
                    this.setAttribute("title", "Click to collapse");
                }
            });
        }
    });


    /* ─────────────────────────────────────────────────────────
       9. EMPTY STATE — JS fallback if no .lms-material-card exists
       (Django template already handles this, this is a safety net)
    ───────────────────────────────────────────────────────── */
    const sessionsWrapper = document.querySelector(".lms-sessions-wrapper");

    if (sessionsWrapper) {
        const hasCards = sessionsWrapper.querySelector(".lms-material-card");
        const hasEmpty = sessionsWrapper.querySelector(".lms-empty-state");

        if (!hasCards && !hasEmpty) {
            const emptyDiv = document.createElement("div");
            emptyDiv.className = "lms-empty-state";
            emptyDiv.innerHTML = "<p>No materials found for this filter.</p>";
            sessionsWrapper.appendChild(emptyDiv);
        }
    }


    /* ─────────────────────────────────────────────────────────
       HELPER — Read Django CSRF cookie
    ───────────────────────────────────────────────────────── */
    function getCookie(name) {
        if (!document.cookie) return null;
        for (const cookie of document.cookie.split(";")) {
            const [key, val] = cookie.trim().split("=");
            if (key === name) return decodeURIComponent(val);
        }
        return null;
    }

});


/* ═══════════════════════════════════════════════════════════
   DYNAMIC STYLES — injected to avoid touching lms_dashboard.css
   ═══════════════════════════════════════════════════════════ */
(function () {
    const style = document.createElement("style");
    style.textContent = `
        /* Sticky filter tabs — frosted glass */
        .lms-filters-sticky {
            position: sticky;
            top: 12px;
            z-index: 100;
            background: rgba(255, 255, 255, 0.88);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 10px 16px;
            border-radius: 14px;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.13);
            margin-left: -16px;
            margin-right: -16px;
        }
    `;
    document.head.appendChild(style);
})();