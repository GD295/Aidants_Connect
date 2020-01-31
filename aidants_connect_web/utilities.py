import io
import base64
import qrcode
import qrcode.image.svg
from datetime import date

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password


def generate_mandat_print_hash(aidant, usager, demarches, expiration_date):
    demarches.sort()
    mandat_print_data = {
        "aidant_id": aidant.id,
        "creation_date": date.today().isoformat(),
        "demarches_list": ",".join(demarches),
        "expiration_date": expiration_date.date().isoformat(),
        "organisation_id": aidant.organisation.id,
        "template_version": settings.MANDAT_TEMPLATE_VERSION,
        "usager_sub": usager.sub,
    }
    sorted_mandat_print_data = dict(sorted(mandat_print_data.items()))
    mandat_print_string = ",".join(
        str(x) for x in list(sorted_mandat_print_data.values())
    )
    return make_password(mandat_print_string)


def validate_mandat_print_hash(mandat_print_string, mandat_print_hash):
    return check_password(mandat_print_string, mandat_print_hash)


def generate_qrcode_base64(string: str, image_type: str = "png"):
    stream = io.BytesIO()
    if image_type == "png":
        img = qrcode.make(string)
        img.save(stream, "PNG")
    elif image_type == "svg":
        img = qrcode.make(string, image_factory=qrcode.image.svg.SvgImage)
        img.save(stream, "SVG")
    journal_print_mandat_qrcode = base64.b64encode(stream.getvalue())
    return journal_print_mandat_qrcode.decode("utf-8")
