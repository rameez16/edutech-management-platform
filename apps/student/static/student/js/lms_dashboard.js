/* ═══════════════════════════════════════════════════════════
   LMS DASHBOARD — lms_dashboard.js
   ═══════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", function () {

    /* ─────────────────────────────────────────────────────────
       1. STAT COUNTER ANIMATION
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
        const delay = index * 80;

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

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                card.style.opacity = "1";
                card.style.transform = "translateY(0)";
            });
        });
    });


    /* ─────────────────────────────────────────────────────────
       3. MATERIAL CARD SCROLL ANIMATION
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
       4. FILTER TABS — instant active feedback
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
    ───────────────────────────────────────────────────────── */
    const filterTabsEl = document.querySelector(".lms-filter-tabs");

    if (filterTabsEl) {
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
       6. VIEW TRACKING
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
       7. DOWNLOAD TRACKING
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
    ───────────────────────────────────────────────────────── */
    document.querySelectorAll(".lms-material-desc").forEach(desc => {
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
       9. EMPTY STATE FALLBACK
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
   STICKY FILTER STYLES
   ═══════════════════════════════════════════════════════════ */
(function () {
    const style = document.createElement("style");
    style.textContent = `
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


/* ═══════════════════════════════════════════════════════════
   10. MINI PLAYER
   ═══════════════════════════════════════════════════════════ */
(function () {

    /* ── Inject HTML ── */
    document.body.insertAdjacentHTML("beforeend", `
        <div id="lms-mini-player" style="display:none;">
            <div id="lms-mini-backdrop"></div>
            <div id="lms-mini-modal">
                <div id="lms-mini-header">
                    <span id="lms-mini-title"></span>
                    <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
                        <a id="lms-mini-yt-link" href="#" target="_blank" rel="noopener"
                           style="display:none;font-size:11px;color:#a78bfa;text-decoration:none;
                                  background:rgba(167,139,250,0.15);padding:4px 10px;
                                  border-radius:20px;white-space:nowrap;font-family:Segoe UI,sans-serif;">
                            ↗ Open on YouTube
                        </a>
                        <button id="lms-mini-close" title="Close">✕</button>
                    </div>
                </div>
                <div id="lms-mini-frame-wrap">
                    <iframe id="lms-mini-iframe"
                        frameborder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen>
                    </iframe>
                </div>
            </div>
        </div>
    `);

    /* ── Inject styles ── */
    const style = document.createElement("style");
    style.textContent = `
        #lms-mini-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            z-index: 999;
            animation: lmsBackdropIn 0.2s ease;
        }
        #lms-mini-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            z-index: 1000;
            width: min(860px, 92vw);
            background: #0f0f1a;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 24px 80px rgba(0,0,0,0.6);
            animation: lmsModalIn 0.25s ease forwards;
        }
        #lms-mini-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: #1a1a2e;
            border-bottom: 1px solid rgba(255,255,255,0.07);
        }
        #lms-mini-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: #e0e0ff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: calc(100% - 140px);
            font-family: 'Segoe UI', sans-serif;
        }
        #lms-mini-close {
            background: rgba(255,255,255,0.1);
            border: none;
            color: #fff;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            transition: background 0.15s;
        }
        #lms-mini-close:hover { background: rgba(255,255,255,0.25); }
        #lms-mini-frame-wrap {
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
        }
        #lms-mini-iframe {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
        }
        @keyframes lmsBackdropIn {
            from { opacity: 0; }
            to   { opacity: 1; }
        }
        @keyframes lmsModalIn {
            from { opacity: 0; transform: translate(-50%, -50%) scale(0.93); }
            to   { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
    `;
    document.head.appendChild(style);

    /* ── Element refs ── */
    const player   = document.getElementById("lms-mini-player");
    const backdrop = document.getElementById("lms-mini-backdrop");
    const iframe   = document.getElementById("lms-mini-iframe");
    const titleEl  = document.getElementById("lms-mini-title");
    const closeBtn = document.getElementById("lms-mini-close");
    const ytLink   = document.getElementById("lms-mini-yt-link");

        /* ── Helper: YouTube/Vimeo → embed URL ── */
function toEmbedUrl(url) {
    if (!url) return null;

    // YouTube match
    const yt = url.match(
        /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{11})/
    );

    if (yt) {
        return `https://www.youtube.com/embed/${yt[1]}?` +
               `autoplay=1` +
               `&rel=0` +
               `&modestbranding=1` +
               `&playsinline=1` +
               `&enablejsapi=1` +
               `&origin=${window.location.origin}`;
    }

    // Vimeo match
    const vi = url.match(/vimeo\.com\/(\d+)/);
    if (vi) {
        return `https://player.vimeo.com/video/${vi[1]}?autoplay=1`;
    }

    return null;
}
    /* ── Open ── */
    function openPlayer(embedUrl, title, fallbackUrl) {
        iframe.src = embedUrl;
        titleEl.textContent = title || "Video";

        // Show "Open on YouTube" link as fallback for embed-blocked videos
        if (fallbackUrl) {
            ytLink.href = fallbackUrl;
            ytLink.style.display = "";
        } else {
            ytLink.style.display = "none";
        }

        player.style.display = "block";
        document.body.style.overflow = "hidden";
    }

    /* ── Close ── */
    function closePlayer() {
        player.style.display = "none";
        iframe.src = "";
        document.body.style.overflow = "";
    }

    closeBtn.addEventListener("click", closePlayer);
    backdrop.addEventListener("click", closePlayer);
    document.addEventListener("keydown", e => {
        if (e.key === "Escape") closePlayer();
    });

    /* ── Attach click to thumbnails ── */
    document.querySelectorAll(".lms-material-thumb").forEach(thumb => {
        thumb.style.cursor = "pointer";

        thumb.addEventListener("click", function () {
            const card       = this.closest(".lms-material-card");
            const watchBtn   = card.querySelector(".lms-btn-primary");
            const title      = card.querySelector(".lms-material-title")?.textContent?.trim();

            if (!watchBtn) return;

            const externalUrl = watchBtn.dataset.externalUrl;

            if (!externalUrl) {
                // No external URL — follow the watch button normally
                watchBtn.click();
                return;
            }

            const embedUrl = toEmbedUrl(externalUrl);

            if (embedUrl) {
                openPlayer(embedUrl, title, externalUrl);
            } else {
                // Not a YouTube/Vimeo link — open directly
                window.open(externalUrl, "_blank", "noopener");
            }
        });
    });

})();