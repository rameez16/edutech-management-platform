document.addEventListener("DOMContentLoaded", function () {

    /* ── MODULE CARDS — expand/collapse ─────────────────────────── */
    document.querySelectorAll('.tm-module-header').forEach(header => {
        header.addEventListener('click', () => {
            const moduleCard = header.closest('.tm-module-card');
            const isOpen = moduleCard.classList.contains('open');

            document.querySelectorAll('.tm-module-card')
                .forEach(c => c.classList.remove('open'));

            if (!isOpen) moduleCard.classList.add('open');
        });
    });


    /* ── SESSION CARDS — expand/collapse ─────────────────────────── */
    document.querySelectorAll('.tm-session-header').forEach(header => {
        header.addEventListener('click', (e) => {
            e.stopPropagation();

            const sessionCard = header.closest('.tm-session-card');
            const isOpen = sessionCard.classList.contains('open');

            const moduleBody = sessionCard.closest('.tm-module-body');
            moduleBody.querySelectorAll('.tm-session-card')
                .forEach(c => c.classList.remove('open'));

            if (!isOpen) sessionCard.classList.add('open');
        });
    });


    /* ── STATUS FILTERING (FIXED VERSION) ───────────────────────── */
    document.querySelectorAll('.tm-session-card').forEach(sessionCard => {

        const buttons = sessionCard.querySelectorAll('.filter-btn');
        const tasks = sessionCard.querySelectorAll('.task-card');
        const emptyMessage = sessionCard.querySelector('.filter-empty-message');

        const messages = {
            not_started: "No tasks waiting to be started.",
            in_progress: "You're not working on any tasks currently.",
            submitted: "You haven't submitted any tasks yet.",
            evaluated: "No evaluated tasks available.",
            resubmit: "Great! No tasks require resubmission.",
            all: "No tasks available in this session."
        };

        buttons.forEach(button => {
            button.addEventListener('click', function (e) {

                e.stopPropagation();

                // Remove active
                buttons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                const filter = this.dataset.filter;
                let visibleCount = 0;   // ✅ FIXED

                tasks.forEach(task => {
                    const status = task.dataset.status;

                    if (filter === 'all' || status === filter) {
                        task.style.display = 'flex';
                        visibleCount++;   // ✅ COUNTING
                    } else {
                        task.style.display = 'none';
                    }
                });

                // ✅ Empty message handling
                if (emptyMessage) {
                    if (visibleCount === 0) {
                        emptyMessage.style.display = "block";
                        emptyMessage.textContent = messages[filter];
                    } else {
                        emptyMessage.style.display = "none";
                    }
                }

            });
        });

    });

});