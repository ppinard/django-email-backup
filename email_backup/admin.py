""""""

# Standard library modules.
import zipfile
from io import BytesIO

# Third party modules.
import humanize
from django.contrib import admin
from django.http import HttpResponse

# Local modules.
from .models import Email, Attachment, Message

# Globals and constants variables.


def attachment_count(obj):
    return obj.attachments.count()


attachment_count.short_description = "Attachments"


def human_filesize(obj):
    return humanize.naturalsize(obj.size)


human_filesize.short_description = "Filesize"


def download_message(modeladmin, request, queryset):
    count = queryset.count()

    if count == 1:
        obj = queryset.first()
        response = HttpResponse(obj.content, content_type="message/rfc822")
        response["Content-Disposition"] = f"inline; filename=message-{obj.pk}.eml"
        return response

    else:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as zfp:
            for obj in queryset:
                zfp.writestr(f"message-{obj.pk}.eml", obj.content)

        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f"inline; filename=messages.zip"
        return response


download_message.short_description = "Download (eml)"


class EmailAdmin(admin.ModelAdmin):
    list_display = ("address", "name")
    search_fields = ("address", "name")


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("filename", human_filesize)


class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "date", attachment_count)
    list_filter = ("date",)
    search_fields = ("sender__address", "subject")
    ordering = ("date",)
    actions = (download_message,)


admin.site.register(Email, EmailAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Message, MessageAdmin)
