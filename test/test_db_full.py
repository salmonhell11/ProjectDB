import unittest
import sqlite3
import bcrypt
from datetime import datetime
from db import db
from datacls.user import User
from datacls.auction import Auction
from datacls.bid import Bid

class TestDbFunctions(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.create_all_tables()

    def tearDown(self):
        self.conn.close()

    def create_all_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS Auction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                starting_bid INTEGER NOT NULL,
                item_description TEXT NOT NULL,
                auction_end_datetime TEXT NOT NULL,
                best_bid_amount INTEGER DEFAULT 0,
                best_bid_id INTEGER DEFAULT 0,
                likes_count INTEGER DEFAULT 0,
                dislikes_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS Bid (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                bid_amount INTEGER NOT NULL,
                bid_datetime TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS User (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                passw TEXT NOT NULL,
                is_admin INT NOT NULL
            );
        """)
        self.conn.commit()

    def test_user_operations(self):
        db.add_user(self.conn, "test@example.com", "secret", 0)
        user = db.get_user(self.conn, "test@example.com")
        self.assertIsInstance(user, User)
        users = db.list_users(self.conn)
        self.assertEqual(len(users), 1)
        db.delete_user(self.conn, "test@example.com")
        user = db.get_user(self.conn, "test@example.com")
        self.assertIsNone(user)

    def test_auction_crud(self):
        auction_id = db.new_auction(self.conn, 100, "Book", datetime.now(), "Books")
        self.assertIsInstance(auction_id, int)
        auctions = db.search_auctions(self.conn, "Book")
        self.assertGreaterEqual(len(auctions), 1)
        db.edit_auction(self.conn, auction_id, 200, "New Book", "2025-01-01 10:00:00", "Novels")
        db.like_auction(self.conn, auction_id)
        db.dislike_auction(self.conn, auction_id)
        db.delete_auction(self.conn, auction_id)
        auctions = db.search_auctions(self.conn, "Book")
        self.assertEqual(len(auctions), 0)

    def test_bid_flow(self):
        db.add_user(self.conn, "bidder@example.com", "secret", 0)
        auction_id = db.new_auction(self.conn, 50, "Chair", datetime.now(), "Furniture")
        db.place_bid(self.conn, "bidder@example.com", auction_id, 60)
        auction, bids = db.get_action_with_bids(self.conn, auction_id)
        self.assertIsInstance(auction, Auction)
        self.assertGreaterEqual(len(bids), 1)
        db.delete_bid(self.conn, bids[0].id)

if __name__ == '__main__':
    unittest.main()
