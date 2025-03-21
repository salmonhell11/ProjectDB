import unittest
import sys
import os
import base64
import bcrypt
from flask import Flask
from unittest.mock import patch
from datetime import datetime

# Lägg till sökväg till projektet
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'blueprints', 'userside'))

# Importera blueprint och dtt
from userside import userside_bp, dtt

# Dummy-klasser
class FakeUser:
    def __init__(self, email, passw, is_admin):
        self.email = email
        self.passw = bcrypt.hashpw(passw.encode("utf-8"), bcrypt.gensalt())
        self.is_admin = is_admin

class FakeAuction:
    def __init__(self):
        self.auction_id = 1
        self.category = "Furniture"
        self.starting_bid = 500
        self.item_description = "Stol"
        self.auction_end_datetime = "2025-04-01 12:00:00"

# Auth-header för testklient
def get_auth_headers(username, password):
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode("utf-8")
    return {"Authorization": f"Basic {encoded}"}

# Setup för alla tests
class BaseFlaskTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config["TESTING"] = True
        cls.app.register_blueprint(userside_bp)
        cls.client = cls.app.test_client()

# /see_auction
class TestSeeAuctionRoute(BaseFlaskTest):
    @patch("auth.auth.get_user")
    @patch("db.db.get_action_with_bids")
    def test_see_auction_page_returns_200(self, mock_get_action_with_bids, mock_get_user):
        mock_get_user.return_value = FakeUser("test@example.com", "secret123", 0)
        mock_get_action_with_bids.return_value = (FakeAuction(), [])
        headers = get_auth_headers("test@example.com", "secret123")
        response = self.client.get("/see_auction?auction_id=1", headers=headers)
        self.assertEqual(response.status_code, 200)

    @patch("auth.auth.get_user")
    @patch("db.db.get_action_with_bids")
    def test_see_auction_contains_expected_text(self, mock_get_action_with_bids, mock_get_user):
        mock_get_user.return_value = FakeUser("test@example.com", "secret123", 0)
        mock_get_action_with_bids.return_value = (FakeAuction(), [])
        headers = get_auth_headers("test@example.com", "secret123")
        response = self.client.get("/see_auction?auction_id=1", headers=headers)
        self.assertIn(b"Stol", response.data)

# /make_bid
class TestMakeBidRoute(BaseFlaskTest):
    @patch("auth.auth.get_user")
    def test_make_bid_get_renders_page(self, mock_get_user):
        mock_get_user.return_value = FakeUser("test@example.com", "secret123", 0)
        headers = get_auth_headers("test@example.com", "secret123")
        response = self.client.get("/make_bid?auction_id=1", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please fill", response.data)

    @patch("auth.auth.get_user")
    @patch("db.db.place_bid")
    def test_make_bid_post_success(self, mock_place_bid, mock_get_user):
        mock_get_user.return_value = FakeUser("test@example.com", "secret123", 0)
        mock_place_bid.return_value = None
        headers = get_auth_headers("test@example.com", "secret123")
        response = self.client.post(
            "/make_bid?auction_id=1",
            headers=headers,
            data={"adding_bid": "1", "bid_amount": "600"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

# / (index sida)
class TestIndexRoute(BaseFlaskTest):
    @patch("auth.auth.get_user")
    @patch("db.db.search_auctions")
    def test_index_page_returns_200(self, mock_search_auctions, mock_get_user):
        mock_get_user.return_value = FakeUser("test@example.com", "secret123", 0)
        mock_search_auctions.return_value = []
        headers = get_auth_headers("test@example.com", "secret123")
        response = self.client.get("/", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"category", response.data)

# dtt() – datumhantering
class TestDateConversion(unittest.TestCase):
    def test_dtt_valid_datetime(self):
        result = dtt("2025-04-01 12:00:00")
        self.assertIsInstance(result, datetime)

    def test_dtt_valid_date(self):
        result = dtt("2025-04-01")
        self.assertIsInstance(result, datetime)

    def test_dtt_invalid_input(self):
        with self.assertRaises(ValueError):
            dtt("not-a-date")

if __name__ == '__main__':
    unittest.main()
