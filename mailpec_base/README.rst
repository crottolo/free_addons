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

1. Valorizzare il campo **Filtro mittente** (``from_filter``) con l'indirizzo della casella PEC autenticata, e **nient'altro**: una sola voce, completa di chiocciola.
2. Spuntare l'opzione **Casella PEC** (``is_pec``).

Sono i due soli campi. L'indirizzo PEC **si legge da** ``from_filter``: non esiste un campo dedicato, perché sarebbe un duplicato di un valore che deve comunque stare lì, e due campi separati possono divergere — è così che un messaggio finisce per uscire da una casella certificata diversa da quella dichiarata. La regola di lettura è la stessa del core (``_get_test_email_from``): la prima voce che contiene una chiocciola.

Un vincolo rifiuta le forme ambigue quando ``is_pec`` è attivo: campo vuoto, dominio nudo, o più indirizzi. Con più voci non si saprebbe quale casella autentica.

Una casella PEC = un server. Con più identità PEC (es. ``ctr@``, ``cqs@``, ``legale@``) serve un ``ir.mail_server`` per ciascuna: la selezione automatica confronta il mittente con l'indirizzo di ciascun server.

Su un server PEC il modulo allinea alla casella tutte e tre le identità del messaggio in uscita: **envelope sender**, **Return-Path** e **Reply-To**.

Il ``Reply-To`` va forzato perché in modalità ``comment`` quello del template viene scartato: ``message_post`` lo ricalcola con ``_notify_get_reply_to`` (``mail_thread.py`` L2271-2272) e produce il catchall dell'alias domain. Su una PEC significherebbe far tornare una risposta **certificata** su una casella ordinaria, perdendone il valore legale. Le risposte rientrano invece nella casella che il modulo stesso scarica, e l'aggancio alla pratica si recupera da ``origin_model``.

I tre valori sono scritti **sul record alla creazione**: ``mail_server_id``, ``reply_to`` e il ``Return-Path`` dentro ``headers``. Correggere soltanto all'invio non basterebbe: se lo SMTP è irraggiungibile il messaggio resta in coda con i valori del core, e a ogni ritentativo la correttezza dipenderebbe da quale server viene risolto in quel momento. Nascendo corretto, il record è anche ispezionabile: ciò che si legge su ``mail.mail`` è ciò che partirà.

Il riallineamento all'invio resta come ultima difesa, per i messaggi entrati in coda **prima** di questa versione. Su quei record i campi memorizzati mostrano ancora il catchall e il bounce dell'alias domain: sono vecchi, non un difetto in corso.

Vincoli operativi critici (da rispettare rigorosamente):
--------------------------------------------------------
* **Perché il from_filter è obbligatorio**: lasciarlo vuoto **falsificherebbe il mittente**. Il server verrebbe raggiunto solo al passo 3 di ``_find_mail_server`` (``ir_mail_server.py`` L833-835), che restituisce ``notifications_email`` al posto del mittente; più a valle ``_prepare_email_message`` (L692-694) riscrive di conseguenza l'header ``From``. Misurato su traffico reale: con ``from_filter`` vuoto l'header diventava ``consulenzaffari <notifications@progettorimborso.it>``, che il gestore rifiuta. Con ``from_filter`` valorizzato resta ``consulenzaffari@pec.it``. In entrambi i casi l'envelope è corretto: **guardare il solo envelope non basta a validare la configurazione**. Dalla v18.0.1.11.0 un vincolo impedisce la configurazione sbagliata.

  *(Nota: fino alla v18.0.1.7.0 questo README prescriveva l'esatto contrario, cioè di lasciare il campo vuoto. L'indicazione era sbagliata.)*
* **Mittente del Mail Template**: Impostare il campo ``From`` di qualsiasi ``mail.template`` utilizzato per l'invio PEC esattamente all'indirizzo PEC configurato. Se il mittente dichiarato non coincide con la casella PEC autenticata, il gestore PEC rifiuterà il messaggio senza che Odoo rilevi alcun errore.
* **Il campo ``mail_server_id`` sul template non è più obbligatorio**: dalla v18.0.1.8.0 il server PEC viene individuato dal mittente. Valorizzarlo resta comunque la scelta più esplicita.

Configurazione Ricezione
========================
Per ricevere non serve alcun server in uscita: ``ir.mail_server`` non interviene nella ricezione. È sufficiente un ``fetchmail.server`` sulla casella PEC.

Sul server di posta in ingresso (IMAP/POP) è **obbligatorio** impostare:

* **Keep Attachments** (``attach = True``): se disattivato, il core di Odoo rimuove in silenzio ``daticert.xml`` e ``postacert.eml``, facendo perdere sia la certificazione strutturata sia il corpo del messaggio umano.
* **Conserva busta firmata** (``original = True``): conserva il messaggio originale firmato S/MIME, necessario al valore legale della ricevuta.
* **Casella PEC** (``is_pec``, campo aggiunto da questo modulo): vedere il criterio 2 qui sotto. Facoltativo, ma raccomandato su una casella dedicata.
* Lasciare **vuoto** il campo "Crea un nuovo record" (``object_id``): se valorizzato, la posta della casella che non viene intercettata come PEC genera record di quel modello.

Criteri di instradamento
------------------------
Un messaggio in ingresso finisce su ``mailpec.mail`` se soddisfa **almeno uno** di tre criteri, valutati in OR. Nessuno è sufficiente da solo, ed è il motivo per cui coesistono.

1. **Header PEC** — presenza di ``X-Ricevuta`` oppure ``X-Trasporto``. L'Allegato tecnico al DM 2 novembre 2005 li prescrive ciascuno per la propria categoria (``X-Trasporto`` sulle buste, ``X-Ricevuta`` su ricevute e avvisi), quindi il criterio vale **per costruzione con qualunque gestore**, anche mai incontrato, e su qualunque canale di ingresso. Non copre la posta di servizio del gestore, che PEC non è.
2. **Casella dichiarata PEC** — flag ``is_pec`` sul ``fetchmail.server``. Instrada **tutto** ciò che arriva da quella casella, comprese le comunicazioni di servizio del gestore (avvisi di quota, rinnovi), che altrimenti uscirebbero verso il gateway ordinario. Vale solo sul percorso ``fetch_mail``, perché dipende da una chiave di contesto: per questo è un ramo in OR e non una condizione.
3. **Mittente** — il parametro di sistema ``mailpec_base.pec_senders``, valore predefinito ``posta-certificata@``. Voce **unica e senza dominio**: il confronto è per sottostringa, quindi cattura ogni gestore senza elencarne nessuno. Accetta più voci separate da virgola qualora un gestore deviasse dallo standard.

Portata normativa del criterio 3
--------------------------------
Il criterio sul mittente **non basta da solo**, e va compreso il perché prima di semplificarlo.

L'Allegato tecnico al DM 2 novembre 2005, par. 6.3.4, prescrive alla lettera il ``From`` della **busta di trasporto**::

    From: "Per conto di: [mittente originale]" <posta-certificata@[dominio_di_posta]>

Per le **ricevute** nessuna prescrizione equivalente risulta dalle regole tecniche. Sul traffico reale il criterio regge (119 ricevute su 119), ma il campione è concentrato: due gestori su una ventina accreditati AgID coprono il 96% dei messaggi. Da qui l'aggiunta dei criteri 1 e 2.

Il confronto avviene sull'header ``From`` e **non** sull'envelope sender: la stessa norma impone che i dati di instradamento restino quelli del messaggio originale, e infatti ``message_parse`` valorizza ``email_from`` da ``From`` (``mail/models/mail_thread.py`` L1749). Sono due campi diversi e non vanno confusi.

Visibilità dell'applicazione
----------------------------
Il menu **PEC** è riservato al gruppo **Utente PEC** (``mailpec_base.group_mailpec_user``), assegnabile da *Impostazioni → Utenti* nella categoria *PEC*. È una restrizione di sola presentazione: ``ir.model.access.csv`` resta su ``base.group_user``, quindi i record restano raggiungibili per altra via (ricerca globale, azione richiamata a mano, export). Chi ha bisogno di riservatezza sui contenuti deve intervenire sulle ACL, non su questo gruppo.

Limiti Noti e Comportamenti Accettati
=====================================
* **Nessuna verifica della firma S/MIME**: Odoo conserva la busta firmata originale ma non effettua alcuna validazione crittografica della firma S/MIME.
* **Valorizzazione di company_id**: Il campo ``company_id`` viene valorizzato con la company dell'utente catch-all (poiché ``message_new`` viene eseguito in ``sudo()`` tramite ``with_user(related_user)``). La derivazione della company dall'header ``To:`` è fuori scope.
* **Posta di servizio del gestore**: le comunicazioni che il gestore invia dalla propria casella ordinaria (avvisi di quota, scadenze, rinnovi) non sono PEC, non portano header PEC e non provengono da ``posta-certificata@``. Senza il flag ``is_pec`` sul ``fetchmail.server`` escono verso il gateway ordinario di Odoo e non compaiono nell'elenco. Con il flag attivo atterrano su ``mailpec.mail`` con ``pec_kind`` non valorizzato, e si trovano con il filtro «Non classificate».
* **Ricorsione in postacert.eml**: Il core di Odoo, tramite ``message.walk()``, analizza ricorsivamente il messaggio originale allegato alla ricevuta. Di conseguenza, il corpo della ricevuta conterrà in coda anche il testo del messaggio originale, e gli allegati originali compariranno duplicati (sia all'interno di ``postacert.eml`` sia estratti singolarmente). Questo comportamento è una conseguenza del funzionamento di ``message_parse`` sul modello astratto ``mail.thread`` prima del routing, e non è modificabile all'interno di questo modulo.
* **Correlazione al messaggio inviato**: la ricevuta risale al messaggio spedito confrontando ``X-Riferimento-Message-ID`` con ``mail.message.message_id``. Riesce solo se il messaggio è partito **da Odoo**: le PEC spedite dalla webmail del gestore atterrano correttamente ma restano senza origine, e si isolano con il filtro «Senza messaggio di origine». Nessun errore in caso di mancata corrispondenza: la ricevuta ha valore legale e atterra comunque.
* **Le ricevute tornano alla casella che ha spedito**: se si invia da una casella e se ne monitora un'altra, le ricevute dei propri invii non compaiono mai. Per tracciare il recapito, l'indirizzo in uscita e quello scaricato devono coincidere.

Dettagli Tecnici Interni
========================
* Il modello ``mailpec.mail`` dichiara ``_primary_email = "email_from"`` per consentire al core di Odoo di popolare automaticamente il mittente del messaggio in ingresso.

Evidenze dal Primo Fetch Reale
==============================
L'analisi di un primo lotto di 156 messaggi reali in produzione ha evidenziato alcuni comportamenti e scelte di design che è opportuno documentare per evitare fraintendimenti durante la lettura del codice.

Disallineamento tra pec_kind e pec_receipt_type (Caso Annidato)
---------------------------------------------------------------
È possibile che un record presenti ``pec_kind = 'non_certificata'`` e contemporaneamente ``pec_receipt_type = 'posta-certificata'``. Questo scenario non costituisce un'anomalia del codice, bensì rispecchia la struttura del messaggio ricevuto.
Si verifica quando un messaggio PEC, inviato originariamente, ritorna al mittente attraverso il canale di errore (ad esempio a causa di un bounce). In questo caso:

* L'involucro esterno (envelope) è un'anomalia di trasporto (identificata dall'header ``X-Trasporto: errore``, che determina il valore di ``pec_kind``).
* Il file ``daticert.xml`` contenuto all'interno descrive invece il messaggio PEC originale (determinando il valore di ``pec_receipt_type``).

Un esempio tipico è un messaggio con oggetto del tipo ``ANOMALIA MESSAGGIO: POSTA CERTIFICATA: R: Re...`` e mittente in formato bounce (es. ``benefit-return-5-bo=pec...``). I due campi descrivono quindi livelli diversi dello stesso messaggio ed è corretto che possano differire.

Asimmetria tra pec_receipt_type (Char) e pec_kind (Selection)
-------------------------------------------------------------
La differenza di tipologia tra i due campi è intenzionale:

* ``pec_receipt_type`` rappresenta una tassonomia esterna definita dai vari gestori PEC. Poiché non esiste uno standard univoco e documentato per tutti i possibili valori (analisi indipendenti hanno mostrato discrepanze, confermandone solo 4 nei campioni analizzati), il campo è mantenuto come ``Char`` per evitare la perdita di informazioni non censite.
* ``pec_kind`` è invece una classificazione interna del modulo, derivata direttamente dall'elaborazione degli header ``X-Ricevuta`` e ``X-Trasporto``, ed è pertanto gestita come ``Selection``.

La scelta è confermata anche dalla fonte normativa: nell'Allegato tecnico al DM 2 novembre 2005 **non esiste una tabella di enumerazione esaustiva** dei valori ammessi per ``X-Ricevuta``. Una ``Selection`` chiusa dichiarerebbe quindi una completezza che nemmeno la specifica possiede. Per ``X-Trasporto`` i valori verificati sono invece solo due, ``posta-certificata`` ed ``errore``, e infatti su quell'header si basa ``pec_kind``, che è una ``Selection``.

La validità di questa scelta è stata confermata dal riscontro, nel primo fetch in produzione, di due ricevute di tipo ``errore-consegna`` con attributo ``errore="virus"`` (causate da ``5.5.1, Aruba Pec S.p.A., presenza di un virus nel messaggio``). Nessuno di questi valori era presente nei campioni di test iniziali. Se ``pec_receipt_type`` fosse stato una ``Selection`` chiusa, queste ricevute (che segnalano la presenza di un virus) sarebbero state scartate o registrate con un campo vuoto, senza alcuna evidenza nei log. La regola generale applicata è di enumerare tramite ``Selection`` solo i dati sotto il diretto controllo del modulo.

Comportamento del Fetchmail in Ricezione
----------------------------------------
Il comportamento del modulo durante il fetch, ereditato dal core di Odoo (``mail/models/fetchmail.py``), prevede che:

* Vengano scaricati esclusivamente i messaggi non letti (tramite la ricerca IMAP ``(UNSEEN)``).
* I messaggi elaborati vengano marcati come letti sul server di posta (tramite il flag ``\Seen``).
* Non venga effettuata alcuna cancellazione dei messaggi (nessun flag ``\Deleted`` o comando ``expunge``).

Di conseguenza, i messaggi già letti prima del collegamento della casella a Odoo rimarranno invisibili al sistema. Inoltre, l'attivazione del server su una casella con un elevato numero di messaggi non letti comporterà la marcatura massiva di tutti i messaggi come letti in un unico passaggio. Si raccomanda di valutare lo stato della casella prima di abilitare il servizio, specialmente se lo stato "non letto" viene utilizzato come coda di lavoro esterna.

Distribuzione dei Messaggi Osservata
------------------------------------
Di seguito si riporta la distribuzione reale dei messaggi rilevata su un campione di 156 messaggi ricevuti in produzione:

.. list-table::
   :widths: 70 30
   :header-rows: 1

   * - Tipologia / Ricevuta
     - Quantità
   * - accettazione
     - 93
   * - posta-certificata
     - 47
   * - avvenuta-consegna
     - 11
   * - errore-consegna
     - 2
   * - non certificate
     - 2
   * - anomalia con PEC incapsulata
     - 1

Nota: in tutti i 50 casi di messaggi incapsulati (ricevute e anomalie contenenti ``postacert.eml``), il mittente reale è stato estratto correttamente dal messaggio originale.
