function openTab(evt, tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    evt.target.classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

function enableEdit() {
    document
        .querySelectorAll('#profileForm input, #profileForm textarea, #profileForm select')
        .forEach(el => el.disabled = false);
}
