// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::Path;
use std::fs;
use serde::{Deserialize, Serialize};
use base64;

#[derive(Debug, Serialize, Deserialize)]
struct ProcessResult {
    success: bool,
    message: String,
    data: Option<ProcessedData>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ProcessedData {
    images: Vec<String>, // Base64 encoded images
    text: String,
    pages: usize,
}

// PDF işleme fonksiyonu
#[tauri::command]
async fn process_pdf(file_path: String) -> Result<ProcessResult, String> {
    println!("Processing PDF: {}", file_path);
    
    if !Path::new(&file_path).exists() {
        return Ok(ProcessResult {
            success: false,
            message: "File not found".to_string(),
            data: None,
        });
    }

    match extract_pdf_content(&file_path).await {
        Ok(data) => Ok(ProcessResult {
            success: true,
            message: "PDF processed successfully".to_string(),
            data: Some(data),
        }),
        Err(e) => Ok(ProcessResult {
            success: false,
            message: format!("Error processing PDF: {}", e),
            data: None,
        }),
    }
}

// PDF içeriğini çıkart
async fn extract_pdf_content(file_path: &str) -> Result<ProcessedData, Box<dyn std::error::Error>> {
    let file_content = fs::read(file_path)?;
    
    // PDF'den metin çıkar
    let text = match pdf_extract::extract_text_from_mem(&file_content) {
        Ok(content) => content,
        Err(_) => "Text extraction failed".to_string(),
    };

    // Basit bir PDF sayfa sayısı hesaplama
    let pages = text.matches("\n").count().max(1);

    // Mock resim verisi (gerçek implementasyonda PDF'i görüntüye çevireceksiniz)
    let mock_image = create_placeholder_image();
    let images = vec![mock_image];

    Ok(ProcessedData {
        images,
        text,
        pages,
    })
}

// Placeholder resim oluştur
fn create_placeholder_image() -> String {
    // 200x300 piksel beyaz bir resim
    let width = 200;
    let height = 300;
    let mut img = image::RgbImage::new(width, height);
    
    // Beyaz arka plan
    for pixel in img.pixels_mut() {
        *pixel = image::Rgb([255, 255, 255]);
    }
    
    // PNG formatında encode et
    let mut buffer = Vec::new();
    let mut cursor = std::io::Cursor::new(&mut buffer);
    img.write_to(&mut cursor, image::ImageFormat::Png).unwrap();
    
    // Base64'e çevir
    base64::encode(&buffer)
}

// Dosya seçimi için yardımcı
#[tauri::command]
async fn select_pdf_file() -> Result<Option<String>, String> {
    use tauri_plugin_dialog::{DialogExt, FileDialogBuilder};
    
    let file_path = FileDialogBuilder::new()
        .add_filter("PDF files", &["pdf"])
        .pick_file()
        .await;
    
    match file_path {
        Some(path) => Ok(Some(path.to_string_lossy().to_string())),
        None => Ok(None),
    }
}

// Sistem bilgisi
#[tauri::command]
fn get_system_info() -> String {
    format!(
        "Museum PDF Tool v1.0 - Running on {} {}",
        std::env::consts::OS,
        std::env::consts::ARCH
    )
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            process_pdf,
            select_pdf_file,
            get_system_info
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}