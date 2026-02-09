document.addEventListener("DOMContentLoaded", () => {
    const rows = document.querySelectorAll(".upload-row");
    const submitBtn = document.querySelector(".submit-btn");
    const cancelBtn = document.querySelector(".cancel-btn");
    const errorBox = document.getElementById("formError");

    // Update Submit button state
    function updateSubmitState() {
        let allSelected = true;
        rows.forEach(row => {
            const input = row.querySelector("input[type=file]");
            const status = row.querySelector(".status");
            if (status.textContent === "Pending Verification" || status.textContent === "Verified") return;
            if (!input || !input.files.length) allSelected = false;
        });
        submitBtn.disabled = !allSelected;
        updateCancelState();
    }

    // Update Cancel button state
    function updateCancelState() {
        const anySelected = [...document.querySelectorAll("input[type=file]")]
            .some(input => input.files.length > 0);
        if (cancelBtn) cancelBtn.disabled = !anySelected;
    }

    // Handle file selection
    rows.forEach(row => {
        const input = row.querySelector("input[type=file]");
        const status = row.querySelector(".status");
        const fileBox = row.querySelector(".selected-files");

        if (!input) return;

        input.addEventListener("change", () => {
            if (input.files.length) {
                status.textContent = "Selected";
                status.className = "status selected";
                fileBox.textContent = input.files[0].name;
            } else {
                status.textContent = "Not Uploaded";
                status.className = "status not-uploaded";
                fileBox.textContent = "";
            }
            updateSubmitState();
        });
    });

    // Cancel button clears all selected files
    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            rows.forEach(row => {
                const input = row.querySelector("input[type=file]");
                const status = row.querySelector(".status");
                const fileBox = row.querySelector(".selected-files");
                if (input) input.value = "";
                if (status) {
                    const docKey = row.dataset.doc;
                    if (docs[docKey]) {
                        const ver = docs[docKey].verification_status;
                        if (ver === "pending") status.textContent = "Pending Verification";
                        else if (ver === "verified") status.textContent = "Verified";
                        else if (ver === "rejected") status.textContent = "Rejected";
                        else status.textContent = "Not Uploaded";
                    } else {
                        status.textContent = "Not Uploaded";
                    }
                    status.className = "status " + status.textContent.toLowerCase().replace(/\s/g, "-");
                }
                if (fileBox) fileBox.textContent = "";
            });
            if (submitBtn) submitBtn.disabled = true;
            if (errorBox) errorBox.textContent = "";
            updateCancelState();
        });
    }

    // Prevent submitting if any required file missing
    if (submitBtn) {
        submitBtn.addEventListener("click", (e) => {
            let missing = [];
            rows.forEach(row => {
                const key = row.dataset.doc;
                const input = row.querySelector("input[type=file]");
                const status = row.querySelector(".status");
                if (!input || !input.files.length) {
                    if (status.textContent !== "Pending Verification" && status.textContent !== "Verified")
                        missing.push(key.toUpperCase());
                }
            });
            if (missing.length) {
                e.preventDefault();
                errorBox.textContent = "Please upload: " + missing.join(", ");
            }
        });
    }

    // Initialize states on page load
    updateSubmitState();
});
