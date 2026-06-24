# 🗺️ CaveSketch

[![CI](https://github.com/LorBordin/cave_sketch/actions/workflows/ci.yml/badge.svg)](https://github.com/LorBordin/cave_sketch/actions/workflows/ci.yml)

🌍 Lingue disponibili: [🇬🇧 English](README.md) | [🇮🇹 Italiano](README.it.md)

**Disegna le tue poligonali in pochi secondi — direttamente da TopoDroid!**
Niente più software pesanti, niente più configurazioni complicate. Solo file DXF, il tuo telefono o browser e la tua prossima spedizione.

---

## 🚀 Due modi per usare CaveSketch

### 🌐 Web App (Online)
Nessuna installazione richiesta. Funziona direttamente nel browser web.
- 🔗 **Prova l'app live:** [cavesketch.streamlit.app](https://cavesketch.streamlit.app/)
- 📖 **Documentazione Web:** Consulta le [Guide per la Web App](docs/web/README.it.md) per i dettagli sulle funzionalità avanzate online.

### 📱 App Android (Interamente Offline)
Perfetta per l'uso sul campo e campi base offline. Esegue tutto il rendering del rilievo direttamente sul dispositivo.
- 📥 **Scarica l'APK:** Ottieni l'ultima versione dalle [Release su GitHub](https://github.com/LorBordin/cave_sketch/releases).
- 📖 **Documentazione Android:** Consulta la [Guida Utente Android](docs/android/README.it.md) per l'installazione e l'uso.
- 💻 **Contributori Android:** Leggi la guida su [Architettura e Stack Android](docs/android/architecture.it.md).

---

## 🧭 Funzionalità in breve

- 🖨️ **Rilievi Speleologici in PDF** — Genera pianta e sezione ad alta qualità pronte per la stampa con scala, rotazione, griglia personalizzabili e scala grafica integrata.
- 🔗 **Unione dei Rilievi** — Unisci un rilievo padre e uno figlio direttamente nel grafico del rilievo, con supporto a più protocolli per la sezione (Semplice, Specchio, Dislocamento).
- 🌍 **Sovrapposizione su Immagini Satellitari** — Posiziona la mappa della grotta su immagini satellitari georeferenziate tramite punti GPS (più punti si inseriscono, migliore sarà la precisione).
- 🗺️ **Mappe con Più Rilievi** — Combina più rilievi indipendenti su un'unica vista satellitare tramite l'esportazione e re-importazione in formato JSON.
- 📦 **Esportazione KMZ e KML Offline** — Esporta archivi KMZ ottimizzati e autonomi da usare offline in applicazioni cartografiche per dispositivi mobili come Locus Map o OsmAnd.

Per guide dettagliate su come utilizzare queste funzioni, esplora la [Documentazione della Web App](docs/web/README.it.md) o la [Guida Utente Android](docs/android/README.it.md).

---

## 📸 Prerequisito: Esportare da TopoDroid

Per utilizzare CaveSketch, devi esportare i tuoi schizzi da TopoDroid come file **.dxf**:

1. Dalla finestra principale del progetto in TopoDroid, tocca il pulsante Modifica Schizzo <img src="imgs/topodroid_icon.png" style="width: 20px;"> e seleziona la pianta della grotta.
2. Tocca i 3 pulsanti/puntini in alto a sinistra e seleziona `Esporta`.
3. Scegli l'opzione `DXF` e tocca `Salva`.
4. Esporta la sezione della grotta nello stesso modo.

<div style="display: flex; gap: 10px; justify-content: space-between;">
  <img src="imgs/map_export.jpg" style="width: 200px;">
  <img src="imgs/export_format.jpg" style="width: 200px;">
  <img src="imgs/section_export.jpg" style="width: 200px;">
</div>

---

## 💻 Per sviluppatori

### 🔧 Configurazione per lo sviluppo

1. **Clona il repository**:
   ```bash
   git clone https://github.com/LorBordin/cave_sketch.git
   cd cave_sketch
   ```
2. **Installa le dipendenze**:
   ```bash
   uv sync
   ```
3. **Installa i pre-commit hook**:
   ```bash
   uv run pre-commit install
   ```
4. **Esegui l'app di sviluppo locale**:
   ```bash
   uv run streamlit run app/app.py
   ```

### 🧑‍💻 Contribuisci
Hai trovato un bug? Hai un'idea? Le PR sono benvenute!
Per contribuire:
1. Fai il fork del repo.
2. Crea un nuovo branch.
3. Committa le modifiche.
4. Apri una pull request 🚀

---

## 📋 Cose da fare (Aperto ai contributi)

Aiutaci a rendere CaveSketch ancora migliore!

- 🎨 Aggiungere l'opzione per colorare le aree, non solo disegnare linee.
- 🛰️ Migliorare il rendering della mappa satellitare in HTML.
- 🧊 Disegnare ed esportare modelli 3D delle grotte.
