""""""

# Standard library modules.
import getpass
import imaplib
from email.parser import BytesParser
from email.policy import default

# Third party modules.
from django.db import IntegrityError
from django.core.management.base import BaseCommand, CommandError
from loguru import logger
import tqdm

# Local modules.
from email_backup.models import Email, Attachment, Message

# Globals and constants variables.


def _convert_addresses(addresses):
    models = []
    for address in addresses:
        model = Email(address=address.addr_spec, name=address.display_name)

        try:
            model.save()
        except IntegrityError:
            model = Email.objects.get(address=address.addr_spec)

        models.append(model)
    return models


def _convert_attachments(message):
    models = []
    for part in message.iter_attachments():
        filename = part.get_filename()
        if not filename:
            continue

        model = Attachment(filename=filename, size=len(part.get_content()))
        model.save()
        models.append(model)
    return models


class Command(BaseCommand):
    help = "Fetch email from imap"

    def add_arguments(self, parser):
        parser.add_argument("imaphost", type=str)
        parser.add_argument("imapuser", type=str)

    def handle(self, *args, **options):
        host = options["imaphost"]
        user = options["imapuser"]
        password = getpass.getpass(f"Password for {user}@{host}: ")

        parser = BytesParser(policy=default)

        with imaplib.IMAP4(host) as imap:
            status, message = imap.login(user, password)
            if status != "OK":
                raise CommandError("Cannot login")
            logger.debug(message)

            status, _ = imap.select()
            if status != "OK":
                raise CommandError("Cannot select")

            status, data = imap.search(None, "ALL")
            if status != "OK":
                raise CommandError("Cannot search")

            message_numbers = data[0].split()
            logger.debug(f"Found {len(message_numbers)} messages")

            for message_number in tqdm.tqdm(message_numbers):
                status, data = imap.fetch(message_number, "(RFC822)")
                if status != "OK":
                    raise CommandError(f"Cannot fetch {message_number}")

                content = data[0][1]
                message = parser.parsebytes(content)

                try:
                    # Create models
                    senders = _convert_addresses(message["From"].addresses)
                    recipients = _convert_addresses(message["To"].addresses)
                    subject = message["Subject"]
                    date = message["Date"].datetime
                    attachments = _convert_attachments(message)

                    model = Message(
                        sender=senders[0] if senders else None,
                        subject=subject,
                        date=date,
                        content=content,
                    )
                    model.save()

                    model.recipients.add(*recipients)
                    model.attachments.add(*attachments)

                    model.save()
                except:
                    logger.exception(f"Error when saving {message_number}")
