document.addEventListener("DOMContentLoaded", () => {

    // ===============================
    // Step 2: Upload signed enrollment letter
    // ===============================
    const uploadBtn = document.getElementById('uploadSignedBtn');
    const fileInput = document.getElementById('signedLetterInput');
    const form = document.getElementById('uploadSignedForm');

    if (uploadBtn && fileInput && form) {
        // When button clicked, trigger file dialog
        uploadBtn.addEventListener('click', () => fileInput.click());

        // When file selected, submit form automatically
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                form.submit();
            }
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
