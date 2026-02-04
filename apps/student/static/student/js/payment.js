document.addEventListener('DOMContentLoaded', function () {

    const modeButtons = document.querySelectorAll('.mode-btn');
    const sections = document.querySelectorAll('.payment-section');

    modeButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();

            // remove active from all buttons
            modeButtons.forEach(btn => btn.classList.remove('active'));

            // hide all sections
            sections.forEach(section => section.classList.remove('active'));

            // activate clicked button
            this.classList.add('active');

            // show target section
            const target = this.getAttribute('data-target');
            document.getElementById(target).classList.add('active');
        });
    });

});
