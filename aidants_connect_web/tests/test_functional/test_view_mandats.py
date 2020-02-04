from datetime import timedelta
from selenium.webdriver.firefox.webdriver import WebDriver

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.utils import timezone

from aidants_connect_web.models import Aidant, Usager, Mandat
from aidants_connect_web.tests.test_functional.utilities import login_aidant
from aidants_connect_web.tests.factories import UserFactory, UsagerFactory


@tag("functional")
class ViewMandats(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = UserFactory()
        cls.usager = UsagerFactory(given_name="Joséphine", sub_fc="test_sub")
        cls.usager2 = UsagerFactory(given_name="Corentin", sub_fc="test_sub2")
        cls.mandat = Mandat.objects.create(
            aidant=Aidant.objects.get(username="thierry@thierry.com"),
            usager=Usager.objects.get(sub_fc="test_sub"),
            demarche=["social"],
            expiration_date=timezone.now() + timedelta(days=6),
        )
        cls.mandat2 = Mandat.objects.create(
            aidant=Aidant.objects.get(username="thierry@thierry.com"),
            usager=Usager.objects.get(sub_fc="test_sub"),
            demarche=["papiers"],
            expiration_date=timezone.now() + timedelta(days=1),
        )
        cls.mandat3 = Mandat.objects.create(
            aidant=Aidant.objects.get(username="thierry@thierry.com"),
            usager=Usager.objects.get(sub_fc="test_sub2"),
            demarche=["famille"],
            expiration_date=timezone.now() + timedelta(days=365),
        )
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)
        cls.selenium.get(f"{cls.live_server_url}/dashboard/")

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_grouped_mandats(self):
        self.selenium.get(f"{self.live_server_url}/dashboard/")

        # Login
        login_aidant(self)

        # Dashboard
        self.selenium.find_element_by_id("view_mandats").click()

        # Mandat List
        self.assertEqual(
            len(self.selenium.find_elements_by_class_name("fake-table-row")), 2
        )
