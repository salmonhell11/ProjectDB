from datetime import datetime
from flask import Blueprint, render_template, request, redirect
from db.db import get_conn,close_conn,search_auctions,delete_auction
from db.db import new_auction,get_action_with_bids,edit_auction, place_bid
from db.db import delete_bid, like_auction, dislike_auction


from auth.auth import auth,is_admin

# Funktionen ser till att datumsträng konverteras till datetimeobjekt..
def dtt(date_str):
    date_str = date_str.replace("T"," ")
    try:    #Konverterar sträng till ÅÅMMDD HHMMSS format
        res = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except: #Blir det fel så försöker formatet ÅÅMMDD istället..
        res = datetime.strptime(date_str, "%Y-%m-%d")
    return res

# Blueprint till Admindelen av hemsidan skapas upp
admin_bp = Blueprint("admin",__name__,template_folder="templates")

# Routing till Adminsöversikt.
@admin_bp.route("/admin/",methods=['GET', 'POST'])
@auth.login_required
def index_route(): # Kontroll om användaren är admin (inloggad som admin eller ej)
    if not is_admin():
        return render_template("must_be_admin.html")
    # Filterparamteters från GETbegärningen ..
    #search_query_str = request.form.get('search', "")
    search_query_str = request.args.get('search', "")
    category = request.args.get('category', '')
    best_bid_amount_min_str = request.args.get('best_bid_amount_min', "")
    best_bid_amount_max_str = request.args.get('best_bid_amount_max', "")
    auction_end_from_str = request.args.get('auction_end_from', "")
    auction_end_to_str = request.args.get('auction_end_to', "")

    # Om ingen input skrivits in så hanteras de standardvärden som finns nedanför
    if search_query_str != "":
        search_query = search_query_str
    else:
        search_query = None

    try:
        best_bid_amount_min = int(best_bid_amount_min_str)
    except:
        best_bid_amount_min = None

    try:
        best_bid_amount_max = int(best_bid_amount_max_str)
    except:
        best_bid_amount_max = None

    try:
        auction_end_from = dtt(auction_end_from_str)
    except:
        auction_end_from = None

    try:
        auction_end_to = dtt(auction_end_to_str)
    except:
        auction_end_to = None


    #kallar på databasen
    conn = get_conn()
    # Koden hanterar radering av auktioner samt gilla och ogillar knapptrycken för auktionerna
    auction_to_delete = request.form.get('auction_to_delete', None)
    auction_to_like = request.form.get('auction_to_like', None)
    auction_to_dislike = request.form.get('auction_to_dislike', None)

    if auction_to_delete is not None:
        delete_auction(conn,int(auction_to_delete))
    if auction_to_like is not None:
        like_auction(conn,int(auction_to_like))
    if auction_to_dislike is not None:
        dislike_auction(conn,int(auction_to_dislike))
    # De auktioner som filtrerar ut i sökningen hämtas
    auctions = search_auctions(conn,search_query,
                               best_bid_amount_min=best_bid_amount_min,
                               best_bid_amount_max=best_bid_amount_max,
                               auction_end_from=auction_end_from,
                               auction_end_to=auction_end_to,category=category)
    # Stänger ned databas kallningen
    close_conn(conn)
    # Adminsidan med auktionerna genereras
    return render_template("index.html",auctions=auctions,search_query_str=search_query_str, category=category,
                           best_bid_amount_min=best_bid_amount_min_str,
                           best_bid_amount_max=best_bid_amount_max_str,
                           auction_end_from=auction_end_from_str,
                           auction_end_to=auction_end_to_str)

# Routning för att kunna skapa en helt ny auktion som admin
@admin_bp.route("/admin/new_auction", methods=['GET', 'POST'])
@auth.login_required
def make_new_auction_route(): #Kontroll genomförs som ser till att det är en admin som vill skapa
    if not is_admin():
        return render_template("must_be_admin.html")
    # De variabler för den nya auktionen sätts upp
    adding_auction = request.form.get('adding_auction', None)
    item_description = ""
    starting_bid_str = ""
    auction_end_datetime_str = ""
    category = ""
    error = "Please fill"
    if adding_auction is not None:#Hanteringen för input för nya auktioner
        error = ""
        item_description = request.form.get('item_description', None)
        starting_bid_str = request.form.get('starting_bid', None)
        auction_end_datetime_str = request.form.get('auction_end_datetime', None)
        category = request.form.get('category', None)
        try:
            auction_end_datetime = dtt(auction_end_datetime_str)
        except:
            error += "Date must be of format %Y-%m-%d %H:%M:%S"
        if not starting_bid_str:
            starting_bid = 0
        else:
            try:
                starting_bid = int(starting_bid_str)
            except:
                error += "Starting bid must be integer"
    # Om inga fel hittas skapas den nya auktionen
    if error == "":
        try:
            conn = get_conn()
            new_auction(conn,
                        starting_bid=starting_bid,
                        item_description=item_description,
                        auction_end_datetime=auction_end_datetime,
                        category=category)
            close_conn(conn)
        except Exception as e:
            error = str(e)
            close_conn(conn)
        if error == "":
            return redirect("/admin/")
    # Genererar den htmlsida som skapar upp ny auktion och med felmeddelanden om det dyker upp..
    return render_template("new_auction.html",
                           item_description=item_description,
                           starting_bid=starting_bid_str,
                           auction_end_datetime=auction_end_datetime_str,
                           category=category,
                           error=error)




    # Routning som kan redigera de auktioner som redan existerar. och endast admins har behörighet att genomföra det vilket också kontrolleras..
@admin_bp.route("/admin/edit_auction", methods=['GET', 'POST'])
@auth.login_required
def do_edit_auction_route():
    if not is_admin():
        return render_template("must_be_admin.html")

    saving_auction = request.form.get('save_auction', None)
    bid_to_delete = request.form.get('bid_to_delete', None)
    auction_id = request.args.get('auction_id', "")
    #Kallar på databasen
    conn = get_conn()
    # Bud från databasen tas bort från den auktionen som valts i redigering av auktion
    if bid_to_delete is not None:
        delete_bid(conn, int(bid_to_delete))
    # Information om auktionens beskrivning och bud etc hämtas in
    (auction, bids) = get_action_with_bids(conn, auction_id)
    close_conn(conn) # Stänger databas
    # Auktionenens information till redigeringsformulär
    item_description = auction.item_description
    starting_bid_str = str(auction.starting_bid)
    auction_end_datetime_str = str(auction.auction_end_datetime).replace("T", " ")
    category = auction.category
    error = "Please fill"
    if saving_auction is not None:
        error = ""
        item_description = request.form.get('item_description', None)
        starting_bid_str = request.form.get('starting_bid', None)
        auction_end_datetime_str = request.form.get('auction_end_datetime', None)
        category = request.form.get('category', None)
        try:
            auction_end_datetime = dtt(auction_end_datetime_str)
        except:
            error += "Date must be of format %Y-%m-%d %H:%M:%S"
        if not starting_bid_str:
            starting_bid = 0
        else:
            try:
                starting_bid = int(starting_bid_str)
            except:
                error += "Starting bid must be integer"

    if error == "": #Om inga fel hittas så uppdateras auktionen till databasen med de nya parametrarna
        try:
            conn = get_conn()
            edit_auction(conn,
                         auction_id=auction_id,
                         starting_bid=starting_bid,
                         item_description=item_description,
                         auction_end_datetime=auction_end_datetime,
                         category=category)
            close_conn(conn)
        except Exception as e:
            error = str(e)
            close_conn(conn)
        if error == "":
            return redirect("/admin/")
    # Genererar sidan som visar de uppdaterade paramterarna för auktionen..
    return render_template("edit_auction.html",
                           item_description=item_description,
                           starting_bid=starting_bid_str,
                           auction_end_datetime=auction_end_datetime_str,
                           category=category,
                           error=error,
                           bids=bids)


# Routning som skapar ett nytt bud om man är administratör
@admin_bp.route("/admin/make_bid",methods=['GET', 'POST'])
@auth.login_required
def make_new_bid_route():
    if not is_admin():
        return render_template("must_be_admin.html")
    # Förfrågning som hämtar in auktionens egna ID
    auction_id = request.args.get('auction_id', "")
    adding_bid = request.form.get('adding_bid', None)

    user_email = ""
    bid_amount_str = ""

    error = "Please fill"
    if adding_bid is not None:#userns mail och budbelopp tas emot om ett nytt bud skall anges..
        error = ""
        user_email = request.form.get('user_email', None)
        bid_amount_str = request.form.get('bid_amount', None)
    # har det nya budet genomförts korrrekt så läggs det till i databasen
    if error =="":
        try:
            conn = get_conn()
            place_bid(conn,
                      user_email=user_email,
                      auction_id=int(auction_id),
                      bid_amount=int(bid_amount_str))
            close_conn(conn)
        except Exception as e:
            error = str(e)
            close_conn(conn)# Lyckas budet genomföras så återgår man till sidan för budredig.. av auktioner
        if error == "":
            return redirect("/admin/edit_auction?auction_id="+auction_id)
    #Annars om fel dyker upp så återgårs till felmeddelande om att det inte gick.
    if error!="":
        return render_template("make_bid.html",
                           user_email=user_email,
                           auction_id=auction_id,
                           bid_amount=bid_amount_str,
                           error = error)
