import ast

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.base.tests.common import MockSmtplibCase

ALIAS_DOMAIN = "test-mailpec.example.com"
BOUNCE_ADDRESS = f"bounce@{ALIAS_DOMAIN}"
CATCHALL_ADDRESS = f"catchall@{ALIAS_DOMAIN}"
EMAIL_FROM = f"mittente@{ALIAS_DOMAIN}"
EMAIL_TO = "destinatario@example.com"
PEC_ADDRESS = "azienda@pec-mailpec.example.com"


@tagged("post_install", "-at_install")
class TestSend(TransactionCase, MockSmtplibCase):
    """Verifica l'envelope sender SMTP, NON l'header Return-Path.

    L'header viene scritto comunque da ``_prepare_outgoing_list``, quindi
    asserire su di esso non prova nulla. Cio' che il gestore PEC controlla e'
    il MAIL FROM di busta, calcolato in ``_prepare_email_message``
    (base/models/ir_mail_server.py L651 e L699) dove il context
    ``domain_bounce_address`` ha la precedenza sull'header.
    In test mode il core cortocircuita l'invio (connect() torna None,
    ir_mail_server.py L397-399 e L762-764): ``mock_smtplib_connection``
    ripristina il percorso reale e cattura lo ``smtp_from`` passato a
    ``send_message``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alias_domain = cls.env["mail.alias.domain"].create(
            {
                "name": ALIAS_DOMAIN,
                "bounce_alias": "bounce",
                "catchall_alias": "catchall",
                "default_from": "notifications",
            },
        )
        server_values = {"smtp_host": "smtp_host", "smtp_encryption": "none"}
        # sequence 1 = PRIMO dell'elenco, cioe' il ripiego del passo 4 del core
        # quando nessun from_filter combacia (ir_mail_server.py L837-842).
        # Non e' un valore arbitrario: senza, il test (c) non prova nulla.
        cls.pec_server = cls.env["ir.mail_server"].create(
            {
                "name": "PEC",
                "sequence": 1,
                "from_filter": PEC_ADDRESS,
                "is_pec": True,
                **server_values,
            },
        )
        cls.std_server = cls.env["ir.mail_server"].create(
            {
                "name": "Ordinario",
                "sequence": 3,
                "from_filter": ALIAS_DOMAIN,
                "is_pec": False,
                **server_values,
            },
        )

    def _create_mail(self, server):
        return self.env["mail.mail"].create(
            {
                "email_from": EMAIL_FROM,
                "email_to": EMAIL_TO,
                "subject": "test envelope",
                "body_html": "<p>test</p>",
                "mail_server_id": server.id,
                # record_alias_domain_id attiva il context domain_bounce_address
                # (mail_mail.py L738-744), la ragione per cui non basta l'header.
                "record_alias_domain_id": self.alias_domain.id,
            },
        )

    def _send_and_capture(self, mail):
        with self.mock_smtplib_connection():
            mail.send(raise_exception=True)
        self.assertEqual(len(self.emails), 1, "deve partire una sola email")
        return self.emails[0]

    def test_record_is_born_correct(self):
        """(z) Il record nasce corretto: il ritentativo non ricalcola nulla.

        E' la differenza fra correggere all'invio e correggere alla create. Se
        lo SMTP e' giu', la mail resta in coda: con i soli valori del core
        resterebbe con il catchall e il bounce dell'alias domain, e a ogni
        ritentativo la correttezza dipenderebbe da quale server viene risolto.

        Il record e' creato SENZA indicare il server: e' il mittente a
        determinarlo, ed e' il caso dei template che non valorizzano
        ``mail_server_id``.
        """
        mail = self.env["mail.mail"].create(
            {
                "email_from": PEC_ADDRESS,
                "email_to": EMAIL_TO,
                "reply_to": CATCHALL_ADDRESS,
                "headers": repr({"X-Odoo-Objects": "res.partner-1"}),
                "record_alias_domain_id": self.alias_domain.id,
            },
        )

        self.assertEqual(
            mail.mail_server_id,
            self.pec_server,
            "server dedotto dal mittente",
        )
        self.assertEqual(mail.reply_to, PEC_ADDRESS)
        headers = ast.literal_eval(mail.headers)
        self.assertEqual(headers["Return-Path"], PEC_ADDRESS)
        self.assertEqual(
            headers["X-Odoo-Objects"],
            "res.partner-1",
            "gli altri header non vanno sovrascritti in blocco",
        )

    def test_record_of_ordinary_mail_untouched(self):
        """(z-bis) Su un mittente non PEC la create non tocca nulla.

        Contro-prova di (z): senza, (z) passerebbe anche se il modulo
        riscrivesse server e Reply-To di TUTTA la posta.
        """
        mail = self.env["mail.mail"].create(
            {
                "email_from": EMAIL_FROM,
                "email_to": EMAIL_TO,
                "reply_to": CATCHALL_ADDRESS,
                "record_alias_domain_id": self.alias_domain.id,
            },
        )

        self.assertFalse(mail.mail_server_id, "nessun server imposto d'ufficio")
        self.assertEqual(mail.reply_to, CATCHALL_ADDRESS)
        self.assertFalse(mail.headers)

    def test_pec_envelope_sender(self):
        """(a) Server PEC: il MAIL FROM di busta e' l'indirizzo PEC."""
        mail = self._create_mail(self.pec_server)

        sent = self._send_and_capture(mail)

        self.assertEqual(
            sent["smtp_from"],
            PEC_ADDRESS,
            "l'envelope sender deve essere la casella PEC autenticata",
        )
        self.assertNotEqual(sent["smtp_from"], BOUNCE_ADDRESS)
        # L'header From resta quello applicativo: se coincidesse con
        # l'envelope l'asserzione precedente non discriminerebbe.
        self.assertEqual(sent["msg_from"], EMAIL_FROM)

    def test_pec_reply_to(self):
        """(a-bis) Server PEC: il Reply-To e' la casella PEC.

        Il valore memorizzato sul record e' il catchall dell'alias domain,
        perche' in modalita' ``comment`` ``message_post`` lo ricalcola con
        ``_notify_get_reply_to`` scartando quello del template. Sulla PEC
        significherebbe far tornare una risposta CERTIFICATA su una casella
        ordinaria: recapito senza valore legale.

        L'asserzione sul valore memorizzato e' la meta' che conta: prova che il
        test non sta leggendo un campo gia' corretto in partenza.
        """
        mail = self._create_mail(self.pec_server)
        mail.reply_to = CATCHALL_ADDRESS
        self.assertEqual(mail.reply_to, CATCHALL_ADDRESS, "punto di partenza")

        sent = self._send_and_capture(mail)

        self.assertIn(f"Reply-To: {PEC_ADDRESS}", sent["message"])
        self.assertNotIn(CATCHALL_ADDRESS, sent["message"])

    def test_standard_reply_to_unchanged(self):
        """(a-ter) Server non PEC: il Reply-To resta quello del core.

        Senza questa contro-prova (a-bis) passerebbe anche se il modulo
        riscrivesse il Reply-To di TUTTA la posta, PEC e non.
        """
        mail = self._create_mail(self.std_server)
        mail.reply_to = CATCHALL_ADDRESS

        sent = self._send_and_capture(mail)

        self.assertIn(f"Reply-To: {CATCHALL_ADDRESS}", sent["message"])
        self.assertNotIn(PEC_ADDRESS, sent["message"])

    def test_standard_envelope_sender_unchanged(self):
        """(b) Server non PEC: comportamento core, envelope = bounce address."""
        mail = self._create_mail(self.std_server)

        sent = self._send_and_capture(mail)

        self.assertEqual(sent["smtp_from"], BOUNCE_ADDRESS)
        self.assertNotEqual(sent["smtp_from"], PEC_ADDRESS)

    def test_find_mail_server_excludes_pec_for_ordinary_mail(self):
        """(c) Sulla posta ordinaria non viene mai scelto un server PEC.

        Mirror di mail_mail.py L574-585: il recordset arriva posizionale e
        gia' valorizzato.

        Il server PEC e' il primo dell'elenco e nessun ``from_filter`` combacia
        con questo mittente: senza l'esclusione, il passo 4 del core
        (ir_mail_server.py L837-842) ripiegherebbe proprio su di lui.
        """
        mail_servers = self.pec_server + self.std_server

        server, _email_from = self.env["ir.mail_server"]._find_mail_server(
            EMAIL_FROM,
            mail_servers,
        )

        self.assertFalse(server.is_pec, "selezionato un server PEC")
        self.assertEqual(server, self.std_server)

    def test_find_mail_server_pec_not_used_as_last_resort(self):
        """(c-bis) Anche restando SOLO la PEC, la posta ordinaria non ci passa.

        Isola il ripiego del passo 4: unico candidato il server PEC, mittente
        che non e' la sua casella. L'esclusione lo toglie di mezzo e il core
        finisce sulla configurazione da riga di comando invece di spedire da una
        casella certificata.
        """
        server, _email_from = self.env["ir.mail_server"]._find_mail_server(
            EMAIL_FROM,
            self.pec_server,
        )

        self.assertFalse(server, "nessun server: meglio di una PEC a sproposito")

    def test_find_mail_server_selects_pec_for_its_own_sender(self):
        """(d) Sul proprio mittente il server PEC viene scelto DA SOLO.

        E' cio' che rende inoffensivo dimenticare ``mail_server_id`` su un
        template: senza questo ramo il messaggio uscirebbe da un server
        qualunque con envelope sbagliato, e il gestore lo rifiuterebbe senza
        che Odoo registri un errore.

        L'asserzione sul mittente RESTITUITO e' la meta' che conta: finisce in
        ``smtp_from`` (mail_mail.py L578-590), e i passi 3 e 4 del core lo
        sostituirebbero con l'indirizzo di notifica.
        """
        mail_servers = self.pec_server + self.std_server

        server, email_from = self.env["ir.mail_server"]._find_mail_server(
            PEC_ADDRESS,
            mail_servers,
        )

        self.assertEqual(server, self.pec_server)
        self.assertEqual(email_from, PEC_ADDRESS, "il mittente non va sostituito")

    def test_pec_requires_a_single_full_address_in_from_filter(self):
        """(e) Su una casella PEC il filtro mittente e' UN SOLO indirizzo.

        Sostituisce il vecchio test che documentava la trappola del
        ``from_filter`` vuoto: quella configurazione ora non e' piu'
        rappresentabile, perche' il vincolo la rifiuta. La trappola era che il
        core ripiegasse sul passo 3 restituendo l'indirizzo di notifica al posto
        del mittente, e da li' riscrivesse l'header From.

        Tre forme respinte, tutte viste come possibili in configurazione:
        vuoto, dominio nudo, e piu' indirizzi.
        """
        server_values = {"smtp_host": "smtp_host", "smtp_encryption": "none"}
        for label, from_filter in (
            ("vuoto", False),
            ("dominio nudo", "pec-mailpec.example.com"),
            ("due indirizzi", f"{PEC_ADDRESS},altra@pec-mailpec.example.com"),
        ):
            with self.subTest(from_filter=label), self.assertRaises(ValidationError):
                self.env["ir.mail_server"].create(
                    {
                        "name": f"PEC {label}",
                        "from_filter": from_filter,
                        "is_pec": True,
                        **server_values,
                    },
                )

    def test_pec_address_is_read_from_from_filter(self):
        """(e-bis) L'indirizzo PEC si legge da ``from_filter``, senza campo proprio.

        Un campo dedicato sarebbe un duplicato che puo' divergere: e' cosi' che
        un messaggio esce da una casella certificata diversa da quella
        dichiarata.
        """
        self.assertEqual(self.pec_server._mailpec_address(), PEC_ADDRESS)
        self.assertFalse(
            self.std_server._mailpec_address(),
            "un server non PEC non ha un indirizzo PEC da esporre",
        )
