ABI e CAB per Banche Italiane
=============================

Introduzione
------------
Il modulo `bank_abicab` è un'estensione avanzata per Odoo che migliora significativamente la gestione delle banche italiane. Progettato per automatizzare e semplificare l'inserimento e la gestione dei codici ABI (Associazione Bancaria Italiana) e CAB (Codice di Avviamento Bancario), questo modulo è essenziale per le aziende che operano nel contesto bancario italiano.

Caratteristiche Principali
--------------------------
1. **Estensione dei Modelli Bancari**
   - Aggiunge i campi ABI e CAB ai modelli `res.bank` e `res.partner.bank`.
   - Implementa relazioni tra i campi per una gestione coerente dei dati.

2. **Aggiornamento Automatico via Cron**
   - Funzione `cron_associate_bank_abicab` per l'associazione automatica di ABI e CAB.
   - Scansiona e aggiorna i conti bancari italiani senza codici ABI e CAB.

3. **Integrazione con Schwifty**
   - Utilizza la libreria `schwifty` per la validazione e l'analisi degli IBAN.
   - Estrae automaticamente il BIC (Bank Identifier Code) dagli IBAN.

4. **Gestione Intelligente delle Banche**
   - Crea automaticamente nuovi record `res.bank` se non esistono corrispondenze ABI/CAB.
   - Associa i conti bancari esistenti basandosi sui codici ABI e CAB.

5. **Arricchimento Dati Bancari**
   - Popola automaticamente informazioni come nome, indirizzo, città e CAP della banca.
   - Associa le banche alle corrette regioni e paesi italiani.

6. **Gestione degli Errori**
   - Sistema robusto di logging per tracciare e gestire le eccezioni.
   - Opzione commentata per il posting di messaggi in caso di errori (personalizzabile).

Dettagli Tecnici
----------------
- **Modello ResBank**
  - Estende `res.bank` con campi `abi` e `cab` (entrambi Char, lunghezza 5).

- **Modello ResPartnerBank**
  - Estende `res.partner.bank` con campi `bank_abi` e `bank_cab`.
  - Implementa relazioni con `bank_id` per ABI e CAB.

- **Funzione Cron `cron_associate_bank_abicab`**
  - Ricerca conti bancari italiani senza ABI/CAB.
  - Elabora ogni conto:
    1. Estrae ABI e CAB dall'IBAN.
    2. Cerca corrispondenze nel modello `bank.abicab`.
    3. Crea o aggiorna il record `res.bank`.
    4. Associa il conto bancario alla banca corrispondente.

Dipendenze
----------
- **Moduli Odoo**: `base`, `account`, `contacts`
- **Librerie Python**: `schwifty` (per la gestione IBAN/BIC)

Installazione e Configurazione
------------------------------
1. Installare il modulo tramite l'interfaccia Odoo o via comando:
   ```
   pnpm install
   ```
2. Assicurarsi che la libreria `schwifty` sia installata:
   ```
   pip install schwifty
   ```
3. Configurare il job cron per l'esecuzione automatica di `cron_associate_bank_abicab`.

Sicurezza e Dati
----------------
- File di sicurezza: `security/ir.model.access.csv`
- Dati iniziali e configurazioni: `data/data.xml`
- Assicurarsi che gli utenti abbiano i permessi appropriati per accedere e modificare i dati bancari.

Interfaccia Utente
------------------
- Viste personalizzate in `views/abicab.xml`
- Asset frontend in `bank_abicab/static/src/`
- Integrazione con l'interfaccia di gestione banche di Odoo

Risoluzione Problemi
--------------------
- Controllare i log di Odoo per eventuali errori durante l'esecuzione del cron job.
- Verificare la corretta installazione di `schwifty` in caso di problemi con la gestione IBAN.
- Per problemi di associazione, controllare la correttezza dei dati nel modello `bank.abicab`.

Sviluppi Futuri
---------------
- Implementazione di un'interfaccia per l'aggiornamento manuale dei codici ABI/CAB.
- Miglioramento della gestione degli errori con notifiche utente più dettagliate.
- Possibile integrazione con API bancarie italiane per aggiornamenti in tempo reale.

Supporto e Contributi
---------------------
Per supporto, segnalazione bug o contributi, contattare:
- Autore: FL1 sro
- Sito Web: https://fl1.cz
- Email: [inserire email di supporto]

Licenza
-------
Questo modulo è distribuito sotto licenza LGPL-3. Per i dettagli completi, consultare il file LICENSE incluso nel modulo.