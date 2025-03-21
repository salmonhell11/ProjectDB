from datetime import datetime
from flask import Blueprint, render_template, request, redirect
from db.db import get_conn,close_conn,delete_user,list_users,add_user

from auth.auth import auth,is_admin

# Skapar blueprinten som ger admin de funktioner som behövs
admin_users_bp = Blueprint("admin_users",__name__,template_folder="templates")

#Getförfrågningar och Postförfrågningar  hanteras i funktionen
@admin_users_bp.route("/admin_users/",methods=['GET', 'POST'])
@auth.login_required
def index_route():
    if not is_admin():
        return render_template("must_be_user_admin.html")

    user_to_delete = request.form.get('user_to_delete', None)

    conn = get_conn()
    users = list_users(conn)
    if user_to_delete is not None:
        delete_user(conn,user_to_delete)
    users = list_users(conn)
    close_conn(conn)

    return render_template("index_users_admin.html",users = users)
#Routning för adminöversikten
@admin_users_bp.route("/admin_users/add_user",methods=['GET', 'POST'])
@auth.login_required
def add_user_route():
    if not is_admin():#Kontroll körs om användaren som är inloggad har adminrättigheter
        return render_template("must_be_user_admin.html")
# Vilken användare som ska raderas om metoden post körs
    user_to_delete = request.form.get('user_to_delete', None)
#Databasanslutning
    conn = get_conn()
    users = list_users(conn)
    if user_to_delete is not None:
        delete_user(conn,user_to_delete)
    close_conn(conn)
#Genererar htmlsidan som visar alla befintliga användare på sidan
    return render_template("index_users_admin.html",users = users)


#Routning för att göra nya users
@admin_users_bp.route("/admin_users/new_user", methods=['GET', 'POST'])
@auth.login_required
def make_new_user_route():
    if not is_admin():
        return render_template("must_be_admin.html")
#Hämtar formulärens data som behövs för att skapa en ny användare
    adding_user = request.form.get('adding_user', None)
    error = "Please fill"
    if adding_user is not None:#Om det finns data så hanteras använder inputen
        error = ""
        user_email = request.form.get('user_email', None)
        user_passw = request.form.get('user_passw', None)
        user_is_admin = request.form.get('user_is_admin', 0)
        conn = get_conn()
        try:
            add_user(conn,user_email,user_passw,user_is_admin)
        except Exception as e:
            error += "Try again (maybe the user already exists)" + str(e)
        close_conn(conn)
    if error == "":
        return redirect("/admin_users/")
# Genererar htmlsidan för att lägga till ny användare och visar om det blivit fel någonstans

    return render_template("new_user.html",error=error)

