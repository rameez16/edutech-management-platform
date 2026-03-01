// ═══════════════════════════════════════════════
//  attend_exam.js  —  Exam Timer + File Upload
// ═══════════════════════════════════════════════

// ── File label update ──
function updateLabel(input) {
    const label = document.getElementById('fileLabel');
    label.textContent = input.files[0] ? input.files[0].name : 'Choose file…';
}

// ── Countdown timer ──
(function () {
    const display    = document.getElementById('timerDisplay');
    const timerBlock = document.getElementById('examTimer');

    if (!display || !timerBlock) return;

    const durationMinutes = parseInt(timerBlock.dataset.duration, 10);
    const examDatetime    = timerBlock.dataset.datetime; // "YYYY-MM-DDTHH:MM:SS" or ""

    let remaining;

    if (examDatetime) {
        const examStart = new Date(examDatetime);
        const examEnd   = new Date(examStart.getTime() + durationMinutes * 60000);
        const now       = new Date();

        if (now < examStart) {
            remaining = durationMinutes * 60;
        } else if (now >= examEnd) {
            remaining = 0;
        } else {
            remaining = Math.floor((examEnd - now) / 1000);
        }
    } else {
        remaining = durationMinutes * 60;
    }

    function fmt(s) {
        return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
    }

    function tick() {
        display.textContent = fmt(remaining);

        if (remaining <= 0) {
            timerBlock.classList.add('timer-expired');
            timerBlock.classList.remove('timer-warning', 'timer-danger');
            return;
        }

        if (remaining <= 60)       timerBlock.classList.add('timer-danger');
        else if (remaining <= 300) timerBlock.classList.add('timer-warning');

        remaining--;
        setTimeout(tick, 1000);
    }

    tick();
})();