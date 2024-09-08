Gestione e aggiornamento codici Ateco
=====================================

Introduzione
------------
Il modulo `atecoit` è un'estensione avanzata per Odoo che migliora significativamente la gestione dei codici Ateco per le aziende italiane. Progettato per automatizzare e semplificare l'inserimento e la gestione dei codici Ateco (Classificazione delle attività economiche), questo modulo è essenziale per le aziende che operano nel contesto italiano.

Caratteristiche Principali
--------------------------
1. **Estensione dei Modelli di Contatto**
   - Aggiunge il campo codice Ateco al modello `res.partner`.
   - Implementa relazioni tra i campi per una gestione coerente dei dati.

2. **Aggiornamento Automatico dei Codici Ateco**
   - Funzionalità per l'aggiornamento automatico dei codici dalla repository ufficiale italiana.
   - Mantiene i codici Ateco sempre aggiornati e conformi alle normative.

3. **Gestione Intelligente delle Categorie Ateco**
   - Crea e gestisce automaticamente le categorie Ateco.
   - Associa i contatti alle corrette categorie Ateco.

4. **Interfaccia Utente Migliorata**
   - Viste personalizzate per una facile gestione dei codici Ateco.
   - Integrazione seamless con l'interfaccia di gestione contatti di Odoo.

5. **Ricerca Avanzata**
   - Implementa funzionalità di ricerca avanzata per codici e descrizioni Ateco.

Dettagli Tecnici
----------------
- **Modello AtecoitCategory**
  - Gestisce le categorie Ateco con campi come `name`, `code`, `parent_id`, `child_ids`.

- **Estensione ResPartner**
  - Aggiunge campi relativi ai codici Ateco ai contatti.

- **Funzionalità di Aggiornamento**
  - Implementa metodi per l'aggiornamento automatico dei codici Ateco.

Dipendenze
----------
- **Moduli Odoo**: `base`, `contacts`

Installazione e Configurazione
------------------------------
1. Installare il modulo tramite l'interfaccia Odoo o via comando.
2. Configurare l'accesso alla repository ufficiale dei codici Ateco.
3. Eseguire l'aggiornamento iniziale dei codici Ateco.

Sicurezza e Dati
----------------
- File di sicurezza: `security/ir.model.access.csv`
- Dati iniziali: `data/data.xml`
- Assicurarsi che gli utenti abbiano i permessi appropriati per accedere e modificare i dati Ateco.

Interfaccia Utente
------------------
- Viste personalizzate in `views/atecoit_category.xml` e `views/res_partner.xml`
- Asset frontend in `atecoit/static/src/`
- Integrazione con l'interfaccia di gestione contatti di Odoo

Risoluzione Problemi
--------------------
- Controllare i log di Odoo per eventuali errori durante l'aggiornamento dei codici Ateco.
- Verificare la connessione alla repository ufficiale dei codici Ateco.

Sviluppi Futuri
---------------
- Implementazione di un'interfaccia per l'aggiornamento manuale dei codici Ateco.
- Miglioramento della gestione degli errori con notifiche utente più dettagliate.
- Possibile integrazione con altri sistemi di classificazione economica.

Supporto e Contributi
---------------------
Per supporto, segnalazione bug o contributi, contattare:
- Autore: FL1 sro
- Sito Web: https://fl1.cz

Licenza
-------
Questo modulo è distribuito sotto licenza LGPL-3. Per i dettagli completi, consultare il file LICENSE incluso nel modulo.