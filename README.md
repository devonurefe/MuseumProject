# PDF Verwerking Tool

Een web-gebaseerde tool voor het verwerken van PDF-documenten en het genereren van verschillende output formaten. De tool ondersteunt het extraheren van afbeeldingen, OCR-verwerking, en het combineren van specifieke artikelen.

## Functionaliteiten

- PDF uploaden en verwerken
- Genereren van small en large afbeeldingen
- OCR-verwerking van PDF-inhoud
- Combineren van geselecteerde artikelen
- Automatische bestandsnaamgeneratie volgens gestandaardiseerd formaat
- Meertalige interface (Nederlands)

## Technische Vereisten

- Python 3.8+
- Flask
- PyPDF2
- Pillow
- Tesseract OCR

## Installatie

1. Clone de repository:
```bash
git clone https://github.com/yourusername/pdf-processor.git
cd pdf-processor
```

2. Installeer de vereiste packages:
```bash
pip install -r requirements.txt
```

3. Installeer Tesseract OCR:
- Voor Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- Voor Windows: Download van de [officiële website](https://github.com/UB-Mannheim/tesseract/wiki)

## Gebruik

1. Start de server:
```bash
python app.py
```

2. Open een browser en ga naar `http://localhost:5000`
3. Upload een PDF bestand
4. Optioneel: specificeer artikelpagina's om te combineren
5. Verwerk het bestand en download de resultaten

## Bestandsnaamconventies

- Reguliere outputs: `YYYYMMDDPP.ext`
  - YYYY: jaar
  - MM: maand
  - DD: dag
  - PP: paginanummer
- Gecombineerde artikelen: `YYYYMMDDSSEE.ext`
  - SS: startpagina
  - EE: eindpagina

## Deployment

De applicatie kan worden gedeployed op verschillende platforms:

### Vercel
1. Fork deze repository
2. Maak een nieuwe project aan op Vercel
3. Connect met je GitHub repository
4. Deploy

### Heroku
1. Maak een nieuw Heroku project
2. Voeg de Python buildpack toe
3. Deploy vanuit je GitHub repository

## Veiligheid

- Implementeer rate limiting voor uploads
- Valideer bestandstypes
- Scan uploads op malware
- Gebruik HTTPS voor alle verkeer
- Implementeer gebruikersauthenticatie indien nodig

## Database

Voor productie wordt aangeraden:
- PostgreSQL voor gebruikersgegevens en bestandsmetadata
- S3 of vergelijkbare object storage voor bestandsopslag

## Licentie

MIT License - Zie LICENSE bestand voor details

## Bijdragen

Bijdragen zijn welkom! Zie CONTRIBUTING.md voor details.
