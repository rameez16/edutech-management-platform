
document.addEventListener("DOMContentLoaded", () => {

    // ===== ALERTIFY CONFIG =====
    alertify.set('notifier','position', 'top-right');
    alertify.set('notifier','delay', 5); // 5 seconds
    
    /* ======================================================
       COMMON ELEMENTS
    ====================================================== */
    const uploadForm = document.getElementById('uploadSignedForm');
    const csrfToken = uploadForm
        ? uploadForm.querySelector('[name=csrfmiddlewaretoken]').value
        : null;

    /* ======================================================
       STEP 0: SAVE COURSE FEE
    ====================================================== */
    const courseFeeInput = document.getElementById('courseFeeInput');
    const saveCourseFeeBtn = document.getElementById('saveCourseFeeBtn');
    const courseFeeStatus = document.getElementById('courseFeeStatus');

    let courseFeeSaved = false;
    let paymentPlanSaved = false;

    if (courseFeeInput && saveCourseFeeBtn) {
        saveCourseFeeBtn.addEventListener('click', () => {
            const feeValue = courseFeeInput.value.trim();
            const url = courseFeeInput.dataset.url;

            if (!feeValue || isNaN(feeValue) || Number(feeValue) < 0) {
                courseFeeStatus.textContent = "Please enter a valid course fee.";
                courseFeeStatus.style.color = "red";
                return;
            }

            const formData = new FormData();
            formData.append('course_fee_agreed', feeValue);

            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    courseFeeStatus.textContent = "Course fee saved ✔";
                    courseFeeStatus.style.color = "green";
                    courseFeeInput.disabled = true;
                    saveCourseFeeBtn.disabled = true;
                    courseFeeSaved = true;

                    // Enable upload only if payment plan also saved
                    if (paymentPlanSaved && uploadBtn) uploadBtn.disabled = false;
                } else {
                    courseFeeStatus.textContent = data.message || "Failed to save course fee";
                    courseFeeStatus.style.color = "red";
                }
            })
            .catch(err => {
                console.error(err);
                courseFeeStatus.textContent = "Something went wrong";
                courseFeeStatus.style.color = "red";
            });
        });
    }

    /* ======================================================
       STEP 1: SAVE PAYMENT PLAN
    ====================================================== */
    const savePaymentBtn = document.getElementById('savePaymentPlanBtn');
    const paymentSelect = document.getElementById('paymentPlanSelect');
    const paymentStatus = document.getElementById('paymentStatus');
    const uploadBtn = document.getElementById('uploadSignedBtn');

    if (savePaymentBtn && paymentSelect && uploadForm) {
        savePaymentBtn.addEventListener('click', () => {
            const selectedPlan = paymentSelect.value;

            if (!selectedPlan) {
                paymentStatus.textContent = "Please select a payment plan first.";
                paymentStatus.style.color = "red";
                return;
            }

            const url = uploadForm.dataset.url;
            const formData = new FormData();
            formData.append("payment_plan", selectedPlan);

            fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    paymentStatus.textContent = "Payment plan saved ✔";
                    paymentStatus.style.color = "green";
                    paymentSelect.disabled = true;
                    savePaymentBtn.disabled = true;
                    paymentPlanSaved = true;

                    // Enable upload only if course fee also saved
                    if (courseFeeSaved && uploadBtn) uploadBtn.disabled = false;
                } else {
                    paymentStatus.textContent = data.message || "Failed to save payment plan";
                    paymentStatus.style.color = "red";
                }
            })
            .catch(err => {
                console.error(err);
                paymentStatus.textContent = "Something went wrong";
                paymentStatus.style.color = "red";
            });
        });
    }

    /* ======================================================
       STEP 2: UPLOAD SIGNED ENROLLMENT LETTER
    ====================================================== */
    const fileInput = document.getElementById('signedLetterInput');
    const uploadStatus = document.getElementById('uploadStatus');

    if (uploadBtn && fileInput && uploadForm) {

        // Initially disable upload button until both previous steps complete
        if (!courseFeeSaved || !paymentPlanSaved) uploadBtn.disabled = true;

        // Trigger file selector
        uploadBtn.addEventListener('click', () => {
            if (!uploadBtn.disabled) {
                fileInput.click();
            } else {
                let msg = "";
                if (!courseFeeSaved) msg += "Please enter and save course fee first. ";
                if (!paymentPlanSaved) msg += "Please select and save a payment plan first.";
                uploadStatus.textContent = msg.trim();
                uploadStatus.style.color = "red";
            }
        });

        // Upload file when selected
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length === 0) return;

            const url = uploadForm.dataset.url;
            const formData = new FormData();
            formData.append('signed_letter', fileInput.files[0]);

            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alertify.success("Enrollment letter uploaded successfully ✔");

                    // Auto refresh after 1 second
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);

                } else {
                    alertify.error(data.message || "Upload failed ❌");
                }
            })
            .catch(err => {
                console.error(err);
                uploadStatus.textContent = "Something went wrong";
                uploadStatus.style.color = "red";
            });

        });
    }




    /* ======================================================
       ID CARD MODAL VIEW
    ====================================================== */
    const modal = document.getElementById("idCardModal");

    if (modal) {
        const modalBody = document.getElementById("modal-body-full");
        const closeBtn = modal.querySelector(".close");

        document.querySelectorAll(".view-id-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const url = btn.dataset.idUrl;
                fetch(url)
                    .then(res => res.text())
                    .then(html => {
                        modalBody.innerHTML = html;
                        modal.style.display = "block";
                    });
            });
        });

        if (closeBtn) {
            closeBtn.onclick = () => {
                modal.style.display = "none";
                modalBody.innerHTML = "";
            };
        }

        window.onclick = (event) => {
            if (event.target === modal) {
                modal.style.display = "none";
                modalBody.innerHTML = "";
            }
        };

        const downloadBtn = document.querySelector(".btn-idcard-download");
        if (downloadBtn) {
            downloadBtn.addEventListener("click", async () => {
                const url = downloadBtn.dataset.idUrl;
                const res = await fetch(url);
                const html = await res.text();
                modalBody.innerHTML = html;
                modal.style.display = "block";

                await new Promise(resolve => setTimeout(resolve, 500));

                html2pdf().set({
                    margin: 0,
                    filename: 'ID_Card.pdf',
                    image: { type: 'jpeg', quality: 1 },
                    html2canvas: { scale: 1.5, useCORS: true },
                    jsPDF: { unit: 'px', format: [595, 842], orientation: 'portrait' }
                }).from(modalBody).save()
                  .finally(() => {
                      modal.style.display = "none";
                      modalBody.innerHTML = "";
                  });
            });
        }
    }

});
