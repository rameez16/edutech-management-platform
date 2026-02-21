// ── COLLAPSIBLE CARDS (.batch-card-header) ──────────────────
document.querySelectorAll('.batch-card-header').forEach(header => {
    header.addEventListener('click', () => {
        const content = header.nextElementSibling;
        const arrow = header.querySelector('.arrow-icon');

        if (content.style.display === 'block') {
            content.style.display = 'none';
            if (arrow) arrow.style.transform = '';
        } else {
            content.style.display = 'block';
            if (arrow) arrow.style.transform = 'rotate(180deg)';
        }
    });
});

// ── TABS ─────────────────────────────────────────────────────
// Scope tabs to their nearest container:
//   - inside .module-body  → scoped to .module-body
//   - inside .batch-card   → scoped to .batch-card  (fallback flat view)
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation();

        const target = btn.dataset.tab;

        // Use module-body as scope if inside one, otherwise fall back to batch-card
        const scope = btn.closest('.module-body') || btn.closest('.batch-card');

        scope.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        scope.querySelectorAll('.tab-content').forEach(tc => {
            tc.classList.toggle('active', tc.dataset.tab === target);
        });
    });
});

// ── MODULE ACCORDION ─────────────────────────────────────────
document.querySelectorAll('.module-row').forEach(row => {
    row.addEventListener('click', () => {
        const moduleItem = row.closest('.module-item');
        const isOpen = moduleItem.classList.contains('open');

        // Accordion: close all, then open clicked one if it was closed
        document.querySelectorAll('.module-item').forEach(m => m.classList.remove('open'));
        if (!isOpen) moduleItem.classList.add('open');
    });
});


