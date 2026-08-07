=================================
PEC - Invio e Ricezione (mailpec)
=================================

Questo modulo gestisce l'integrazione delle caselle PEC (Posta Elettronica Certificata) in Odoo 18, occupandosi del corretto invio dei messaggi con envelope sender allineato e dell'atterraggio delle ricevute PEC in ingresso.

Dipendenze
==========
Il modulo dipende esclusivamente dal modulo nativo ``mail`` di Odoo. Non dipende da ``l10n_it_edi`` né da ``l10n_it_edi_pec``, e non sostituisce alcuna regola di automazione esistente.

Configurazione Invio
====================
Per configurare l'invio tramite una casella PEC, accedere alla configurazione dei server di posta in uscita (``ir.mail_server``) e configurare come segue:

1. Spuntare l'opzione **Casella PEC** (campo ``is_pec``). Questo esclude il server dalla selezione automatica per le email ordinarie e forza l'envelope sender all'indirizzo PEC.
2. Valorizzare il campo **Indirizzo PEC** (campo ``pec_email_from``) con l'indirizzo email della casella PEC autenticata sul server.

Vincoli operativi critici (da rispettare rigorosamente):
--------------------------------------------------------
* **Filtro mittente (from_filter) vuoto**: Lasciare il campo ``from_filter`` completamente **VUOTO** sui server PEC. Se valorizzato, il server PEC potrebbe non essere selezionato correttamente o causare il rifiuto dei messaggi.
* **Mittente del Mail Template**: Impostare il campo ``From`` di qualsiasi ``mail.template`` utilizzato per l'invio PEC esattamente all'indirizzo PEC configurato. Se il mittente dichiarato non coincide con la casella PEC autenticata, il gestore PEC rifiuterà il messaggio senza che Odoo rilevi alcun errore.

Configurazione Ricezione
========================
Per la ricezione e l'instradamento delle ricevute PEC, configurare i seguenti parametri:

1. **Allowlist dei mittenti PEC**: Il parametro di sistema ``mailpec_base.pec_senders`` contiene l'elenco dei mittenti dei gestori PEC autorizzati, separati da virgola (valore predefinito: Aruba, Telecom Post, Poste Italiane). Qualsiasi email in ingresso il cui mittente combacia con questa lista viene dirottata sul modello ``mailpec.mail``.
2. **Configurazione del server di ricezione (fetchmail.server)**: Sul server di posta in ingresso (IMAP/POP), è **obbligatorio** impostare le seguenti opzioni:
   * **Keep Attachments** (``attach = True``): Se disattivato, il file ``daticert.xml`` (che contiene i dati strutturati della ricevuta) viene rimosso in silenzio dal core di Odoo, impedendo la conservazione della ricevuta strutturata.
   * **Conserva busta firmata** (``original = True``): Conserva il messaggio originale firmato S/MIME, necessario per garantire il valore legale della ricevuta PEC.

Limiti Noti e Comportamenti Accettati
=====================================
* **Nessuna verifica della firma S/MIME**: Odoo conserva la busta firmata originale ma non effettua alcuna validazione crittografica della firma S/MIME.
* **Valorizzazione di company_id**: Il campo ``company_id`` viene valorizzato con la company dell'utente catch-all (poiché ``message_new`` viene eseguito in ``sudo()`` tramite ``with_user(related_user)``). La derivazione della company dall'header ``To:`` è fuori scope.
* **Intercettazione limitata alle sole ricevute**: L'allowlist basata sul mittente intercetta esclusivamente le ricevute PEC (che provengono dai server dei gestori PEC). I messaggi PEC ordinari in ingresso (il cui mittente reale è nell'header ``From``) non vengono dirottati su ``mailpec.mail`` ma seguono il flusso standard.
* **Ricorsione in postacert.eml**: Il core di Odoo, tramite ``message.walk()``, analizza ricorsivamente il messaggio originale allegato alla ricevuta. Di conseguenza, il corpo della ricevuta conterrà in coda anche il testo del messaggio originale, e gli allegati originali compariranno duplicati (sia all'interno di ``postacert.eml`` sia estratti singolarmente). Questo comportamento è una conseguenza del funzionamento di ``message_parse`` sul modello astratto ``mail.thread`` prima del routing, e non è modificabile all'interno di questo modulo.
* **Nessun parsing o correlazione automatica**: Il parsing del file ``daticert.xml`` e la correlazione automatica della ricevuta al messaggio inviato non sono implementati, in quanto richiedono campioni reali di ricevute PEC non ancora disponibili. Le ricevute vengono semplicemente archiviate intatte per preservarne il valore legale.

Dettagli Tecnici Interni
========================
* Il modello ``mailpec.mail`` dichiara ``_primary_email = "email_from"`` per consentire al core di Odoo di popolare automaticamente il mittente del messaggio in ingresso.
