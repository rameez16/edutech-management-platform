document.addEventListener("DOMContentLoaded", () => {

// ===============================
// Step 2: Upload signed enrollment letter
// ===============================
const uploadBtn = document.getElementById('uploadSignedBtn');
const fileInput = document.getElementById('signedLetterInput');
const form = document.getElementById('uploadSignedForm');
const uploadStatus = document.getElementById('uploadStatus');

if (uploadBtn && fileInput && form) {
    // Trigger file selector when clicking upload button
    uploadBtn.addEventListener('click', () => fileInput.click());

    // Upload when a file is selected
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length === 0) return;

        const url = form.dataset.url;
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

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
                // ✅ Update upload status
                uploadStatus.textContent = "Uploaded successfully ✔";
                uploadStatus.style.color = "green";

                // ✅ Disable upload button
                uploadBtn.disabled = true;
                uploadBtn.textContent = "Uploaded Successfully ✔";

                // ✅ Disable file input
                fileInput.disabled = true;

                // ✅ Update step badge
                const stepCard = form.closest('.step-card');
                const badge = stepCard.querySelector('.badge');
                if (badge) {
                    badge.textContent = "Completed";
                    badge.classList.remove('warning', 'locked');
                    badge.classList.add('success');
                }

                // ✅ Update step card class
                stepCard.classList.remove('pending', 'locked');
                stepCard.classList.add('completed');

                // ✅ Update step description
                const stepDesc = stepCard.querySelector('.step-desc');
                if (stepDesc) {
                    stepDesc.textContent = "Enrollment letter signed successfully.";
                }

                // ✅ Optional: update checkbox if exists
                const checkbox = stepCard.querySelector('input[type="checkbox"]');
                if (checkbox) checkbox.checked = true;

            } else {
                uploadStatus.textContent = data.message || "Upload failed";
                uploadStatus.style.color = "red";
            }
        })
        .catch(err => {
            console.error(err);
            uploadStatus.textContent = "Something went wrong";
            uploadStatus.style.color = "red";
        });
    });
}



    const modal = document.getElementById("idCardModal");
    const modalBody = document.getElementById("modal-body-full");
    const closeBtn = modal.querySelector(".close");

    // VIEW ID CARD (modal)
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

    // Close modal
    closeBtn.onclick = () => {
        modal.style.display = "none";
        modalBody.innerHTML = "";
    };
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = "none";
            modalBody.innerHTML = "";
        }
    };

    // DOWNLOAD PDF from modal content
    const downloadBtn = document.querySelector(".btn-idcard-download");
    if (downloadBtn) {
        downloadBtn.addEventListener("click", async () => {
            const url = downloadBtn.dataset.idUrl;

            // 1️⃣ Fetch HTML and inject into modal (offscreen)
            const res = await fetch(url);
            const html = await res.text();

            modalBody.innerHTML = html; // inject into modal
            modal.style.display = "block"; // temporarily show to render images

            // Wait a moment to ensure images load
            await new Promise(resolve => setTimeout(resolve, 500));

            // 2️⃣ Generate PDF directly from modal content
            html2pdf().set({
                margin: 0,
                filename: 'ID_Card.pdf',
                image: { type: 'jpeg', quality: 1 },
                html2canvas: { scale: 1.5, useCORS: true },
                jsPDF: { unit: 'px', format: [595, 842], orientation: 'portrait' }

            }).from(modalBody).save()
              .finally(() => {
                  modal.style.display = "none";
                  modalBody.innerHTML = ""; // clean up
              });
        });
    }

});
