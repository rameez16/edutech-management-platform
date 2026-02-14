document.addEventListener('DOMContentLoaded', function() {
    // Schedule toggle
    const scheduleToggle = document.getElementById('scheduleToggle');
    const scheduleContent = document.getElementById('scheduleContent');
    const scheduleArrowIcon = document.getElementById('scheduleArrowIcon');

    if (scheduleToggle && scheduleContent && scheduleArrowIcon) {
        scheduleToggle.addEventListener('click', function() {
            if (scheduleContent.style.display === 'none' || scheduleContent.style.display === '') {
                scheduleContent.style.display = 'block';
                scheduleArrowIcon.classList.add('rotate');
            } else {
                scheduleContent.style.display = 'none';
                scheduleArrowIcon.classList.remove('rotate');
            }
        });
    }

    // Trainers toggle
    const trainersToggle = document.getElementById('trainersToggle');
    const trainersContent = document.getElementById('trainersContent');
    const trainersArrowIcon = document.getElementById('trainersArrowIcon');

    if (trainersToggle && trainersContent && trainersArrowIcon) {
        trainersToggle.addEventListener('click', function() {
            if (trainersContent.style.display === 'none' || trainersContent.style.display === '') {
                trainersContent.style.display = 'block';
                trainersArrowIcon.classList.add('rotate');
            } else {
                trainersContent.style.display = 'none';
                trainersArrowIcon.classList.remove('rotate');
            }
        });
    }

    // Statistics toggle
    const statsToggle = document.getElementById('statsToggle');
    const statsContent = document.getElementById('statsContent');
    const statsArrowIcon = document.getElementById('statsArrowIcon');

    if (statsToggle && statsContent && statsArrowIcon) {
        statsToggle.addEventListener('click', function() {
            if (statsContent.style.display === 'none' || statsContent.style.display === '') {
                statsContent.style.display = 'block';
                statsArrowIcon.classList.add('rotate');
            } else {
                statsContent.style.display = 'none';
                statsArrowIcon.classList.remove('rotate');
            }
        });
    }
});