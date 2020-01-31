import io
import qrcode
import hashlib
import qrcode.image.svg
from pathlib import Path
from datetime import date

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password


def generate_file_sha256_hash(filename):
    base_path = Path(__file__).resolve().parent
    file_path = (base_path / filename).resolve()
    with open(file_path, "rb") as f:
        bytes = f.read()  # read entire file as bytes
        file_readable_hash = hashlib.sha256(bytes).hexdigest()
        return file_readable_hash


def generate_mandat_print_hash(aidant, usager, demarches, expiration_date):
    demarches.sort()
    mandat_print_data = {
        "aidant_id": aidant.id,
        "creation_date": date.today().isoformat(),
        "demarches_list": ",".join(demarches),
        "expiration_date": expiration_date.date().isoformat(),
        "organisation_id": aidant.organisation.id,
        "template_hash": generate_file_sha256_hash(settings.MANDAT_TEMPLATE_PATH),
        "usager_sub": usager.sub,
    }
    sorted_mandat_print_data = dict(sorted(mandat_print_data.items()))
    mandat_print_string = ",".join(
        str(x) for x in list(sorted_mandat_print_data.values())
    )
    return make_password(mandat_print_string, salt=settings.MANDAT_PRINT_SALT)


def validate_mandat_print_hash(mandat_print_string, mandat_print_hash):
    return check_password(mandat_print_string, mandat_print_hash)


def generate_qrcode_png(string: str):
    stream = io.BytesIO()
    img = qrcode.make(string)
    img.save(stream, "PNG")
    return stream.getvalue()
