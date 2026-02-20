// Collapsible Cards - using inline style to avoid CSS specificity issues
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

// Tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation();

        const target = btn.dataset.tab;
        const parentCard = btn.closest('.batch-card');

        parentCard.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        parentCard.querySelectorAll('.tab-content').forEach(tc => {
            tc.classList.toggle('active', tc.dataset.tab === target);
        });
    });
});