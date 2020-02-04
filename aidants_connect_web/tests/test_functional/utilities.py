import time
from django.core import mail


def login_aidant(self):
    login_field = self.selenium.find_element_by_id("id_email")
    login_field.send_keys("thierry@thierry.com")
    submit_button = self.selenium.find_element_by_xpath("//button")
    submit_button.click()
    email_sent_title = self.selenium.find_element_by_tag_name("h1").text
    time.sleep(5)
    self.assertEqual(
        email_sent_title, "Un email vous a été envoyé pour vous connecter."
    )
    self.assertEqual(len(mail.outbox), 1)
    token_email = mail.outbox[0].body
    line_containing_magic_link = token_email.split("\n")[2]
    magic_link_https = line_containing_magic_link.split()[-1]
    magic_link_http = magic_link_https.replace("https", "http", 1)
    self.selenium.get(magic_link_http)
