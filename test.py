import requests
import unittest

BASE_URL = "http://localhost:8000" 

class TestAPI(unittest.TestCase):
    def setUp(self):
        response = requests.post(f"{BASE_URL}/token?github_code=token")
        response.raise_for_status() 
        self.token = response.json().get("access_token")
        self.assertIsNotNone(self.token) 

    def test_deploy(self):
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        data = {
            "image_link": "ghcr.io/jeffreywangdev/campton:main",
            "main_domain": "test.jeffrey.hackclub.app",
            "name": "test-app-deploy", 
            "docker_flags": []
        }

        response = requests.post(f"{BASE_URL}/deploy", headers=headers, json=data)
        self.assertEqual(response.status_code, 200) 
        self.assertIn("message", response.json())
        
if __name__ == "__main__":
    unittest.main()