

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll('input[type="file"]').forEach(input => {

        input.addEventListener('change', function () {

            const row = this.closest('tr');
            const fileBox = row.querySelector('.selected-files');
            const status = row.querySelector('.status');

            if (!this.files || this.files.length === 0) {
                return;
            }

            // show file names
            let names = Array.from(this.files).map(f => f.name);
            fileBox.textContent = names.join(', ');

            // update status
            status.textContent = "Selected";
            status.className = "status uploaded";
        });

    });

});
