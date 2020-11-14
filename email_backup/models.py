""""""

# Standard library modules.

# Third party modules.
from django.db import models

# Local modules.

# Globals and constants variables.


class Email(models.Model):
    address = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        if self.name:
            return f"{self.name} <{self.address}>"
        else:
            return self.address


class Attachment(models.Model):
    filename = models.CharField(max_length=255)
    size = models.PositiveIntegerField()

    def __str__(self):
        return self.filename


class Message(models.Model):
    sender = models.ForeignKey("Email", on_delete=models.CASCADE, null=True)
    recipients = models.ManyToManyField("Email", related_name="recipients")
    subject = models.CharField(max_length=1024, blank=True)
    date = models.DateTimeField()
    attachments = models.ManyToManyField("Attachment")
    content = models.BinaryField()

    def __str__(self):
        return self.subject
