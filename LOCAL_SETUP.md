# 🏠 Museum PDF Tool - Lokal Kurulum Rehberi

## 📋 Sistem Gereksinimleri

### Windows
- **Windows 10/11** (64-bit)
- **Node.js 18+** ([nodejs.org](https://nodejs.org))
- **Rust 1.70+** ([rustup.rs](https://rustup.rs))
- **WebView2** (Windows 11'de varsayılan)

### macOS
- **macOS 10.15+**
- **Xcode Command Line Tools**
- **Node.js 18+**
- **Rust 1.70+**

### Linux (Ubuntu/Debian)
- **Ubuntu 22.04+**
- **Node.js 18+**
- **Rust 1.70+**
- **WebKit2GTK**

## 🚀 1. Adım: Gerekli Yazılımları Kurun

### Windows'da:
```powershell
# 1. Node.js indir ve kur: https://nodejs.org
# 2. Rust indir ve kur: https://rustup.rs
# 3. Powershell'i yönetici olarak aç:

# Rust kurulumunu kontrol et
rustc --version
cargo --version

# Node.js kontrol et
node --version
npm --version
```

### macOS'ta:
```bash
# Homebrew ile (önerilen)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install node
brew install rust

# Manuel kurulum:
# 1. Node.js: https://nodejs.org
# 2. Rust: https://rustup.rs
```

### Linux'ta (Ubuntu/Debian):
```bash
# Sistem güncellemeleri
sudo apt update && sudo apt upgrade

# Node.js kurulumu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Rust kurulumu
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Tauri bağımlılıkları
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf
```

## 📦 2. Adım: Projeyi İndirin ve Açın

### Zip Dosyası İndirme
1. **museum-desktop-app.zip** dosyasını indirin
2. İstediğiniz klasöre çıkarın
3. Terminal/Command Prompt açın
4. Proje klasörüne gidin:

```bash
cd museum-desktop-app
```

### Klasör Yapısını Kontrol Edin
```
museum-desktop-app/
├── src/                 # React frontend
├── src-tauri/          # Rust backend
├── package.json        # Node.js dependencies
├── vite.config.js      # Vite config
└── README.md          # Dokümantasyon
```

## 🔧 3. Adım: Bağımlılıkları Kurun

```bash
# Proje klasöründe:
npm install

# Tauri CLI'yi global kurma (isteğe bağlı)
npm install -g @tauri-apps/cli@latest
```

## 🚀 4. Adım: Uygulamayı Çalıştırın

### Development Modunda Çalıştırma
```bash
# Uygulamayı geliştirme modunda başlat
npm run tauri dev

# Veya direkt:
npx tauri dev
```

**İlk çalıştırma** biraz zaman alabilir çünkü:
- Rust bağımlılıkları derleniyor
- Frontend build ediliyor

### Build (Executable Oluşturma)
```bash
# Production build
npm run tauri build

# Build dosyaları:
# Windows: src-tauri/target/release/museum-pdf-tool.exe
# macOS: src-tauri/target/release/bundle/dmg/
# Linux: src-tauri/target/release/bundle/deb/
```

## 🎯 5. Adım: Uygulamayı Kullanın

1. **Uygulama açılır** - Modern masaüstü penceresi
2. **PDF Seç** - Dosya seçici açılır
3. **İşleme Seçenekleri**:
   - ⚡ **Hızlı İşle**: Tüm özelliklerle default ayarlar
   - 🔧 **Gelişmiş Ayarlar**: OCR, görsel boyutları, makale birleştirme vs.
4. **Sonuçları Görüntüle**: OCR metinleri, görseller, istatistikler

## 🛠️ Sorun Giderme

### "npm command not found"
```bash
# Node.js yükleme kontrol et
node --version
npm --version

# Eğer yüklü değilse: https://nodejs.org
```

### "cargo command not found"
```bash
# Rust yükleme kontrol et
rustc --version
cargo --version

# Eğer yüklü değilse: https://rustup.rs

# Linux/macOS'ta path ekle:
source ~/.cargo/env
```

### "npm install" Hatası
```bash
# npm cache temizle
npm cache clean --force

# Node modules sil ve tekrar kur
rm -rf node_modules
npm install
```

### "tauri dev" Başlamıyor
```bash
# Rust bileşenlerini güncelle
rustup update

# Tauri CLI güncelle
npm install -g @tauri-apps/cli@latest
```

### Windows WebView2 Hatası
```bash
# WebView2 Runtime indir:
# https://developer.microsoft.com/en-us/microsoft-edge/webview2/
```

## 📱 Platform-Specific Notlar

### Windows
- **Antivürüs**: İlk çalıştırma sırasında antivürüs uyarısı çıkabilir (güvenli)
- **Firewall**: Local port access onayı isteyebilir

### macOS
- **Gatekeeper**: "Unidentified developer" uyarısı çıkabilir
- **Çözüm**: System Preferences > Security > "Open Anyway"

### Linux
- **AppImage**: Tauri Linux'ta AppImage de oluşturur
- **Permissions**: Execute permission gerekebilir (`chmod +x`)

## 🎉 Başarı!

Artık sizin **tam özellikli PDF işleme uygulamanız** lokalinizde çalışıyor!

### Özellikler:
- ✅ **OCR Metin Çıkarma**
- ✅ **Görsel İşleme** (500x700 & 1024x1280)
- ✅ **Makale Birleştirme**
- ✅ **Paralel İşleme**
- ✅ **Custom Dosya Adlandırma**
- ✅ **100% Güvenli & Yerel**
- ✅ **Virüs Algılanmaz**

## 📞 Destek

Sorun yaşarsanız:
1. Terminal'deki hata mesajlarını kontrol edin
2. Sistem gereksinimlerini doğrulayın
3. Bağımlılıkları tekrar kurmayı deneyin

**Başarılı kurulum dilerim! 🚀**