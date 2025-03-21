import sqlite3
import datetime
import os

import bcrypt
from datacls.auction import Auction
from datacls.bid import Bid
from datacls.user import User

from os import path


######################################################
########## Database connection managment #############
######################################################

 # Funktion som kallar/ansluter till SQlite databas
def get_conn():
    root = path.dirname(path.realpath(__file__))
    fn = path.join(root, "..", "auctionsite.db")
    conn = sqlite3.connect(fn)
    return conn
# Funktionen som stänger anslutningen till databas
def close_conn(conn):
    try:
        conn.commit()
    except:
        pass
    try:
        conn.close()
    except:
        pass
#test
def test():
    return "This is test"



######################################################
########## Creating database structure ###############
######################################################

#Funktion som skapar databas och tabellerna
def create_db():
    root = path.dirname(path.realpath(__file__))
    fn = path.join(root, "..", "auctionsite.db")
    if os.path.exists(fn):
        return
    # Auktionstabellen skapas om den inte finns redan
    conn = sqlite3.connect(fn)
    cursor = conn.cursor()
    cursor.execute("""
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
        )
    """)
    #Budgivningstabellen skapas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Bid (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auction_id INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            bid_amount INTEGER NOT NULL,
            bid_datetime TEXT NOT NULL,
            FOREIGN KEY (auction_id) REFERENCES Auction(id)
        )
    """)

    #Tabellen user skapas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            passw TEXT NOT NULL,
            is_admin INT NOT NULL
        )
    """)

    conn.commit()
    conn.close()



######################################################
################# User managment #####################
######################################################

 # Denna funktion tar fram user baserat på vilken email
def get_user(sqlite_connection,email)->User|None:
    query = "select * from User where email = ?"

    sqlite_connection.row_factory = sqlite3.Row
    cursor = sqlite_connection.cursor()
    cursor.execute(query, [email])
    rows = cursor.fetchall()
    if len(rows)==0:
        return None
    return User(**dict(rows[0]))

 # Funktionen som lägger till användare
def list_users(sqlite_connection)->list[User]:
    query = "select * from User "

    sqlite_connection.row_factory = sqlite3.Row
    cursor = sqlite_connection.cursor()
    cursor.execute(query, [])
    rows = cursor.fetchall()
    if len(rows)==0:
        return []
    return [User(**dict(row)) for row in rows]


def add_user(sqlite_connection,email,passw,is_admin):
    hashed = bcrypt.hashpw(passw.encode('utf-8'), bcrypt.gensalt())
    cursor = sqlite_connection.cursor()
    cursor.execute("""
        INSERT INTO User (email,passw,is_admin) VALUES(?,?,?)
    """, [email,hashed,is_admin])
    sqlite_connection.commit()

 # Denna funktionen tar bort användare efter deras email
def delete_user(sqlite_connection,email):

    cursor = sqlite_connection.cursor()
    cursor.execute("""
        DELETE from User where email = ?
    """, [email])
    sqlite_connection.commit()


######################################################
################# Auction managment ##################
######################################################

# Funktion för att påbörja en ny auktion
def new_auction(sqlite_connection, starting_bid, item_description, auction_end_datetime, category):
    cursor = sqlite_connection.cursor()
    cursor.execute("""INSERT INTO Auction (starting_bid, item_description, auction_end_datetime, category)
                        VALUES(?,?,?,?)
                   """,
                   [starting_bid, item_description, auction_end_datetime.isoformat(), category])
    sqlite_connection.commit()
    id = cursor.lastrowid
    return id
 # Funktion för att söka fram en auktion beroende på input kriterierna som anges i sökrutorna
def search_auctions(sqlite_connection, search_str=None, best_bid_amount_min=None, best_bid_amount_max=None, auction_end_from=None, auction_end_to=None, category=None)->list[Auction]:
    wheres = []
    params = []

    if search_str is not None and search_str != "":
        wheres.append("item_description LIKE ?")
        params.append(f"%{search_str}%")

    if category:
        wheres.append("category = ?")
        params.append(category)

    if best_bid_amount_min is not None:
        wheres.append("best_bid_amount >= ?")
        params.append(best_bid_amount_min)

    if best_bid_amount_max is not None:
        wheres.append("best_bid_amount <= ?")
        params.append(best_bid_amount_max)

    if auction_end_from is not None:
        wheres.append("auction_end_datetime >= ?")
        params.append(auction_end_from.isoformat())

    if auction_end_to is not None:
        wheres.append("auction_end_datetime <= ?")
        params.append(auction_end_to.isoformat())

    query = "SELECT * FROM Auction"
    if len(wheres) > 0:
        query += " WHERE " + " AND ".join(wheres)

    sqlite_connection.row_factory = sqlite3.Row
    cursor = sqlite_connection.cursor()
    cursor.execute(query, params)

    rows = cursor.fetchall()
    return [Auction(**dict(row)) for row in rows]

 # Funktionen som hämtar auktioner och buden som finns baserat på auktionens ID
def get_action_with_bids(sqlite_connection, auction_id)->tuple[Auction,list[Bid]]:
    sqlite_connection.row_factory = sqlite3.Row
    cursor = sqlite_connection.cursor()

    query = "SELECT * FROM Auction where id = ?"
    cursor.execute(query, [auction_id])
    row = cursor.fetchall()[0]
    auction = Auction(**dict(row))

    query = "SELECT * FROM Bid where auction_id = ? ORDER BY bid_amount DESC"
    cursor.execute(query, [auction_id])
    rows = cursor.fetchall()

    bids = [Bid(**dict(row)) for row in rows]

    return (auction, bids)

def delete_auction(sqlite_connection, auction_id):
    cursor = sqlite_connection.cursor()
    cursor.execute("""
        DELETE from Bid WHERE auction_id = ?
    """, [auction_id])
# Auktionen raderas
    cursor.execute("""
        DELETE from Auction WHERE id = ?
    """, [auction_id])
    sqlite_connection.commit()

# Den här funktionen redigerar auktioner  som endast admins kan genomföra
def edit_auction(sqlite_connection, auction_id, starting_bid=None, item_description=None, auction_end_datetime=None, category=None):
    cursor = sqlite_connection.cursor()

    ups = []
    params = []
    # parametrar läggs till för uppdateringarna
    if item_description is not None:
        ups.append("item_description = ?")
        params.append(item_description)

    if starting_bid is not None:
        ups.append("starting_bid = ?")
        params.append(starting_bid)

    if auction_end_datetime is not None:
        ups.append("auction_end_datetime = ?")
        params.append(auction_end_datetime)

    if category:
        ups.append("category = ?")
        params.append(category)

    if category is not None:
        ups.append("category = ?")
        params.append(category)

    query = "UPDATE Auction"
    if len(ups) > 0:
        query += " SET " + " , ".join(ups)

    query += " WHERE id = ?"
    params.append(auction_id) #Auktionens ID läggs in i parametrar

    cursor.execute(query, params) #Uppdaterar databas
    sqlite_connection.commit() #Sparar änbdringarna till databas


# Denna funktionen är till för likes och har blan d annat counter för antal
def like_auction(sqlite_connection, auction_id):
    cursor = sqlite_connection.cursor()
    cursor.execute("""
        UPDATE Auction SET likes_count = likes_count + 1 where id = ?
                   """, [auction_id])

    sqlite_connection.commit()

# Denna funktion är till för dislikes och har också counter för antal
def dislike_auction(sqlite_connection, auction_id):
    cursor = sqlite_connection.cursor()
    cursor.execute("""
        UPDATE Auction SET dislikes_count = dislikes_count + 1 where id = ?
                   """, [auction_id])

    sqlite_connection.commit()


######################################################
#################### Bid managment ###################
######################################################  

#Funktion för att kunna lägga ett nytt bud på auktioner
def place_bid(sqlite_connection, user_email, auction_id, bid_amount):
    cursor = sqlite_connection.cursor()
    now_datetime = datetime.datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO Bid (auction_id, user_email, bid_amount, bid_datetime)
            VALUES (?,?,?,?)
    """, [auction_id, user_email, bid_amount, now_datetime])
    sqlite_connection.commit()
    id = cursor.lastrowid
    # Ett nytt bud läggs till i Bid tabellen
    #Information om högsta budet uppdateras
    cursor.execute("""
        UPDATE Auction SET best_bid_amount = ?, best_bid_id = ? WHERE id = ? AND best_bid_amount< ?
    """, [bid_amount, id, auction_id, bid_amount])
    sqlite_connection.commit() #med commit sparas justeringar till databasen

#Funktion som tar bort en auktion och allt som finns tillhörande den
def delete_bid(sqlite_connection, bid_id):
    cursor = sqlite_connection.cursor()
    cursor.execute("""
        DELETE from Bid WHERE id = ?
    """, [bid_id])
    sqlite_connection.commit()

