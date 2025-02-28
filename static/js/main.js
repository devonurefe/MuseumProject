document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('result');
    const downloadLocation = document.getElementById('downloadLocation');
    const downloadLinks = document.getElementById('downloadLinks');
    const pdfPageCount = document.getElementById('pdfPageCount');
    const notificationSound = document.getElementById('notificationSound');

    // Form reset function
    function resetForm() {
        form.reset();
        resultDiv.classList.add('hidden');
        downloadLocation.innerHTML = '';
        downloadLinks.innerHTML = '';
        submitButton.disabled = false;
        submitButton.querySelector('span').textContent = 'Verwerken';
        pdfPageCount.textContent = ''; // Reset page count
        const progressBar = submitButton.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = '0%';
        }
    }

    // Show the number of pages in the PDF
    const fileInput = form.querySelector('input[type="file"]');
    fileInput.addEventListener('change', function() {
        const file = fileInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const pdfData = new Uint8Array(e.target.result);
                const loadingTask = pdfjsLib.getDocument(pdfData);
                loadingTask.promise.then(function(pdf) {
                    pdfPageCount.textContent = `Aantal pagina's: ${pdf.numPages}`;
                }).catch(function(error) {
                    pdfPageCount.textContent = 'Fout bij het lezen van PDF';
                });
            };
            reader.readAsArrayBuffer(file);
        } else {
            pdfPageCount.textContent = ''; // Reset if no file is selected
        }
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Reset previous results
        resultDiv.classList.add('hidden');
        downloadLocation.innerHTML = '';
        downloadLinks.innerHTML = '';

        const progressBar = submitButton.querySelector('.progress-bar');
        progressBar.style.width = '0%';

        // Start animation
        submitButton.classList.add('processing');
        submitButton.querySelector('span').textContent = 'Verwerking...';

        let progress = 0;
        const progressInterval = setInterval(() => {
            progress = Math.min(progress + 5, 90); // Max 90% until completion
            progressBar.style.width = `${progress}%`;
        }, 200);

        try {
            submitButton.disabled = true;
            const formData = new FormData(form);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            // Progress bar to 100%
            clearInterval(progressInterval);
            progressBar.style.width = '100%';

            if (result.success) {
                downloadLocation.innerHTML = `
                    <p class="text-green-500">${result.message}</p>
                `;

                // Play notification sound
                notificationSound.play();

                downloadLinks.innerHTML = `
                    <div class="text-center p-4">
                        <a href="data:application/zip;base64,${result.zip_file.data}"
                           download="${result.zip_file.name}"
                           class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded inline-flex items-center">
                            Download Output (${result.zip_file.name})
                        </a>
                    </div>
                `;

                resultDiv.classList.remove('hidden');
            } else {
                throw new Error(result.error || 'Er is een fout opgetreden');
            }
        } catch (error) {
            downloadLocation.innerHTML = `
                <p class="text-red-500">Fout: ${error.message}</p>
            `;
            resultDiv.classList.remove('hidden');
        } finally {
            // Stop animation and reset button
            submitButton.classList.remove('processing');
            submitButton.disabled = false;
            submitButton.querySelector('span').textContent = 'Verwerken';
        }
    });

    // Register the service worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/static/js/service-worker.js')
                .then(function(registration) {
                    console.log('Service Worker registered with scope:', registration.scope);
                })
                .catch(function(error) {
                    console.log('Service Worker registration failed:', error);
                });
        });
    }
});
