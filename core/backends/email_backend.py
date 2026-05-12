import logging
import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.utils.functional import cached_property

logger = logging.getLogger('mardid')

class EmailBackend(SMTPBackend):
    @cached_property
    def ssl_context(self):
        logger.debug("Email Backend has been initialized")
        ssl_context = ssl.create_default_context()
        if self.ssl_certfile or self.ssl_keyfile:
            ssl_context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
        return ssl_context
