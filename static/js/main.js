document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const statusDiv = document.getElementById('status');
    const processingAnimation = document.querySelector('.processing-animation');
    const steps = document.querySelectorAll('.step');
    const submitButton = form.querySelector('button[type="submit"]');
    let currentStep = 0;

    function updateProgress() {
        steps.forEach((step, index) => {
            if (index === currentStep) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
        currentStep = (currentStep + 1) % steps.length;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Her yeni işlemde önceki sonuçları ve mesajları temizle
        statusDiv.textContent = '';
        statusDiv.className = '';
        document.getElementById('result').classList.add('hidden');
        document.getElementById('downloadLocation').innerHTML = '';
        document.getElementById('downloadLinks').innerHTML = '';
        
        // Animasyonu göster
        processingAnimation.classList.remove('hidden');
        currentStep = 0; // Animasyonu baştan başlat
        updateProgress(); // İlk adımı hemen göster
        
        // İlerleme animasyonunu başlat
        const progressInterval = setInterval(updateProgress, 2000);
        
        const formData = new FormData(this);
        
        try {
            submitButton.disabled = true;
            submitButton.textContent = 'Verwerking...';
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                statusDiv.textContent = 'Bestand succesvol verwerkt!';
                statusDiv.className = 'mt-4 text-green-500';
                
                const downloadLinks = document.getElementById('downloadLinks');
                downloadLinks.innerHTML = `
                    <div class="text-center p-4">
                        <a href="data:application/zip;base64,${result.zip_file.data}" 
                           download="${result.zip_file.name}"
                           class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded inline-flex items-center">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                            </svg>
                            Download Output Folder (${result.zip_file.name})
                        </a>
                    </div>
                `;
                
                document.getElementById('result').classList.remove('hidden');
            } else {
                throw new Error(result.error || 'Er is een fout opgetreden');
            }
        } catch (error) {
            statusDiv.textContent = `Fout: ${error.message}`;
            statusDiv.className = 'mt-4 text-red-500';
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Verwerken';
            clearInterval(progressInterval);
            processingAnimation.classList.add('hidden');
        }
    });
}); 