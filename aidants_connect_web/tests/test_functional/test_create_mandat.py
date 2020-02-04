import time
from selenium.webdriver.firefox.webdriver import WebDriver

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from django.test import tag

from aidants_connect_web.tests.test_functional.test_utilities import login_aidant
from aidants_connect_web.tests.factories import UserFactory


@tag("functional", "new_mandat")
class CreateNewMandat(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        # FC only calls back on specific port
        cls.port = settings.FC_AS_FS_TEST_PORT
        cls.aidant = UserFactory()
        device = cls.aidant.staticdevice_set.create(id=1)
        device.token_set.create(token="123456")
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)
        cls.selenium.get(f"{cls.live_server_url}/usagers/")

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_create_new_mandat(self):
        login_aidant(self)

        welcome_aidant = self.selenium.find_element_by_tag_name("h1").text
        self.assertEqual(welcome_aidant, "Vos mandats")

        self.assertEqual(
            len(self.selenium.find_elements_by_class_name("fake-table-row")), 0
        )

        # Create new mandat
        add_usager_button = self.selenium.find_element_by_id("add_usager")
        add_usager_button.click()

        demarches_section = self.selenium.find_element_by_id("demarches")
        demarche_title = demarches_section.find_element_by_tag_name("h2").text
        self.assertEqual(demarche_title, "Étape 1 : Sélectionnez la ou les démarche(s)")

        demarches_grid = self.selenium.find_element_by_id("demarches_list")
        demarches = demarches_grid.find_elements_by_tag_name("input")
        self.assertEqual(len(demarches), 10)

        demarches_section.find_element_by_id("argent").find_element_by_tag_name(
            "label"
        ).click()
        demarches_section.find_element_by_id("famille").find_element_by_tag_name(
            "label"
        ).click()

        duree_section = self.selenium.find_element_by_id("duree")
        duree_section.find_element_by_id("long").find_element_by_tag_name(
            "label"
        ).click()

        # FranceConnect
        fc_button = self.selenium.find_element_by_id("submit_button")
        fc_button.click()
        fc_title = self.selenium.title
        self.assertEqual("Connexion - choix du compte", fc_title)
        time.sleep(2)

        # Click on the 'Démonstration' identity provider
        demonstration_hex = self.selenium.find_element_by_id(
            "fi-identity-provider-example"
        )
        demonstration_hex.click()
        time.sleep(2)

        # FC - Use the Mélaine_trois credentials
        demo_title = self.selenium.find_element_by_tag_name("h3").text
        self.assertEqual(demo_title, "Fournisseur d'identité de démonstration")
        submit_button = self.selenium.find_elements_by_tag_name("input")[2]
        self.assertEqual(submit_button.get_attribute("type"), "submit")
        submit_button.click()

        # FC - Validate the information
        submit_button = self.selenium.find_element_by_tag_name("input")
        submit_button.click()
        time.sleep(2)

        # Recap all the information for the Mandat
        recap_title = self.selenium.find_element_by_tag_name("h1").text
        self.assertEqual(recap_title, "Récapitulatif du mandat")
        recap_text = self.selenium.find_element_by_id("recap_text").text
        self.assertIn("Angela Claire Louise DUBOIS ", recap_text)
        checkboxes = self.selenium.find_elements_by_tag_name("input")
        id_personal_data = checkboxes[1]
        self.assertEqual(id_personal_data.get_attribute("id"), "id_personal_data")
        id_personal_data.click()
        id_brief = checkboxes[2]
        self.assertEqual(id_brief.get_attribute("id"), "id_brief")
        id_brief.click()
        id_otp_token = checkboxes[3]
        self.assertEqual(id_otp_token.get_attribute("id"), "id_otp_token")
        id_otp_token.send_keys("123456")
        submit_button = checkboxes[-1]
        self.assertEqual(submit_button.get_attribute("type"), "submit")
        submit_button.click()
        time.sleep(2)

        # Success page
        success_title = self.selenium.find_element_by_tag_name("h1").text
        self.assertEqual(success_title, "Le mandat a été créé avec succès !")
        go_to_usager_button = self.selenium.find_element_by_class_name(
            "tiles"
        ).find_elements_by_tag_name("a")[1]
        go_to_usager_button.click()
        time.sleep(2)

        # See all mandats of usager page
        # Should find 3 table rows: 1 header row + 2 mandat rows
        self.assertEqual(len(self.selenium.find_elements_by_tag_name("tr")), 3)
