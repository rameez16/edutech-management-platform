// ═══════════════════════════════════════════════
//  attend_exam.js  —  Exam Timer + File Upload
// ═══════════════════════════════════════════════

// ── File label update ──
function updateLabel(input) {
    const label = document.getElementById('fileLabel');
    label.textContent = input.files[0] ? input.files[0].name : 'Choose file…';
}

// ── Auto-refresh when exam is not yet published ──
(function () {
    const pendingCard = document.querySelector('.exam-pending-card');
    if (!pendingCard) return;
    setTimeout(function () { location.reload(); }, 30000);
})();

// ── Countdown timer ──
(function () {
    const display    = document.getElementById('timerDisplay');
    const timerBlock = document.getElementById('examTimer');

    if (!display || !timerBlock) return;

    const durationMinutes = parseInt(timerBlock.dataset.duration, 10);
    const endTimeAttr     = timerBlock.dataset.endtime;

    const LATE_WINDOW_MS = 60 * 60 * 1000;   // 1 hour grace period

    // Always use the real fixed end time from server — never recalculate
    const endTime     = endTimeAttr ? new Date(endTimeAttr).getTime() : Date.now() + durationMinutes * 60000;
    const lateEndTime = endTime + LATE_WINDOW_MS;

    // ── UI helpers ──
    function getUploadForm() { return document.querySelector('.upload-form'); }
    function getSubmitBtn()  { return document.querySelector('.upload-form button[type="submit"]'); }
    function getFileInput()  { return document.getElementById('answerFile'); }
    function getFileLabel()  { return document.querySelector('.file-upload-label'); }
    function getLateNotice() { return document.getElementById('lateNotice'); }

    function showLateNotice() {
        if (getLateNotice()) return;
        const uploadForm = getUploadForm();
        if (!uploadForm) return;
        const notice     = document.createElement('div');
        notice.id        = 'lateNotice';
        notice.className = 'late-submission-notice';
        notice.innerHTML = '⚠️ Time is up! You can still submit — it will be marked as <strong>Late Submission</strong>.';
        uploadForm.parentNode.insertBefore(notice, uploadForm);
    }

    function lockSubmission() {
        const notice = getLateNotice();
        if (notice) notice.remove();

        const uploadForm = getUploadForm();
        if (!uploadForm) return;

        const locked     = document.createElement('div');
        locked.className = 'late-submission-notice submission-locked';
        locked.innerHTML = '🔒 Submission closed. The exam window has ended.';
        uploadForm.parentNode.insertBefore(locked, uploadForm);

        const btn   = getSubmitBtn();
        const input = getFileInput();
        const label = getFileLabel();
        if (btn)   { btn.disabled = true; btn.textContent = '🔒 Submission Closed'; }
        if (input) { input.disabled = true; }
        if (label) { label.style.opacity = '0.4'; label.style.pointerEvents = 'none'; }
        uploadForm.style.pointerEvents = 'none';
    }

    function fmt(s) {
        const m   = String(Math.floor(s / 60)).padStart(2, '0');
        const sec = String(s % 60).padStart(2, '0');
        return m + ':' + sec;
    }

    function tick() {
        const now           = Date.now();
        const remaining     = Math.max(0, Math.floor((endTime - now) / 1000));
        const lateRemaining = Math.max(0, Math.floor((lateEndTime - now) / 1000));

        if (now < endTime) {
            // ── Normal exam window ──
            display.textContent = fmt(remaining);
            timerBlock.classList.remove('timer-warning', 'timer-danger', 'timer-expired', 'timer-late');
            if (remaining <= 60)       timerBlock.classList.add('timer-danger');
            else if (remaining <= 300) timerBlock.classList.add('timer-warning');
            setTimeout(tick, 1000);

        } else if (now < lateEndTime) {
            // ── Late window ──
            timerBlock.classList.remove('timer-warning', 'timer-danger');
            timerBlock.classList.add('timer-expired', 'timer-late');
            display.textContent = '00:00';
            showLateNotice();
            setTimeout(tick, 1000);

        } else {
            // ── Grace period over: lock ──
            timerBlock.classList.remove('timer-late');
            timerBlock.classList.add('timer-expired');
            display.textContent = '00:00';
            lockSubmission();
        }
    }

    tick();
})();