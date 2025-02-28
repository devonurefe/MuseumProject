# 📄 PDF Verwerking Tool 🛠️

Een web-gebaseerde tool voor het verwerken van PDF-documenten en het genereren van verschillende outputformaten. De tool ondersteunt het extraheren van afbeeldingen, OCR-verwerking, en het combineren van specifieke artikelen. Perfect voor archivering, documentbeheer en digitale transformatie!

---

## 🌟 Functionaliteiten

- **PDF uploaden en verwerken** 📤
  Upload PDF-bestanden en verwerk ze in een handomdraai.

- **Genereren van small en large afbeeldingen** 🖼️
  Maak kleine (500x700) en grote (1024x1280) afbeeldingen van PDF-pagina's.

- **OCR-verwerking van PDF-inhoud** 🔍
  Extraheer tekst uit PDF's met behulp van Tesseract OCR, ondersteund voor Nederlands en Engels.

- **Combineren van geselecteerde artikelen** 📑
  Selecteer specifieke pagina's of artikelen en combineer ze tot één document.

- **Automatische bestandsnaamgeneratie** 📂
  Bestanden worden automatisch benoemd volgens een gestandaardiseerd formaat (bijv. `YYYYMMDDPP.ext`).

---

## 🛠️ Technische Vereisten

- **Python 3.10.11+** 🐍
  De tool is geschreven in Python en vereist minimaal versie 3.10.11.

- **Flask** 🌐
  Gebruikt voor het bouwen van de webapplicatie.

- **PyPDF2** 📑
  Voor het lezen en manipuleren van PDF-bestanden.

- **Pillow** 🖼️
  Voor het verwerken en opslaan van afbeeldingen.

- **Tesseract OCR** 🔍
  Voor het uitvoeren van optische karakterherkenning (OCR).

---

## 🚀 Installatie

1. **Clone de repository:**
   ```bash
   git clone https://github.com/devonurefe/MuseumProject
Installeer de vereiste packages:

Copy
pip install -r requirements.txt
Installeer Tesseract OCR:

Ubuntu/Debian:
Copy
sudo apt-get install tesseract-ocr
Windows: Download en installeer Tesseract van de officiële website.
🖥️ Gebruik
Start de server:

Copy
python app.py
Open een browser en ga naar:
http://localhost:5000

Upload een PDF-bestand 📤
Selecteer een PDF-bestand en upload het naar de tool.

Optioneel: specificeer artikelpagina's om te combineren 📑
Geef aan welke pagina's of artikelen je wilt combineren.

Verwerk het bestand en download de resultaten ⬇️
De tool genereert PDF's, afbeeldingen en OCR-tekstbestanden die je kunt downloaden.

📂 Bestandsnaamconventies
Reguliere outputs:
YYYYMMDDPP.ext
YYYY: jaar
MM: maand
DD: dag
PP: paginanummer
Gecombineerde artikelen:
YYYYMMDDSSEE.ext
SS: startpagina
EE: eindpagina
🌍 Deployment
De applicatie kan worden gedeployed op verschillende platforms:
Windows desktop versie
Download de desktopversie voor Windows.

Webversie:
Bezoek de live versie op [https://museumproject.onrender.com]

🔒 Veiligheid
Rate limiting voor uploads ⏳
Beperk het aantal uploads per gebruiker om misbruik te voorkomen.

Validatie van bestandstypes ✅
Alleen PDF-bestanden worden geaccepteerd.

Malware scanning 🛡️
Scan uploads op malware voordat ze worden verwerkt.

HTTPS voor alle verkeer 🔐
Gebruik HTTPS om gegevens te versleutelen.

Gebruikersauthenticatie 🔑
Optioneel: implementeer gebruikersauthenticatie voor extra beveiliging.

📜 Licentie
Deze tool is vrijgegeven onder de MIT License. Zie het LICENSE-bestand voor meer details.

🤝 Bijdragen
Bijdragen zijn welkom! 🎉
Zie CONTRIBUTING.md voor details over hoe je kunt bijdragen aan dit project.

📧 Contact
Voor vragen of meer informatie, neem contact op via:
📧 koris.onur@gmail.com

💧 Powered by h2O
Deze tool is mede mogelijk gemaakt door h2O – omdat elke druppel telt! 💧

🎉 Geniet van het verwerken van je PDF's! 🎉
