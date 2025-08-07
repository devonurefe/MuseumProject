import React, { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

function App() {
  const [selectedFile, setSelectedFile] = useState("");
  const [fileInfo, setFileInfo] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [systemInfo, setSystemInfo] = useState("");
  const [processingOptions, setProcessingOptions] = useState({
    pages_to_remove: [],
    article_ranges: null,
    merge_article_indices: [],
    year: "2024",
    number: "01",
    enable_ocr: true,
    generate_small_images: true,
    generate_large_images: true,
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    // Sistem bilgisini al
    invoke("get_system_info").then((info) => {
      setSystemInfo(info);
    });
  }, []);

  const selectFile = async () => {
    try {
      const filePath = await open({
        filters: [
          {
            name: "PDF",
            extensions: ["pdf"],
          },
        ],
        multiple: false,
      });

      if (filePath) {
        setSelectedFile(filePath);
        setResult(null);
        
        // PDF dosyasını validate et
        try {
          const validation = await invoke("validate_pdf_file", { filePath });
          setFileInfo(validation);
        } catch (error) {
          console.error("PDF validation error:", error);
          alert(`PDF validation error: ${error}`);
        }
      }
    } catch (error) {
      console.error("Dosya seçimi hatası:", error);
      alert("Dosya seçimi sırasında hata oluştu.");
    }
  };

  const processPDF = async () => {
    if (!selectedFile) {
      alert("Lütfen önce bir PDF dosyası seçin.");
      return;
    }

    setIsProcessing(true);
    try {
      // Advanced options ile tam özellikli processing
      const response = await invoke("process_pdf_full", { 
        filePath: selectedFile,
        options: processingOptions
      });
      
      setResult(response);
      
      if (response.success) {
        alert(`PDF başarıyla işlendi! ${response.data.statistics.total_files_created} dosya oluşturuldu.`);
      } else {
        alert(`Hata: ${response.message}`);
      }
    } catch (error) {
      console.error("PDF işleme hatası:", error);
      alert("PDF işleme sırasında hata oluştu.");
    } finally {
      setIsProcessing(false);
    }
  };

  const quickProcess = async () => {
    if (!selectedFile) {
      alert("Lütfen önce bir PDF dosyası seçin.");
      return;
    }

    setIsProcessing(true);
    try {
      // Hızlı işleme - default ayarlar
      const response = await invoke("process_pdf", { filePath: selectedFile });
      setResult(response);
      
      if (response.success) {
        alert("PDF hızlı işleme tamamlandı!");
      } else {
        alert(`Hata: ${response.message}`);
      }
    } catch (error) {
      console.error("PDF işleme hatası:", error);
      alert("PDF işleme sırasında hata oluştu.");
    } finally {
      setIsProcessing(false);
    }
  };

  const updateOption = (key, value) => {
    setProcessingOptions(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleArrayInput = (key, value) => {
    try {
      const array = value.split(',').map(item => parseInt(item.trim())).filter(num => !isNaN(num));
      updateOption(key, array);
    } catch (error) {
      console.error("Array input error:", error);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>🏛️ Museum PDF Tool - Full Featured</h1>
        <p className="subtitle">OCR • Image Processing • Article Merging • Batch Operations</p>
        <div className="system-info">{systemInfo}</div>
      </header>

      <main className="main">
        <div className="upload-section">
          <div className="file-selector">
            <button className="btn btn-primary" onClick={selectFile}>
              📁 PDF Dosyası Seç
            </button>
            {selectedFile && (
              <div className="selected-file">
                <span className="file-icon">📄</span>
                <span className="file-name">{selectedFile.split('/').pop()}</span>
                {fileInfo && (
                  <div className="file-details">
                    <span>📊 {fileInfo.pages} sayfa • 💾 {Math.round(fileInfo.file_size / 1024)} KB</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Quick Process Button */}
          <button
            className={`btn btn-process ${isProcessing ? 'processing' : ''}`}
            onClick={quickProcess}
            disabled={!selectedFile || isProcessing}
          >
            {isProcessing ? "⚙️ İşleniyor..." : "⚡ Hızlı İşle (Tüm Özellikler)"}
          </button>

          {/* Advanced Options Toggle */}
          <button
            className="btn btn-secondary"
            onClick={() => setShowAdvanced(!showAdvanced)}
            disabled={isProcessing}
          >
            {showAdvanced ? "🔼 Gelişmiş Ayarları Gizle" : "🔽 Gelişmiş Ayarları Göster"}
          </button>

          {/* Advanced Options Panel */}
          {showAdvanced && (
            <div className="advanced-options">
              <h3>🔧 Gelişmiş İşleme Ayarları</h3>
              
              <div className="options-grid">
                <div className="option-group">
                  <label>📅 Yıl:</label>
                  <input
                    type="text"
                    value={processingOptions.year}
                    onChange={(e) => updateOption('year', e.target.value)}
                    placeholder="2024"
                  />
                </div>

                <div className="option-group">
                  <label>🔢 Numara:</label>
                  <input
                    type="text"
                    value={processingOptions.number}
                    onChange={(e) => updateOption('number', e.target.value)}
                    placeholder="01"
                  />
                </div>

                <div className="option-group">
                  <label>🗑️ Çıkarılacak Sayfalar (virgülle ayırın):</label>
                  <input
                    type="text"
                    placeholder="Örn: 1,3,5"
                    onChange={(e) => handleArrayInput('pages_to_remove', e.target.value)}
                  />
                </div>

                <div className="option-group">
                  <label>🔗 Birleştirilecek Makale İndeksleri (virgülle ayırın):</label>
                  <input
                    type="text"
                    placeholder="Örn: 1,2,3"
                    onChange={(e) => handleArrayInput('merge_article_indices', e.target.value)}
                  />
                </div>
              </div>

              <div className="feature-toggles">
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={processingOptions.enable_ocr}
                    onChange={(e) => updateOption('enable_ocr', e.target.checked)}
                  />
                  🔍 OCR Metin Çıkarma
                </label>

                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={processingOptions.generate_small_images}
                    onChange={(e) => updateOption('generate_small_images', e.target.checked)}
                  />
                  🖼️ Küçük Görsel (500x700)
                </label>

                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={processingOptions.generate_large_images}
                    onChange={(e) => updateOption('generate_large_images', e.target.checked)}
                  />
                  🖼️ Büyük Görsel (1024x1280)
                </label>
              </div>

              <button
                className={`btn btn-process advanced ${isProcessing ? 'processing' : ''}`}
                onClick={processPDF}
                disabled={!selectedFile || isProcessing}
              >
                {isProcessing ? "⚙️ Gelişmiş İşleme..." : "🚀 Gelişmiş İşleme Başlat"}
              </button>
            </div>
          )}
        </div>

        {result && (
          <div className="results">
            <h2>📊 İşlem Sonuçları</h2>
            
            <div className="status">
              <span className={`status-badge ${result.success ? 'success' : 'error'}`}>
                {result.success ? "✅ Başarılı" : "❌ Hata"}
              </span>
              <span className="message">{result.message}</span>
            </div>

            {result.success && result.data && (
              <div className="processed-data">
                <div className="stats-grid">
                  <div className="stat-item">
                    <span className="stat-label">Toplam Sayfa:</span>
                    <span className="stat-value">{result.data.total_pages}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">İşleme Süresi:</span>
                    <span className="stat-value">{result.data.processing_time_ms}ms</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Küçük Görsel:</span>
                    <span className="stat-value">{result.data.small_images.length}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Büyük Görsel:</span>
                    <span className="stat-value">{result.data.large_images.length}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">OCR Metni:</span>
                    <span className="stat-value">{result.data.ocr_texts.length}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">PDF Dosyası:</span>
                    <span className="stat-value">{result.data.pdf_files.length}</span>
                  </div>
                </div>

                {/* OCR Results */}
                {result.data.ocr_texts.length > 0 && (
                  <div className="content-section">
                    <h3>📝 OCR Çıkarılan Metinler</h3>
                    <div className="ocr-results">
                      {result.data.ocr_texts.map((text, index) => (
                        <div key={index} className="ocr-item">
                          <div className="ocr-header">
                            <span className="filename">📄 {text.filename}</span>
                            <span className="word-count">📊 {text.word_count} kelime</span>
                            <span className="page-range">📑 Sayfa: {text.page_range}</span>
                          </div>
                          <div className="ocr-content">
                            <pre>{text.content.substring(0, 500)}...</pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Small Images */}
                {result.data.small_images.length > 0 && (
                  <div className="content-section">
                    <h3>🖼️ Küçük Görseller (500x700)</h3>
                    <div className="images-grid">
                      {result.data.small_images.map((image, index) => (
                        <div key={index} className="image-item">
                          <img 
                            src={`data:image/png;base64,${image.base64_data}`} 
                            alt={`Small: ${image.filename}`}
                            className="preview-image small"
                          />
                          <div className="image-info">
                            <p className="image-label">{image.filename}</p>
                            <p className="image-details">{image.width}x{image.height} • Sayfa {image.page_number}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Large Images */}
                {result.data.large_images.length > 0 && (
                  <div className="content-section">
                    <h3>🖼️ Büyük Görseller (1024x1280)</h3>
                    <div className="images-grid">
                      {result.data.large_images.map((image, index) => (
                        <div key={index} className="image-item">
                          <img 
                            src={`data:image/png;base64,${image.base64_data}`} 
                            alt={`Large: ${image.filename}`}
                            className="preview-image large"
                          />
                          <div className="image-info">
                            <p className="image-label">{image.filename}</p>
                            <p className="image-details">{image.width}x{image.height} • Sayfa {image.page_number}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Processing Log */}
                {result.log_messages && result.log_messages.length > 0 && (
                  <div className="content-section">
                    <h3>📋 İşleme Logu</h3>
                    <div className="log-container">
                      {result.log_messages.map((log, index) => (
                        <div key={index} className="log-entry">
                          {log}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Statistics Summary */}
                <div className="content-section">
                  <h3>📈 İstatistik Özeti</h3>
                  <div className="statistics">
                    <div className="stat-row">
                      <span>İşlenen Sayfa Sayısı:</span>
                      <span>{result.data.statistics.pages_processed}</span>
                    </div>
                    <div className="stat-row">
                      <span>Oluşturulan Görsel Sayısı:</span>
                      <span>{result.data.statistics.images_generated}</span>
                    </div>
                    <div className="stat-row">
                      <span>OCR İşlenen Sayfa:</span>
                      <span>{result.data.statistics.ocr_pages}</span>
                    </div>
                    <div className="stat-row">
                      <span>Birleştirilmiş Makale:</span>
                      <span>{result.data.statistics.merged_articles}</span>
                    </div>
                    <div className="stat-row">
                      <span>Toplam Oluşturulan Dosya:</span>
                      <span>{result.data.statistics.total_files_created}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="footer">
        <div className="features">
          <div className="feature">
            <span className="feature-icon">🔍</span>
            <span>OCR</span>
          </div>
          <div className="feature">
            <span className="feature-icon">🖼️</span>
            <span>Image Processing</span>
          </div>
          <div className="feature">
            <span className="feature-icon">🔗</span>
            <span>Article Merging</span>
          </div>
          <div className="feature">
            <span className="feature-icon">⚡</span>
            <span>Parallel Processing</span>
          </div>
          <div className="feature">
            <span className="feature-icon">🛡️</span>
            <span>Secure & Local</span>
          </div>
          <div className="feature">
            <span className="feature-icon">🌍</span>
            <span>Cross-Platform</span>
          </div>
        </div>
        <p className="copyright">© 2024 Museum Team - Full Featured PDF Processing Tool 🚀</p>
      </footer>
    </div>
  );
}

export default App;