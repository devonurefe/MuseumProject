// main.js güncellemesi
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('result');
    const downloadLocation = document.getElementById('downloadLocation');
    const downloadLinks = document.getElementById('downloadLinks');
    
    // Form reset fonksiyonu
    function resetForm() {
        form.reset();
        resultDiv.classList.add('hidden');
        downloadLocation.innerHTML = '';
        downloadLinks.innerHTML = '';
        submitButton.disabled = false;
        submitButton.querySelector('span').textContent = 'Verwerken';
        const progressBar = submitButton.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = '0%';
        }
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

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
            
            // İşlem tamamlandı, progress bar'ı 100% yap
            clearInterval(progressInterval);
            progressBar.style.width = '100%';

            if (result.success) {
                downloadLocation.innerHTML = `
                    <p class="text-green-500">${result.message}</p>
                `;

                downloadLinks.innerHTML = `
                    <div class="text-center p-4">
                        <a href="data:application/zip;base64,${result.zip_file.data}" 
                           download="${result.zip_file.name}"
                           class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded inline-flex items-center">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                            </svg>
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
            
            // Yeni bir dosya seçildiğinde formu resetle
            const fileInput = form.querySelector('input[type="file"]');
            fileInput.addEventListener('change', resetForm);
        }
    });
});