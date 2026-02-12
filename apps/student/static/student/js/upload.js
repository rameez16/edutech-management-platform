document.addEventListener("DOMContentLoaded", function () {

    const rows = document.querySelectorAll(".upload-row");
    const submitBtn = document.querySelector(".submit-btn");
    const cancelBtn = document.querySelector(".cancel-btn");
    const errorBox = document.getElementById("formError");

    /* =============================
       Helpers
    ============================= */

    function isLocked(row) {
        return row.dataset.locked === "true";
    }

    function hasFile(row) {
        const input = row.querySelector("input[type='file']");
        return input && input.files.length > 0;
    }

    function isRequired(row) {
        // Required if NOT locked
        return !isLocked(row);
    }

    function updateButtons() {
        let anySelected = false;
        let allRequiredSelected = true;

        rows.forEach(row => {
            if (hasFile(row)) {
                anySelected = true;
            }

            if (isRequired(row) && !hasFile(row)) {
                allRequiredSelected = false;
            }
        });

        cancelBtn.disabled = !anySelected;
        submitBtn.disabled = !allRequiredSelected;
    }

    function resetRow(row) {
        if (isLocked(row)) return; // 🚫 never touch DB-backed rows

        const input = row.querySelector("input[type='file']");
        const status = row.querySelector(".status");
        const fileBox = row.querySelector(".selected-files");

        if (input) input.value = "";

        if (status) {
            status.textContent = "Not Uploaded";
            status.className = "status not-uploaded";
        }

        if (fileBox) {
            fileBox.textContent = "";
        }
    }

    /* =============================
       File selection
    ============================= */

    rows.forEach(row => {
        const input = row.querySelector("input[type='file']");
        const status = row.querySelector(".status");
        const fileBox = row.querySelector(".selected-files");

        if (!input || isLocked(row)) return;

        input.addEventListener("change", function () {
            if (input.files.length > 0) {
                status.textContent = "Selected";
                status.className = "status selected";
                fileBox.textContent = input.files[0].name;
            } else {
                resetRow(row);
            }

            updateButtons();
        });
    });

    /* =============================
       Cancel button
    ============================= */

    cancelBtn.addEventListener("click", function () {
        rows.forEach(row => resetRow(row));

        submitBtn.disabled = true;
        cancelBtn.disabled = true;

        if (errorBox) {
            errorBox.textContent = "";
            errorBox.style.display = "none";
        }
    });

    /* =============================
       Submit validation
    ============================= */

    submitBtn.addEventListener("click", function (e) {
        let missing = [];

        rows.forEach(row => {
            if (isRequired(row) && !hasFile(row)) {
                missing.push(row.dataset.doc);
            }
        });

        if (missing.length > 0) {
            e.preventDefault();

            errorBox.style.display = "block";
            errorBox.textContent =
                "Please upload required files: " +
                missing.map(m => m.replace("_", " ").toUpperCase()).join(", ");
        }
    });

    /* =============================
       Initial state
    ============================= */

    submitBtn.disabled = true;
    cancelBtn.disabled = true;
});
