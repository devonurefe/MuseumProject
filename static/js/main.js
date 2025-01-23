document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('result');
    const downloadLocation = document.getElementById('downloadLocation');
    const downloadLinks = document.getElementById('downloadLinks');
    const pdfPageCount = document.getElementById('pdfPageCount');
    const notificationSound = document.getElementById('notificationSound');

    // Form reset fonksiyonu
    function resetForm() {
        form.reset();
        resultDiv.classList.add('hidden');
        downloadLocation.innerHTML = '';
        downloadLinks.innerHTML = '';
        submitButton.disabled = false;
        submitButton.querySelector('span').textContent = 'Verwerken';
        pdfPageCount.textContent = ''; // Sayfa sayısını sıfırla
        const progressBar = submitButton.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = '0%';
        }
    }

    // PDF dosyasının sayfa sayısını göster
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
            pdfPageCount.textContent = ''; // Dosya yüklenmezse sayfa sayısını sıfırla
        }
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Önceki sonuçları sıfırla
        resultDiv.classList.add('hidden');
        downloadLocation.innerHTML = '';
        downloadLinks.innerHTML = '';

        const progressBar = submitButton.querySelector('.progress-bar');
        progressBar.style.width = '0%';
        
        // Animasyon başlangıcı
        submitButton.classList.add('processing');
        submitButton.querySelector('span').textContent = 'Verwerking...';
        
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress = Math.min(progress + 5, 90); // Max 90% until complete
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
            
            // Progress bar'ı 100%
            clearInterval(progressInterval);
            progressBar.style.width = '100%';

            if (result.success) {
                downloadLocation.innerHTML = `
                    <p class="text-green-500">${result.message}</p>
                `;

                // Ses çalma
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
            // Animasyonu kaldır ve butonu resetle
            submitButton.classList.remove('processing');
            submitButton.disabled = false;
            submitButton.querySelector('span').textContent = 'Verwerken';
        }
    });
});