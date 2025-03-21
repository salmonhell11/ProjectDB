import bcrypt
from flask import redirect
from flask_httpauth import HTTPBasicAuth
from db.db import get_conn,close_conn, get_user

# Förskapade användarkonton för inlogg med admins och vanliga users
users = {
    "admin": "xxx998xxx",
    "admin@h23mlaak.pythonanywhere.com":"xxx998xxx",
    "admin@testing.se":"testing",
    "user@testing.se":"testing",
    "h23mlaak@du.se":"xxx998xxx",
    "h23danbl@du.se":"xxx998xxx",
    "h23dohkh@du.se":"xxx998xxx",
}
#instansiering för autentifikation
auth = HTTPBasicAuth()
@auth.verify_password # funktion som verifierar att lösenord och inlogg/mailen stämmer överens och kallar på databasen för att stämma av
def verify_password(user_email, passw):
    if user_email in users and users[user_email] == passw:
        return user_email

    conn = get_conn()
    user_data = get_user(conn,user_email)
    close_conn(conn)
    if user_data is None:
        return None

    if bcrypt.checkpw(passw.encode('utf-8'), user_data.passw):
        return user_data.email


    return None

#Errorhanterare

@auth.error_handler
def unauthorized():
    return """
    <script>
    function reload_clean(){
        const protocol = window.location.protocol;
        const domain = window.location.hostname;
        const port = window.location.port ? `:${window.location.port}` : '';
        window.location.href = `${protocol}//@${domain}${port}/`;

    }
    </script>

    <button onclick="reload_clean()">Login</button>



    """
    # Omdirigering om autentiseringen av inloggning inte lyckas
    return redirect("/")

def is_admin():
    current_user_email = auth.current_user()
    if current_user_email in ["admin","admin@h23mlaak.pythonanywhere.com","admin@testing.se"]:
        return True

    conn = get_conn()
    current_user = get_user(conn,current_user_email)
    close_conn(conn)
    if current_user is None:
        return False
    return current_user.is_admin == 1

def get_current_user():
    return auth.current_user()