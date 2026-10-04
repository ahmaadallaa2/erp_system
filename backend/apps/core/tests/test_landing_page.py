from django.test import TestCase


class LandingPageTestCase(TestCase):
    def test_root_renders_branded_html_landing_page(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        self.assertTemplateUsed(response, "core/landing.html")
        self.assertContains(response, "Wethaq ERP")
        self.assertContains(response, "وثاق ERP")
        self.assertContains(response, "AI-integrated commercial ERP")
        self.assertContains(response, '<a class="button" href="/admin/">Go to Admin Panel</a>', html=True)

    def test_root_is_public(self):
        response = self.client.get("/")

        self.assertNotIn("Location", response)
        self.assertEqual(response.status_code, 200)
