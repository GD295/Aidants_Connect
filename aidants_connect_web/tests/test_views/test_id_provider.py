import json
from pytz import timezone as pytz_timezone
from secrets import token_urlsafe
from datetime import date, datetime, timedelta
from freezegun import freeze_time

from django.db.models.query import QuerySet
from django.test.client import Client
from django.test import TestCase, override_settings, tag
from django.urls import resolve
from django.utils import timezone
from django.conf import settings
from django.urls import reverse

from aidants_connect_web.views import id_provider
from aidants_connect_web.models import (
    Connection,
    Aidant,
    Usager,
    Mandat,
    CONNECTION_EXPIRATION_TIME,
    Journal,
)
from aidants_connect_web.tests.factories import UserFactory, UsagerFactory

fc_callback_url = settings.FC_AS_FI_CALLBACK_URL


@tag("id_provider")
class AuthorizeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.aidant_thierry = UserFactory()
        self.aidant_jacques = UserFactory(
            username="jacques@domain.user", email="jacques@domain.user"
        )
        Aidant.objects.create_user(
            "Jacques", "jacques@domain.user", "motdepassedejacques"
        )
        self.usager = UsagerFactory(given_name="Joséphine", sub_fc="123")
        Mandat.objects.create(
            aidant=Aidant.objects.get(username="thierry@thierry.com"),
            usager=Usager.objects.get(sub_fc="123"),
            demarche="Revenus",
            expiration_date=timezone.now() + timedelta(days=6),
        )

        Mandat.objects.create(
            aidant=Aidant.objects.get(username="thierry@thierry.com"),
            usager=Usager.objects.get(sub_fc="123"),
            demarche="Famille",
            expiration_date=timezone.now() + timedelta(days=12),
        )

        Mandat.objects.create(
            aidant=Aidant.objects.get(username=self.aidant_jacques.username),
            usager=Usager.objects.get(sub_fc="123"),
            demarche="Logement",
            expiration_date=timezone.now() + timedelta(days=12),
        )
        date_further_away_minus_one_hour = datetime(
            2019, 1, 9, 8, tzinfo=pytz_timezone("Europe/Paris")
        )
        Connection.objects.create(
            state="test_expiration_date_triggered",
            code="test_code",
            nonce="test_nonce",
            usager=Usager.objects.get(sub_fc="123"),
            expiresOn=date_further_away_minus_one_hour,
        )

    def test_authorize_url_triggers_the_authorize_view(self):
        self.client.force_login(self.aidant_thierry)
        found = resolve("/authorize/")
        self.assertEqual(found.func, id_provider.authorize)

    def test_authorize_url_without_arguments_returns_400(self):
        self.client.force_login(self.aidant_thierry)
        response = self.client.get("/authorize/")
        self.assertEqual(response.status_code, 400)

    def test_authorize_url_triggers_the_authorize_template(self):
        self.client.force_login(self.aidant_thierry)
        good_data = {
            "state": token_urlsafe(4),
            "nonce": token_urlsafe(4),
            "response_type": "code",
            "client_id": settings.FC_AS_FI_ID,
            "redirect_uri": settings.FC_AS_FI_CALLBACK_URL,
            "scope": "openid profile email address phone birth",
            "acr_values": "eidas1",
        }

        response = self.client.get("/authorize/", data=good_data)

        self.assertTemplateUsed(
            response, "aidants_connect_web/id_provider/authorize.html"
        )

    def test_authorize_url_without_right_parameters_triggers_bad_request(self):
        self.client.force_login(self.aidant_thierry)
        good_data = {
            "state": token_urlsafe(4),
            "nonce": token_urlsafe(4),
            "response_type": "code",
            "client_id": settings.FC_AS_FI_ID,
            "redirect_uri": settings.FC_AS_FI_CALLBACK_URL,
            "scope": "openid profile email address phone birth",
            "acr_values": "eidas1",
        }

        for data, value in good_data.items():
            data_with_missing_item = good_data.copy()
            del data_with_missing_item[data]
            response = self.client.get("/authorize/", data=data_with_missing_item)

            self.assertEqual(response.status_code, 400)

    def test_authorize_url_with_wrong_parameters_triggers_403(self):
        self.client.force_login(self.aidant_thierry)

        dynamic_data = {"state": token_urlsafe(4), "nonce": token_urlsafe(4)}
        good_static_data = {
            "response_type": "code",
            "client_id": settings.FC_AS_FI_ID,
            "redirect_uri": settings.FC_AS_FI_CALLBACK_URL,
            "scope": "openid profile email address phone birth",
            "acr_values": "eidas1",
        }

        for data, value in good_static_data.items():
            static_data_with_wrong_item = good_static_data.copy()
            static_data_with_wrong_item[data] = "wrong_data"
            sent_data = {**dynamic_data, **static_data_with_wrong_item}
            response = self.client.get("/authorize/", data=sent_data)

            self.assertEqual(response.status_code, 403)

    def test_authorize_sends_the_correct_amount_of_usagers(self):
        self.client.force_login(self.aidant_thierry)

        response = self.client.get(
            "/authorize/",
            data={
                "state": token_urlsafe(4),
                "nonce": "fc_call_nonce",
                "response_type": "code",
                "client_id": settings.FC_AS_FI_ID,
                "redirect_uri": settings.FC_AS_FI_CALLBACK_URL,
                "scope": "openid profile email address phone birth",
                "acr_values": "eidas1",
            },
        )

        self.assertIsInstance(response.context["state"], str)
        self.assertIsInstance(response.context["usagers"], QuerySet)
        self.assertEqual(len(response.context["usagers"]), 1)
        self.assertIsInstance(response.context["aidant"], Aidant)

    def test_sending_user_information_triggers_callback(self):
        self.client.force_login(self.aidant_thierry)
        c = Connection.objects.create(
            state="test_state", code="test_code", nonce="test_nonce", usager=self.usager
        )
        usager_id = c.usager.id
        response = self.client.post(
            "/authorize/", data={"state": "test_state", "chosen_usager": usager_id}
        )
        saved_items = Connection.objects.all()
        self.assertEqual(saved_items.count(), 2)
        connection = saved_items[1]
        state = connection.state
        self.assertEqual(connection.usager.sub_fc, "123")
        self.assertNotEqual(connection.nonce, "No Nonce Provided")

        url = reverse("fi_select_demarche") + "?state=" + state
        self.assertRedirects(response, url, fetch_redirect_response=False)

    date_further_away = datetime(2019, 1, 9, 9, tzinfo=pytz_timezone("Europe/Paris"))

    @freeze_time(date_further_away)
    def test_post_to_authorize_with_expired_connexion_triggers_bad_request(self):
        self.client.force_login(self.aidant_thierry)
        response = self.client.post(
            "/authorize/",
            data={"state": "test_expiration_date_triggered", "chosen_usager": 1},
        )
        self.assertEqual(response.status_code, 400)


@tag("id_provider")
class FISelectDemarcheTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.aidant_thierry = UserFactory()
        self.usager = UsagerFactory(given_name="Joséphine", sub_fc="123")

        self.connection = Connection.objects.create(
            state="test_state", code="test_code", nonce="test_nonce", usager=self.usager
        )

        date_further_away_minus_one_hour = datetime(
            2019, 1, 9, 8, tzinfo=pytz_timezone("Europe/Paris")
        )
        self.connection = Connection.objects.create(
            state="test_expiration_date_triggered",
            code="test_code",
            nonce="test_nonce",
            usager=self.usager,
            expiresOn=date_further_away_minus_one_hour,
        )
        mandat_creation_date = datetime(
            2019, 1, 5, 3, 20, 34, 0, tzinfo=pytz_timezone("Europe/Paris")
        )
        self.mandat = Mandat.objects.create(
            aidant=self.aidant_thierry,
            usager=self.usager,
            demarche="transports",
            expiration_date=mandat_creation_date + timedelta(days=6),
            creation_date=mandat_creation_date,
        )

        self.mandat_2 = Mandat.objects.create(
            aidant=self.aidant_thierry,
            usager=self.usager,
            demarche="famille",
            expiration_date=mandat_creation_date + timedelta(days=6),
            creation_date=mandat_creation_date,
        )

        self.mandat_3 = Mandat.objects.create(
            aidant=self.aidant_thierry,
            usager=self.usager,
            demarche="logement",
            expiration_date=mandat_creation_date + timedelta(days=3),
            creation_date=mandat_creation_date,
        )

    def test_FI_select_demarche_url_triggers_the_fi_select_demarche_view(self):
        self.client.force_login(self.aidant_thierry)
        found = resolve("/select_demarche/")
        self.assertEqual(found.func, id_provider.fi_select_demarche)

    def test_FI_select_demarche_triggers_FI_select_demarche_template(self):
        self.client.force_login(self.aidant_thierry)
        response = self.client.get("/select_demarche/", data={"state": "test_state"})
        self.assertTemplateUsed(
            response, "aidants_connect_web/id_provider/fi_select_demarche.html"
        )

    date_close = datetime(2019, 1, 6, 9, tzinfo=pytz_timezone("Europe/Paris"))

    @freeze_time(date_close)
    def test_get_demarches_for_one_usager_and_two_mandats(self):
        self.client.force_login(self.aidant_thierry)

        response = self.client.get("/select_demarche/", data={"state": "test_state"})
        demarches = response.context["demarches"]
        mandats = [demarche for demarche in demarches]
        self.assertIn("famille", mandats)
        self.assertIn("transports", mandats)
        self.assertIn("logement", mandats)
        self.assertEqual(len(mandats), 3)

    date_further_away = datetime(2019, 1, 9, 9, tzinfo=pytz_timezone("Europe/Paris"))

    @freeze_time(date_further_away)
    def test_expired_mandat_does_not_appear(self):
        self.client.force_login(self.aidant_thierry)
        response = self.client.get("/select_demarche/", data={"state": "test_state"})
        demarches = response.context["demarches"]

        mandats = [demarche for demarche in demarches]
        self.assertIn("famille", mandats)
        self.assertIn("transports", mandats)
        self.assertNotIn("logement", mandats)
        self.assertEqual(len(mandats), 2)

    @freeze_time(date_further_away)
    def test_post_to_select_demarche_triggers_redirect(self):
        self.client.force_login(self.aidant_thierry)
        response = self.client.post(
            "/select_demarche/",
            data={"state": "test_state", "chosen_demarche": "famille"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, f"{fc_callback_url}?code=test_code&state=test_state"
        )

    @freeze_time(date_further_away)
    def test_post_to_select_demarche_with_expired_demarche_triggers_403(self):
        self.client.force_login(self.aidant_thierry)
        response = self.client.post(
            "/select_demarche/",
            data={"state": "test_state", "chosen_demarche": "logement"},
        )
        self.assertEqual(response.status_code, 403)

    @freeze_time(date_further_away)
    def test_post_to_select_demarche_with_expired_connexion_triggers_timeout(self):
        self.client.force_login(self.aidant_thierry)
        response = self.client.post(
            "/select_demarche/",
            data={
                "state": "test_expiration_date_triggered",
                "chosen_demarche": "famille",
            },
        )
        self.assertEqual(response.status_code, 400)


@tag("id_provider")
@override_settings(
    FC_AS_FI_ID="test_client_id",
    FC_AS_FI_SECRET="test_client_secret",
    FC_AS_FI_CALLBACK_URL="test_url.test_url",
    HOST="localhost",
)
class TokenTests(TestCase):
    def setUp(self):
        self.connection = Connection()
        self.connection.state = "test_state"
        self.connection.code = "test_code"
        self.connection.nonce = "test_nonce"
        self.connection.usager = UsagerFactory(
            given_name="Joséphine", sub_fc="test_sub"
        )
        self.connection.expiresOn = datetime(
            2012, 1, 14, 3, 21, 34, tzinfo=pytz_timezone("Europe/Paris")
        )
        self.connection.save()
        self.fc_request = {
            "grant_type": "authorization_code",
            "redirect_uri": "test_url.test_url",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "code": "test_code",
        }

    def test_token_url_triggers_token_view(self):
        found = resolve("/token/")
        self.assertEqual(found.func, id_provider.token)

    date = datetime(2012, 1, 14, 3, 20, 34, 0, tzinfo=pytz_timezone("Europe/Paris"))

    @freeze_time(date)
    def test_correct_info_triggers_200(self):

        response = self.client.post("/token/", self.fc_request)

        response_content = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response_content)
        connection = Connection.objects.get(code="test_code")
        awaited_response = {
            "access_token": connection.access_token,
            "expires_in": 3600,
            # "id_token": "",
            "refresh_token": "5ieq7Bg173y99tT6MA",
            "token_type": "Bearer",
        }

        del response_json["id_token"]  # sub_fi is random, can't test
        self.assertEqual(response_json, awaited_response)

    def test_wrong_grant_type_triggers_403(self):
        fc_request = dict(self.fc_request)
        fc_request["grant_type"] = "not_authorization_code"
        response = self.client.post("/token/", fc_request)
        self.assertEqual(response.status_code, 403)

    def test_wrong_redirect_uri_triggers_403(self):
        fc_request = dict(self.fc_request)
        fc_request["redirect_uri"] = "test_url.test_url/wrong_uri"

        response = self.client.post("/token/", fc_request)
        self.assertEqual(response.status_code, 403)

    def test_wrong_client_id_triggers_403(self):
        fc_request = dict(self.fc_request)
        fc_request["client_id"] = "wrong_client_id"
        response = self.client.post("/token/", fc_request)
        self.assertEqual(response.status_code, 403)

    def test_wrong_client_secret_triggers_403(self):
        fc_request = dict(self.fc_request)
        fc_request["client_secret"] = "wrong_client_secret"
        response = self.client.post("/token/", fc_request)
        self.assertEqual(response.status_code, 403)

    def test_wrong_code_triggers_403(self):
        fc_request = dict(self.fc_request)
        fc_request["code"] = "wrong_code"
        response = self.client.post("/token/", fc_request)
        self.assertEqual(response.status_code, 403)

    def test_missing_parameters_triggers_bad_request(self):
        for parameter in self.fc_request:
            bad_request = dict(self.fc_request)
            del bad_request[parameter]
            response = self.client.post("/token/", bad_request)
            self.assertEqual(response.status_code, 400)

    date_expired = date + timedelta(minutes=CONNECTION_EXPIRATION_TIME + 20)

    @freeze_time(date_expired)
    def test_expired_code_triggers_403(self):
        response = self.client.post("/token/", self.fc_request)
        self.assertEqual(response.status_code, 403)


@tag("id_provider")
class UserInfoTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.usager = Usager.objects.create(
            given_name="Joséphine",
            family_name="ST-PIERRE",
            preferred_username="ST-PIERRE",
            birthdate=date(1969, 12, 25),
            gender="F",
            birthplace=70447,
            birthcountry=99100,
            sub_fc="test_sub",
            email="User@user.domain",
            creation_date="2019-08-05T15:49:13.972Z",
        )

        self.usager_2 = Usager.objects.create(
            given_name="Joséphine",
            family_name="ST-PIERRE",
            preferred_username="ST-PIERRE",
            birthdate=date(1969, 12, 25),
            gender="F",
            birthplace=70447,
            birthcountry=99100,
            sub_fc="test_sub2",
            email="User@user.domain",
            creation_date="2019-08-05T15:49:13.972Z",
        )

        self.aidant_thierry = UserFactory()

        self.mandat = Mandat.objects.create(
            aidant=self.aidant_thierry,
            usager=self.usager,
            demarche="transports",
            expiration_date=timezone.now() + timedelta(days=6),
        )

        self.connection = Connection.objects.create(
            state="test_state",
            code="test_code",
            nonce="test_nonce",
            usager=self.usager,
            access_token="test_access_token",
            expiresOn=datetime(
                2012, 1, 14, 3, 21, 34, 0, tzinfo=pytz_timezone("Europe/Paris")
            ),
            aidant=self.aidant_thierry,
            mandat=self.mandat,
        )

    def test_token_url_triggers_token_view(self):
        found = resolve("/userinfo/")
        self.assertEqual(found.func, id_provider.user_info)

    date = datetime(2012, 1, 14, 3, 20, 34, 0, tzinfo=pytz_timezone("Europe/Paris"))

    @freeze_time(date)
    def test_well_formatted_access_token_returns_200(self):

        response = self.client.get(
            "/userinfo/", **{"HTTP_AUTHORIZATION": "Bearer test_access_token"}
        )

        FC_formated_info = {
            "given_name": "Joséphine",
            "family_name": "ST-PIERRE",
            "preferred_username": "ST-PIERRE",
            "birthdate": "1969-12-25",
            "gender": "F",
            "birthplace": "70447",
            "birthcountry": "99100",
            "sub_fc": "test_sub",
            "sub_fi": self.connection.usager.sub_fi,
            "email": "User@user.domain",
            "creation_date": "2019-08-05T15:49:13.972Z",
        }

        content = response.json()

        self.assertEqual(content, FC_formated_info)

    @freeze_time(date)
    def test_mandat_use_triggers_journal_entry(self):

        self.client.get(
            "/userinfo/", **{"HTTP_AUTHORIZATION": "Bearer test_access_token"}
        )

        journal_entries = Journal.objects.all()

        self.assertEqual(journal_entries.count(), 2)
        self.assertEqual(journal_entries[1].action, "use_mandat")

    date_expired = date + timedelta(minutes=CONNECTION_EXPIRATION_TIME + 20)

    @freeze_time(date_expired)
    def test_expired_access_token_returns_403(self):
        response = self.client.get(
            "/userinfo/", **{"HTTP_AUTHORIZATION": "Bearer test_access_token"}
        )

        self.assertEqual(response.status_code, 403)

    def test_badly_formatted_authorization_header_triggers_403(self):
        response = self.client.get(
            "/userinfo/", **{"HTTP_AUTHORIZATION": "test_access_token"}
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            "/userinfo/", **{"HTTP_AUTHORIZATION": "Bearer: test_access_token"}
        )
        self.assertEqual(response.status_code, 403)

    def test_wrong_token_triggers_403(self):
        response = self.client.get(
            "/userinfo/", **{"HTTP_AUTHORIZATION": "wrong_access_token"}
        )
        self.assertEqual(response.status_code, 403)
