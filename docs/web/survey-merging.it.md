🌍 Lingue disponibili: [🇬🇧 English](survey-merging.md) | [🇮🇹 Italiano](survey-merging.it.md)

# Unione dei Rilievi — Combinare Rilievo Padre e Figlio

## Panoramica

CaveSketch consente di combinare un rilievo **padre** con un rilievo **figlio** — mappa DXF e/o sezione DXF — in un unico PDF unificato.

## Come Funziona

Nella pagina **Survey Plot**, sotto i pulsanti di caricamento principali, compare una sezione dedicata all'unione. Il flusso di lavoro è:

1. **Caricare il rilievo figlio** — una mappa `.dxf` e/o una sezione `.dxf`.
2. **Specificare gli ID delle stazioni corrispondenti** tra padre e figlio (una coppia che collega i due rilievi).
3. Una **singola coppia di ID stazione** si applica sia alla mappa che alla sezione DXF, poiché lo stesso progetto TopoDroid utilizza la stessa numerazione.

> **Formato ID stazione:** gli ID devono essere puramente numerici (es. `30`, `47`). ID contenenti lettere (es. `12P4`) identificano geometrie di pareti o linee, non stazioni di rilievo — vengono rifiutati con un chiaro messaggio di errore.

Per unire ulteriori rilievi oltre a un figlio, scaricare il risultato unito e ricaricarlo come nuovo padre.

![Interfaccia di unione](imgs/merge-ui.png)

## Vista in Pianta

La vista in pianta utilizza sempre l'**Unione Semplice**: il figlio viene traslato in modo che la sua stazione corrispondente coincida con quella del padre. Non viene esposto alcun selettore di protocollo per la vista in pianta.

## Protocolli per la Vista in Sezione

Per la vista in sezione, si seleziona un protocollo di unione tramite un controllo radio/select:

### Unione Semplice

La stazione corrispondente del figlio viene allineata a quella del padre. Entrambi i rilievi sono disegnati nello stesso spazio di coordinate.

### Specchio Semplice

Come l'Unione Semplice, ma il figlio viene **specchiato rispetto all'asse verticale (asse y)** prima del posizionamento. Utile quando i rilievi si avvicinano alla giunzione da direzioni opposte.

![Protocollo specchio](imgs/merge-mirror.png)

### Dislocamento

Il figlio viene posizionato in un'**area separata e non sovrapposta**. La direzione di ricerca è: prima a destra, poi in basso. Due sottili linee di connessione vengono tracciate dalla stazione corrispondente del padre a quella del figlio, collegando visivamente i due segmenti di rilievo.

![Protocollo dislocamento](imgs/merge-displacement.png)

## Impostazioni e Rendering

Tutte le impostazioni — rotazione, scala, spessore linea, dimensione testo, ecc. — si applicano all'**intero risultato unito**. Se il risultato unito supera le dimensioni della pagina PDF, viene automaticamente riscalato per adattarsi.

## Gestione degli Errori

Se un ID stazione non è valido (non trovato nel DXF caricato), viene visualizzato un messaggio di errore inline e la generazione del PDF viene bloccata fino alla correzione del problema.

---

[Torna alla documentazione Web](README.it.md)
