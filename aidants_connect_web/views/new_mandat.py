import logging
from datetime import date, timedelta

from django.db import IntegrityError
<<<<<<< HEAD
=======
from django.conf import settings
from django.utils import formats
from django.utils import timezone
from django.shortcuts import render, redirect
>>>>>>> 6a08181... Add new Journal entry for mandat_papier. Store template version
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone, formats

from aidants_connect_web.decorators import activity_required
from aidants_connect_web.forms import MandatForm, RecapMandatForm
from aidants_connect_web.models import Mandat, Connection
from aidants_connect_web.views.service import humanize_demarche_names
from aidants_connect_web.models import Mandat, Connection, Journal

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


@login_required
@activity_required
def new_mandat(request):
    aidant = request.user
    form = MandatForm()

    if request.method == "GET":
        return render(
            request,
            "aidants_connect_web/new_mandat/new_mandat.html",
            {"aidant": aidant, "form": form},
        )

    else:
        form = MandatForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            duree = 1 if data["duree"] == "short" else 365
            connection = Connection.objects.create(
                demarches=data["demarche"], duree=duree
            )
            request.session["connection"] = connection.pk
            return redirect("fc_authorize")
        else:
            return render(
                request,
                "aidants_connect_web/new_mandat/new_mandat.html",
                {"aidant": aidant, "form": form},
            )


@login_required
@activity_required
def new_mandat_recap(request):
    connection = Connection.objects.get(pk=request.session["connection"])
    aidant = request.user
    usager = connection.usager
    duree = "1 jour" if connection.duree == 1 else "1 an"
    demarches_description = [
        humanize_demarche_names(demarche) for demarche in connection.demarches
    ]

    if request.method == "GET":
        form = RecapMandatForm(aidant)
        return render(
            request,
            "aidants_connect_web/new_mandat/new_mandat_recap.html",
            {
                "aidant": aidant,
                "usager": usager,
                "demarches": demarches_description,
                "duree": duree,
                "form": form,
            },
        )

    else:
        form = RecapMandatForm(aidant=aidant, data=request.POST)
        if form.is_valid():
            mandat_expiration_date = timezone.now() + timedelta(days=connection.duree)

            try:
                # Add a Journal 'print_mandat' action
                Journal.objects.mandat_print(
                    aidant=aidant,
                    usager=usager,
                    demarches=connection.demarches,
                    expiration_date=mandat_expiration_date,
                )

                # The loop below creates one Mandat object per Démarche in the form
                for demarche in connection.demarches:
                    Mandat.objects.update_or_create(
                        aidant=aidant,
                        usager=usager,
                        demarche=demarche,
                        defaults={
                            "expiration_date": mandat_expiration_date,
                            "last_mandat_renewal_date": timezone.now(),
                            "last_mandat_renewal_token": connection.access_token,
                        },
                    )

            except (AttributeError, IntegrityError) as e:
                log.error("Error happened in Recap")
                log.error(e)
                messages.error(request, f"No Usager was given : {e}")
                return redirect("dashboard")

            return redirect("new_mandat_success")

        else:
            return render(
                request,
                "aidants_connect_web/new_mandat/new_mandat_recap.html",
                {
                    "aidant": aidant,
                    "usager": usager,
                    "demarche": demarches_description,
                    "duree": duree,
                    "form": form,
                    "error": form.errors,
                },
            )


@login_required
def new_mandat_success(request):
    connection = Connection.objects.get(pk=request.session["connection"])
    aidant = request.user
    usager = connection.usager

    return render(
        request,
        "aidants_connect_web/new_mandat/new_mandat_success.html",
        {"aidant": aidant, "usager": usager},
    )


@login_required
def mandat_preview(request, final=False):
    connection = Connection.objects.get(pk=request.session["connection"])
    aidant = request.user
    usager = connection.usager
    demarches = connection.demarches

    duree = "1 jour" if connection.duree == 1 else "1 an"

    if final:
        journal_print_mandat = aidant.get_journal_of_last_print_mandat()
        journal_print_mandat_qrcode_svg = journal_print_mandat.generate_mandat_qrcode(
            "svg"
        )

    return render(
        request,
        "aidants_connect_web/mandat_preview.html",
        {
            "usager": usager,
            "aidant": aidant,
            "date": formats.date_format(date.today(), "l j F Y"),
            "demarches": [humanize_demarche_names(demarche) for demarche in demarches],
            "duree": duree,
            "mandat_template_version": "layouts/mandat/mandat_template_"
            f"{settings.MANDAT_TEMPLATE_VERSION}.html",
            "journal_print_mandat": journal_print_mandat if final else None,
            "journal_print_mandat_qrcode_svg": journal_print_mandat_qrcode_svg
            if final
            else None,
        },
    )
