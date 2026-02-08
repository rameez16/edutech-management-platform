document.addEventListener("DOMContentLoaded", () => {

    /* ================================
       STEP 1 – DOCUMENT UPLOAD LOGIC
    ================================ */

    const rows = document.querySelectorAll(".upload-row");
    const submitBtn = document.querySelector(".submit-btn");
    const cancelBtn = document.querySelector(".cancel-btn");
    const errorBox = document.getElementById("formError");

    function updateSubmitState() {
        let allSelected = true;

        rows.forEach(row => {
            const input = row.querySelector("input[type=file]");
            if (input && !input.files.length) {
                allSelected = false;
            }
        });

        if (submitBtn) {
            submitBtn.disabled = !allSelected;
        }
    }

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

    if (submitBtn) {
        submitBtn.addEventListener("click", (e) => {
            let missing = [];

            rows.forEach(row => {
                const key = row.dataset.doc;
                const input = row.querySelector("input[type=file]");
                if (input && !input.files.length) {
                    missing.push(key.toUpperCase());
                }
            });

            if (missing.length) {
                e.preventDefault();
                errorBox.textContent = "Please upload: " + missing.join(", ");
            }
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            rows.forEach(row => {
                const input = row.querySelector("input[type=file]");
                if (!input) return;

                input.value = "";
                row.querySelector(".status").textContent = "Not Uploaded";
                row.querySelector(".status").className = "status not-uploaded";
                row.querySelector(".selected-files").textContent = "";
            });

            if (submitBtn) submitBtn.disabled = true;
            if (errorBox) errorBox.textContent = "";
        });
    }

    /* ================================
       STEP 2 – ENROLLMENT LETTER UPLOAD
       (AJAX – NO PAGE RELOAD)
    ================================ */

    const uploadBtn = document.getElementById("upload-btn");
    const fileInput = document.getElementById("signed-letter-input");
    const form = document.getElementById("upload-signed-form");

    if (!uploadBtn || !fileInput || !form) return;

    // Create status text dynamically
    const statusText = document.createElement("small");
    statusText.style.display = "block";
    statusText.style.marginTop = "6px";
    statusText.style.fontSize = "12px";
    form.appendChild(statusText);

    uploadBtn.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {
        if (!fileInput.files.length) return;

        const formData = new FormData(form);
        const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;

        uploadBtn.textContent = "Uploading...";
        uploadBtn.disabled = true;
        statusText.textContent = "Uploading...";
        statusText.style.color = "#666";

        fetch(form.action, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                statusText.textContent = data.message || "✔ Upload successful";
                statusText.style.color = "green";
                uploadBtn.textContent = "Uploaded ✔";
            } else {
                statusText.textContent = data.message || "Upload failed";
                statusText.style.color = "red";
                uploadBtn.disabled = false;
                uploadBtn.textContent = "Upload Signed Enrollment Letter";
            }
        })
        .catch(() => {
            statusText.textContent = "Upload failed. Try again.";
            statusText.style.color = "red";
            uploadBtn.disabled = false;
            uploadBtn.textContent = "Upload Signed Enrollment Letter";
        });
    });

});



