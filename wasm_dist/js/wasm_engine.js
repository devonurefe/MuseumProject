const { PDFDocument } = PDFLib;

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    const pdfPageCount = document.getElementById('pdfPageCount');
    const logArea = document.getElementById('logArea');
    const resultDiv = document.getElementById('result');
    const downloadLinks = document.getElementById('downloadLinks');
    const btnText = document.getElementById('btn-text');
    const progressBar = document.getElementById('progress-bar');
    const submitBtn = form.querySelector('button[type="submit"]');

    let globalPdfBytes = null;
    let totalPdfPages = 0;

    function logProgress(msg) {
        logArea.classList.remove('hidden');
        logArea.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${msg}</div>`;
        logArea.scrollTop = logArea.scrollHeight;
        console.log(msg);
    }

    // PDF Load Listener
    document.getElementById('pdf_file').addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) {
            pdfPageCount.textContent = "";
            return;
        }

        pdfPageCount.textContent = "Reading PDF file...";
        const arrayBuffer = await file.arrayBuffer();
        globalPdfBytes = new Uint8Array(arrayBuffer);

        try {
            const pdfDoc = await PDFDocument.load(globalPdfBytes);
            totalPdfPages = pdfDoc.getPageCount();
            pdfPageCount.textContent = `Total Pages: ${totalPdfPages}`;
            logProgress(`PDF loaded. Total ${totalPdfPages} pages.`);
        } catch (err) {
            pdfPageCount.textContent = "ERROR: Cannot read PDF.";
            console.error(err);
        }
    });

    // Parsers (Ported from python process_ranges & process_remove_pages)
    function parseRanges(rangesStr, maxPages) {
        if (!rangesStr) return [[...Array(maxPages).keys()].map(i => i + 1)];
        const ranges = [];
        rangesStr.split(',').forEach(part => {
            if (part.includes('-')) {
                const [start, end] = part.split('-').map(Number);
                if (start > end || start < 1 || end > maxPages) throw new Error(`Invalid page range: ${part}`);
                const r = [];
                for (let i = start; i <= end; i++) r.push(i);
                ranges.push(r);
            } else {
                const page = Number(part);
                if (page < 1 || page > maxPages) throw new Error(`Invalid page range: ${part}`);
                ranges.push([page]);
            }
        });
        return ranges;
    }

    function parseRemovePages(removeStr, maxPages) {
        if (!removeStr) return [];
        const pages = removeStr.split(',').map(s => Number(s.trim())).filter(n => n);
        if (pages.some(p => p < 1 || p > maxPages)) throw new Error("Invalid pages to remove");
        return pages;
    }

    function mergeArticles(ranges, mergeStr) {
        if (!mergeStr) return ranges;
        const mergeIndices = mergeStr.split(',').map(s => Number(s.trim())).filter(n => n);
        if (mergeIndices.length < 2) return ranges;

        const validIndices = mergeIndices.filter(i => i >= 1 && i <= ranges.length).sort((a, b) => a - b);
        if (validIndices.length < 2) return ranges;

        let allPages = [];
        const indicesSet = new Set(validIndices.map(i => i - 1));
        validIndices.forEach(i => allPages.push(...ranges[i - 1]));
        allPages.sort((a, b) => a - b);

        const result = [];
        for (let i = 0; i < ranges.length; i++) {
            if (i === validIndices[0] - 1) result.push(allPages);
            else if (!indicesSet.has(i)) result.push(ranges[i]);
        }
        return result;
    }

    // Helper Format Name
    function generateFilename(year, number, start, end) {
        const pYear = String(year);
        const pNum = String(number).padStart(2, '0');
        const pStart = String(start).padStart(2, '0');
        const pEnd = String(end).padStart(2, '0');
        return `${pYear}${pNum}${pStart}${pEnd}`;
    }

    // Extract Text natively without Tesseract (Matches Python PyPDF2 logic)
    async function extractTextFromPdf(pdfBytes) {
        const loadingTask = pdfjsLib.getDocument({ data: pdfBytes });
        const pdf = await loadingTask.promise;
        let fullText = "";
        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const pageText = textContent.items.map(item => item.str).join(' ');
            fullText += pageText + "\n\n";
        }
        return fullText;
    }

    // PDF.js Render Page as Image (Matches Python PIL dimensions)
    async function renderScaledImages(pdfBytes, pageNumber) {
        const loadingTask = pdfjsLib.getDocument({ data: pdfBytes });
        const pdf = await loadingTask.promise;
        const page = await pdf.getPage(pageNumber);

        // Render at a high scale initially (scale 3.0) for good base quality
        const viewport = page.getViewport({ scale: 3.0 });

        const sourceCanvas = document.createElement('canvas');
        sourceCanvas.height = viewport.height;
        sourceCanvas.width = viewport.width;

        await page.render({ canvasContext: sourceCanvas.getContext('2d'), viewport: viewport }).promise;

        function resizeCanvas(maxW, maxH) {
            let ratio = Math.min(maxW / viewport.width, maxH / viewport.height);
            let targetW = viewport.width * ratio;
            let targetH = viewport.height * ratio;

            const targetCanvas = document.createElement('canvas');
            targetCanvas.width = targetW;
            targetCanvas.height = targetH;
            const ctx = targetCanvas.getContext('2d');
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
            ctx.drawImage(sourceCanvas, 0, 0, targetW, targetH);
            return targetCanvas.toDataURL('image/jpeg', 0.85).split(',')[1];
        }

        // Python used 500x700 for small, 1024x1280 for large
        const smallBase64 = resizeCanvas(500, 700);
        const largeBase64 = resizeCanvas(1024, 1280);

        return { small: smallBase64, large: largeBase64 };
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!globalPdfBytes) return alert("Please select a PDF file first");

        btnText.textContent = "Processing... (Do not close tab)";
        submitBtn.disabled = true;
        resultDiv.classList.add('hidden');
        logArea.innerHTML = '';
        progressBar.style.width = '10%';

        logProgress("System initialized...");

        try {
            const year = document.getElementById('year').value;
            const number = document.getElementById('number').value;
            const pRangesStr = document.getElementById('article_ranges').value;
            const pMergeStr = document.getElementById('merge_ranges').value;
            const pRemoveStr = document.getElementById('remove_pages').value;

            // Parsers
            let articleRanges = parseRanges(pRangesStr, totalPdfPages);
            articleRanges = mergeArticles(articleRanges, pMergeStr);
            const removePages = parseRemovePages(pRemoveStr, totalPdfPages);

            logProgress("Inputs parsed. Preparing JSZip compression engine...");
            const zip = new JSZip();
            const originalDoc = await PDFDocument.load(globalPdfBytes);

            progressBar.style.width = '30%';

            for (let i = 0; i < articleRanges.length; i++) {
                const range = articleRanges[i];
                logProgress(`Processing: Article Block ${i + 1}/${articleRanges.length} (Pages: ${range.join(',')})`);

                // PDF Splitting (pdf-lib)
                const newPdf = await PDFDocument.create();
                const pagesToCopy = range.filter(p => !removePages.includes(p)).map(p => p - 1);

                if (pagesToCopy.length === 0) continue;

                const copiedPages = await newPdf.copyPages(originalDoc, pagesToCopy);
                copiedPages.forEach(p => newPdf.addPage(p));
                const newPdfBytes = await newPdf.save();

                const startP = Math.min(...range);
                const endP = Math.max(...range);
                const baseName = generateFilename(year, number, startP, endP);

                // Add PDF
                zip.file(`output${year}${number}/pdf/${baseName}.pdf`, newPdfBytes);

                // Generate Images (Canvas pdf.js)
                logProgress(`  -> Generating thumbnail images (Small & Large)...`);
                const { small, large } = await renderScaledImages(newPdfBytes, 1);
                zip.file(`output${year}${number}/small/${baseName}.jpg`, small, { base64: true });
                zip.file(`output${year}${number}/large/${baseName}.jpg`, large, { base64: true });

                // Extract Text (PyPDF2 mapping)
                logProgress(`  -> Extracting raw text from PDF...`);
                // Directly extracting embedded text from newPdfBytes
                const extractedText = await extractTextFromPdf(newPdfBytes);
                zip.file(`output${year}${number}/ocr/${baseName}.txt`, extractedText);
            }

            progressBar.style.width = '80%';
            logProgress("All PDFs processed. Creating ZIP archive...");

            const content = await zip.generateAsync({ type: "blob" });

            progressBar.style.width = '100%';
            logProgress("Process completed successfully!");

            document.getElementById('notificationSound').play();

            const outputName = `output${year}${number}.zip`;
            downloadLinks.innerHTML = `
                <button id="downloadBtn" class="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded mx-auto block transition duration-300 shadow-lg">
                    ⬇️ Download (${outputName})
                </button>
            `;

            document.getElementById('downloadBtn').addEventListener('click', () => {
                saveAs(content, outputName);
            });

            resultDiv.classList.remove('hidden');

        } catch (e) {
            logProgress("ERROR: " + e.message);
            alert("Error during processing: " + e.message);
        } finally {
            btnText.textContent = "Process PDF";
            submitBtn.disabled = false;
        }
    });

});
