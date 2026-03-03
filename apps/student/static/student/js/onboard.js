
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
       STEP 2: UPLOAD SIGNED ENROLLMENT LETTER
    ====================================================== */
    const uploadBtn = document.getElementById('uploadSignedBtn');
    const fileInput = document.getElementById('signedLetterInput');
    const uploadStatus = document.getElementById('uploadStatus');

    if (uploadBtn && fileInput && uploadForm) {

        // Trigger file selector
        uploadBtn.addEventListener('click', () => {
            fileInput.click();
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

                    uploadBtn.disabled = true;
                    uploadBtn.textContent = "Uploaded Successfully ✔";
                    fileInput.disabled = true;

                    const stepCard = uploadForm.closest('.step-card');
                    if (stepCard) {
                        const badge = stepCard.querySelector('.badge');
                        if (badge) {
                            badge.textContent = "Completed";
                            badge.classList.remove('warning', 'locked');
                            badge.classList.add('success');
                        }

                        stepCard.classList.remove('pending', 'locked');
                        stepCard.classList.add('completed');

                        const stepDesc = stepCard.querySelector('.step-desc');
                        if (stepDesc) {
                            stepDesc.textContent = "Enrollment letter signed successfully.";
                        }

                        const checkbox = stepCard.querySelector('input[type="checkbox"]');
                        if (checkbox) checkbox.checked = true;
                    }

                    setTimeout(() => {
                        location.reload();
                    }, 1500);

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
