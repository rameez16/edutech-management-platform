document.addEventListener("DOMContentLoaded", () => {

    const rows = document.querySelectorAll(".upload-row");
    const submitBtn = document.querySelector(".submit-btn");
    const cancelBtn = document.querySelector(".cancel-btn");
    const errorBox = document.getElementById("formError");

    const REQUIRED = ["photo", "education", "aadhaar", "resume"];

    function updateSubmitState() {
        let allSelected = true;

        rows.forEach(row => {
            const input = row.querySelector("input[type=file]");
            if (!input.files.length) {
                allSelected = false;
            }
        });

        submitBtn.disabled = !allSelected;
    }

    rows.forEach(row => {
        const input = row.querySelector("input[type=file]");
        const status = row.querySelector(".status");
        const fileBox = row.querySelector(".selected-files");

        input.addEventListener("change", () => {
            if (input.files.length) {
                status.textContent = "Selected";
                status.className = "status selected";
                fileBox.textContent = input.files[0].name;
            }
            updateSubmitState();
        });
    });

    submitBtn.addEventListener("click", (e) => {
        let missing = [];

        rows.forEach(row => {
            const key = row.dataset.doc;
            const input = row.querySelector("input[type=file]");
            if (REQUIRED.includes(key) && !input.files.length) {
                missing.push(key);
            }
        });

        if (missing.length) {
            e.preventDefault();
            errorBox.textContent =
                "Please upload: " + missing.map(k => k.toUpperCase()).join(", ");
        }
    });

    cancelBtn.addEventListener("click", () => {
        rows.forEach(row => {
            row.querySelector("input").value = "";
            row.querySelector(".status").textContent = "Not Uploaded";
            row.querySelector(".status").className = "status not-uploaded";
            row.querySelector(".selected-files").textContent = "";
        });
        submitBtn.disabled = true;
        errorBox.textContent = "";
    });

});
