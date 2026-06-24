🌍 Lingue disponibili: [🇬🇧 English](README.md) | [🇮🇹 Italiano](README.it.md)

# CaveSketch per Android — Guida Utente

CaveSketch per Android è un'app nativa Android utilizzabile offline che sfrutta
lo stesso motore Python di elaborazione rilievi dell'app web CaveSketch. Tutta
l'elaborazione avviene **interamente sul dispositivo** — nessun server
necessario.

---

## Installazione

1. Scarica **`CaveSketch-1.0.0.apk`** dalle
   [Release su GitHub](https://github.com/LorBordin/cave_sketch/releases).
2. Android chiederà di consentire l'installazione da fonti sconosciute.
   Abilita in **Impostazioni → App → Accesso speciale → Installa app
   sconosciute** e concedi il permesso al browser o al file manager.
3. Tocca **Installa**.

> [!TIP]
> **Aggiornamenti**: Scarica semplicemente un APK più recente e installalo
> sopra la versione esistente — le impostazioni vengono mantenute (l'APK usa
> la stessa chiave di firma).

---

## Le Tre Schermate

### 📋 Rilievo Topografico

Seleziona file DXF dal dispositivo e configura l'output del rilievo:

- **Nome rilievo** e **rilevatore**
- **Scala** e **lunghezza scala grafica**
- **Rotazione**
- **Zoom marcatori / testo / spessore linee**
- **Marcatori stazione** e **griglia**
- Unione opzionale con un **rilievo figlio** (ID stazione + protocollo sezione)

Tocca **Genera** per produrre un'anteprima PDF, poi **Salva** o **Condividi**
il risultato.

![Rilievo — selezione file e impostazioni base](../mobile-app/screenshots_v1/survey_1.jpg)

![Rilievo — opzioni zoom e marcatori](../mobile-app/screenshots_v1/survey_2.jpg)

![Rilievo — unione con rilievo figlio](../mobile-app/screenshots_v1/survey_3.jpg)

![Rilievo — anteprima PDF](../mobile-app/screenshots_v1/survey_4.jpg)

---

### 🌍 Mappa Satellitare

Aggiungi punti di riferimento GPS (ID stazione, latitudine, longitudine) e
configura:

- **Nome rilievo** e **rotazione**
- Importazione opzionale di una **mappa JSON** per sovrapposizione
  multi-rilievo

Tocca **Genera** per produrre:

- **Anteprima HTML** (richiede connessione per i server di tile satellitari)
- **Esportazione JSON** (formato mappa grotta)
- **Esportazione KMZ** (per Google Earth)

**Salva** o **Condividi** ogni output in modo indipendente.

![Mappa satellitare — inserimento punti GPS](../mobile-app/screenshots_v1/satellite_1.jpg)

![Mappa satellitare — configurazione e generazione](../mobile-app/screenshots_v1/satellite_2.jpg)

![Mappa satellitare — anteprima satellitare HTML](../mobile-app/screenshots_v1/satellite_3.jpg)

---

### ℹ️ Informazioni

Mostra la versione dell'app e fornisce un collegamento al
[repository GitHub](https://github.com/LorBordin/cave_sketch).

![Schermata Informazioni](../mobile-app/screenshots_v1/about.jpg)

---

## Comportamento Offline

| Funzionalità | Offline | Note |
|---|---|---|
| Generazione PDF | ✅ | Interamente sul dispositivo |
| Esportazione KMZ | ✅ | Interamente sul dispositivo |
| Esportazione JSON | ✅ | Interamente sul dispositivo |
| Anteprima HTML satellitare | 🌐 | Richiede connessione per i server di tile online |

> [!NOTE]
> Quando il dispositivo è offline, l'anteprima HTML satellitare mostra un
> banner **"No connection — satellite preview unavailable"**, ma le
> esportazioni KMZ e JSON vengono generate normalmente.

---

## Per i Contributori

Curioso di come è costruita l'app? Consulta il documento
[Architettura e Stack Tecnologico](architecture.md) per i dettagli tecnici
sull'implementazione Android.

---

[Torna al README principale](../../README.it.md)
