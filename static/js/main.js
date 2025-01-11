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
                
                if (result.files) {
                    const downloadLinks = document.getElementById('downloadLinks');
                    downloadLinks.innerHTML = '<h3 class="text-sm font-medium text-gray-700 mb-2">Download bestanden:</h3>';
                    
                    Object.entries(result.files).forEach(([type, files]) => {
                        files.forEach(file => {
                            const link = document.createElement('a');
                            link.href = `data:application/octet-stream;base64,${file.data}`;
                            link.download = file.name;
                            link.className = 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mr-2 mb-2 inline-block';
                            link.textContent = `Download ${file.name}`;
                            downloadLinks.appendChild(link);
                        });
                    });
                    
                    document.getElementById('result').classList.remove('hidden');
                }
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