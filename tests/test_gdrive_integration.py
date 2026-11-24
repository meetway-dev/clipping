import unittest
import urllib.parse
from core.gdrive_manager import GoogleDriveManager

class TestGoogleDriveIntegration(unittest.TestCase):
    """
    Tests for Google Drive cloud sync and mobile TikTok export workflow.
    """

    def setUp(self):
        self.gdm = GoogleDriveManager.get_instance()

    def test_gdrive_status(self):
        data = self.gdm.get_status()
        self.assertIn("connected", data)
        self.assertIn("folder_name", data)
        self.assertIn("has_credentials", data)

    def test_gdrive_configure_and_auth_url(self):
        test_cid = "123456789-testclient.apps.googleusercontent.com"
        test_sec = "GOCSPX-testsecret123"
        test_folder = "TikTok Viral Clips"

        cfg = self.gdm.configure(
            client_id=test_cid,
            client_secret=test_sec,
            folder_name=test_folder
        )
        self.assertTrue(cfg["has_credentials"])
        self.assertEqual(cfg["folder_name"], test_folder)

        auth_url = self.gdm.get_auth_url()
        self.assertIn("accounts.google.com/o/oauth2/v2/auth", auth_url)
        
        parsed = urllib.parse.urlparse(auth_url)
        qs = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(qs["client_id"][0], test_cid)
        self.assertIn("drive.file", qs["scope"][0])

    def test_gdrive_upload_unauthorized_when_not_connected(self):
        self.gdm.disconnect()
        self.assertFalse(self.gdm.is_connected())
        with self.assertRaises(RuntimeError) as ctx:
            self.gdm.upload_file("storage/outputs/test_rendered_padding.mp4")
        self.assertIn("Google Drive is not connected", str(ctx.exception))

    def test_gdrive_disconnect(self):
        self.gdm.disconnect()
        self.assertFalse(self.gdm.is_connected())

if __name__ == "__main__":
    unittest.main()
