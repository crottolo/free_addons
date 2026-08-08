"""``pec_email_from`` viene rimosso: il suo valore vive ora in ``from_filter``.

Non e' prudenza teorica. Su una delle installazioni reali un server PEC aveva
``pec_email_from`` valorizzato e ``from_filter`` VUOTO: senza questa copia il
modulo avrebbe smesso di riconoscere quella casella, e gli invii PEC sarebbero
degradati in silenzio.

La colonna NON sopravvive: alla rimozione del campo Odoo cancella il record
``ir.model.fields``, e il suo ``unlink`` esegue il ``DROP COLUMN``. Verificato
sull'installazione di sviluppo, dove dopo l'aggiornamento la colonna non esiste
piu'. Non c'e' quindi alcuna rete di sicurezza dietro questo script: se non
copia il valore qui, il valore e' perso.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        SELECT id, name, from_filter, pec_email_from
        FROM ir_mail_server
        WHERE is_pec IS TRUE
          AND coalesce(pec_email_from, '') <> ''
          AND coalesce(from_filter, '') NOT IN ('', pec_email_from)
    """)
    # Divergenze: from_filter e' l'autorevole (e' quello che il core usa per
    # non falsificare il mittente), quindi NON viene sovrascritto. Va segnalato
    # perche' significa che quel server era configurato in modo incoerente.
    for server_id, name, from_filter, pec_email_from in cr.fetchall():
        _logger.warning(
            "PEC: server %s (%s) aveva from_filter=%r e pec_email_from=%r "
            "discordanti. Tenuto from_filter; verificare quale sia la casella "
            "autenticata.",
            server_id,
            name,
            from_filter,
            pec_email_from,
        )

    cr.execute("""
        UPDATE ir_mail_server
        SET from_filter = pec_email_from
        WHERE is_pec IS TRUE
          AND coalesce(pec_email_from, '') <> ''
          AND coalesce(from_filter, '') = ''
    """)
    if cr.rowcount:
        _logger.info(
            "PEC: from_filter valorizzato da pec_email_from su %s server.",
            cr.rowcount,
        )
