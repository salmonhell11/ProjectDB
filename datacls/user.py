from dataclasses import dataclass
import datetime

@dataclass
class User:
  id:int=0 #auto increment
  email: str = ""
  passw: str= ""
  is_admin: int = 0
