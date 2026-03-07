

// ── Notification Panel ──────────────────────────────────────────

let notifLoaded = false;

function getTypeIcon(type) {
    const map = {
        payment_reminder: { icon: '💳', cls: 'nti-payment' },
        payment_received: { icon: '✅', cls: 'nti-payment' },
        lead_assigned:    { icon: '👤', cls: 'nti-lead'    },
        issue_assigned:   { icon: '🚨', cls: 'nti-issue'   },
        followup_due:     { icon: '📅', cls: 'nti-followup' },
        document_pending: { icon: '📄', cls: 'nti-document' },
        general:          { icon: '🔔', cls: 'nti-general'  },
    };
    return map[type] || map['general'];
}

function renderNotifications(notifications) {
    const body = document.getElementById('notif-panel-body');
    if (!notifications.length) {
        body.innerHTML = `
            <div class="notif-empty">
                <span class="notif-empty-icon">🎉</span>
                You're all caught up!
            </div>`;
        return;
    }
    body.innerHTML = notifications.map(n => {
        const ti = getTypeIcon(n.type);
        return `
        <div class="notif-item" id="notif-item-${n.id}" onclick="handleNotifClick(event, '${n.link_url}', ${n.id})">
            <div class="notif-type-icon ${ti.cls}">${ti.icon}</div>
            <div class="notif-text">
                <div class="notif-title">${n.title}</div>
                <div class="notif-msg">${n.message}</div>
                <div class="notif-time">${n.created_at}</div>
            </div>
            <button class="notif-dismiss" onclick="dismissNotif(event, ${n.id})" title="Mark as read">✕</button>
        </div>`;
    }).join('');
}

function updateBadge(count) {
    const badge = document.getElementById('notif-count-badge');
    if (!badge) return;
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

async function loadNotifications() {
    const url = document.getElementById('notif-fetch-url').value;
    try {
        const res = await fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await res.json();
        renderNotifications(data.notifications);
        updateBadge(data.count);
        notifLoaded = true;
    } catch (e) {
        document.getElementById('notif-panel-body').innerHTML =
            '<div class="notif-empty">Could not load notifications.</div>';
    }
}

function toggleNotifPanel(e) {
    e.stopPropagation();
    const panel = document.getElementById('notif-panel');
    const isOpen = panel.classList.contains('open');
    panel.classList.toggle('open', !isOpen);
    if (!isOpen && !notifLoaded) loadNotifications();
}

function getCsrfToken() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}

function getMarkReadUrl(id) {
    const base = document.getElementById('notif-mark-read-base').value;
    // base should be like /student/notifications/mark-read/0/
    return base.replace('/0/', `/${id}/`);
}

async function dismissNotif(e, id) {
    e.stopPropagation();
    try {
        await fetch(getMarkReadUrl(id), {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
    } catch (_) {}

    const item = document.getElementById(`notif-item-${id}`);
    if (item) {
        item.style.transition = 'opacity 0.2s, max-height 0.3s, padding 0.3s';
        item.style.opacity = '0';
        item.style.maxHeight = '0';
        item.style.overflow = 'hidden';
        item.style.padding = '0';
        setTimeout(() => {
            item.remove();
            const remaining = document.querySelectorAll('.notif-item').length;
            updateBadge(remaining);
            if (!remaining) renderNotifications([]);
        }, 320);
    }
}

function handleNotifClick(e, url, id) {
    if (e.target.classList.contains('notif-dismiss')) return;
    dismissNotif(e, id);
    if (url && url !== 'None' && url !== '') {
        setTimeout(() => window.location.href = url, 370);
    }
}

async function markAllRead() {
    const items = document.querySelectorAll('.notif-item');
    const csrf = getCsrfToken();
    const promises = Array.from(items).map(item => {
        const id = item.id.replace('notif-item-', '');
        return fetch(getMarkReadUrl(id), {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf,
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(() => {});
    });
    await Promise.all(promises);
    renderNotifications([]);
    updateBadge(0);
}





// ── Profile Dropdown ─────────────────────────────

function toggleProfileMenu(e) {
    e.stopPropagation();
    const menu = document.getElementById('profile-dropdown');
    menu.classList.toggle('open');
}

// ── Global Click Handler (close panels) ─────────────────

document.addEventListener('click', function (e) {

    const notifWrapper = document.getElementById('notif-wrapper');
    const notifPanel = document.getElementById('notif-panel');

    if (notifWrapper && !notifWrapper.contains(e.target)) {
        if (notifPanel) notifPanel.classList.remove('open');
    }

    const profileWrapper = document.getElementById('profile-wrapper');
    const profileDropdown = document.getElementById('profile-dropdown');

    if (profileWrapper && !profileWrapper.contains(e.target)) {
        if (profileDropdown) profileDropdown.classList.remove('open');
    }

});