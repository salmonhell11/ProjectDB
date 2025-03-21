from dataclasses import dataclass
import datetime
# Vi använder dataklassdekoratorn för att kunna automatiskt skapa upp...
#klass med standardfunktioner.
@dataclass
class Auction: #Auktionklass
  id:int=0 #automatiskt inkrement på id för varje auktion
  category: str = "" #kategoribeskrivning i strängformat.
  starting_bid:int=0 # startbud som startar vid 0
  item_description:str="" # beskriver varan på auktionen
  auction_end_datetime:datetime.datetime|None = None #sluttid för auktion
  best_bid_amount:int=0 # högsta bud som startar från 0
  best_bid_id:int=0 # id på auktionen vars vara har högsta bud..
  likes_count:int=0 #antal likes counter
  dislikes_count:int=0 #antal dislike counter