from dataclasses import dataclass
import datetime
# Bid klassen använder dataclass från pythondekorering som då ger standardmetoder
# detta för att förenkla kodning av klassen som vi använder för att spara datan om autkioner..
@dataclass
class Bid:
  id:int=0 #automatiskt inkrement..
  auction_id:int=0 #id för auktionen i integer.
  user_email:str="" #strängformat till budgivarens mail
  bid_amount:int=0 # budsumma i integer
  bid_datetime:datetime.datetime|None = None #nuvarande tid i databasen
