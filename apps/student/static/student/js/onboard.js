document.addEventListener("DOMContentLoaded", () => {
    // ===============================
    // Step 2: Upload signed enrollment letter
    // ===============================
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('signed-letter-input');
    const form = document.getElementById('upload-signed-form');

    if(uploadBtn && fileInput && form){
        // When button clicked, trigger file dialog
        uploadBtn.addEventListener('click', () => fileInput.click());

        // When file selected, submit form automatically
        fileInput.addEventListener('change', () => {
            if(fileInput.files.length > 0){
                form.submit();
            }
        });
    }

    // ===============================
    // Step 3: Download ID Card
    // ===============================
    const downloadIdCardBtn = document.getElementById('download-idcard-btn');

    if(downloadIdCardBtn){
        downloadIdCardBtn.addEventListener('click', () => {
            // Trigger download by redirecting to the URL
            window.location.href = downloadIdCardBtn.dataset.url;
        });
    }
});
