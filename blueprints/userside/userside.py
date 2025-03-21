from datetime import datetime
from flask import Blueprint, flash, render_template, request, redirect
from db.db import get_conn,close_conn,search_auctions
from db.db import get_action_with_bids, place_bid
from db.db import like_auction, dislike_auction


from auth.auth import auth,get_current_user

# Funktion som konverterar datum till datetimeobjekt i olika format.
def dtt(date_str):
    date_str = date_str.replace("T"," ")
    try:
        res = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except:
        res = datetime.strptime(date_str, "%Y-%m-%d")
    return res
# Blueprint med template för vyer
userside_bp = Blueprint("userside",__name__,template_folder="templates")

@userside_bp.route("/",methods=['GET', 'POST'])
@auth.login_required
def index_route():
    #Från Getbegäran hämtas de olika paramterarna i filtret.
    #search_query_str = request.form.get('search', "")
    search_query_str = request.args.get('search', "")
    category = request.args.get('category', '')
    best_bid_amount_min_str = request.args.get('best_bid_amount_min', "")
    best_bid_amount_max_str = request.args.get('best_bid_amount_max', "")
    auction_end_from_str = request.args.get('auction_end_from', "")
    auction_end_to_str = request.args.get('auction_end_to', "")

    # Här hanteras standardvärden som anges i det fall ingen input skrivits in..
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
 # Kallar på datasen
    conn = get_conn()
# Gilla och ogilla knapparna/buttons hanteras nedan
    auction_to_like = request.form.get('auction_to_like', None)
    auction_to_dislike = request.form.get('auction_to_dislike', None)

    if auction_to_like is not None:
        like_auction(conn,int(auction_to_like))
    if auction_to_dislike is not None:
        dislike_auction(conn,int(auction_to_dislike))
    #Auktionerna som filtrerats ut hämtas
    auctions = search_auctions(conn,search_query,
                               best_bid_amount_min=best_bid_amount_min,
                               best_bid_amount_max=best_bid_amount_max,
                               auction_end_from=auction_end_from,
                               auction_end_to=auction_end_to,category=category)
    # Stänger databas
    close_conn(conn)
    # Genererar landningssidan för users (index))
    return render_template("index_user.html",auctions=auctions,search_query_str=search_query_str,
                           category=category,
                           best_bid_amount_min=best_bid_amount_min_str,
                           best_bid_amount_max=best_bid_amount_max_str,
                           auction_end_from=auction_end_from_str,
                           auction_end_to=auction_end_to_str)



@userside_bp.route("/make_bid",methods=['GET', 'POST'])
@auth.login_required
def make_new_bid_route():
    # Auktions ID från GETbegäran
    auction_id = request.args.get('auction_id', "")
    adding_bid = request.form.get('adding_bid', None)

    bid_amount_str = ""
    #Validering görs på inputfälten för att skriva in bud
    error = "Please fill"
    if adding_bid is not None:
        error = ""
        bid_amount_str = request.form.get('bid_amount', None)

    if error =="":
        try:                # Bud läggs till i databsen
            conn = get_conn()
            place_bid(conn,
                      user_email=get_current_user(), #!!!
                      auction_id=int(auction_id),
                      bid_amount=int(bid_amount_str))
            close_conn(conn)
        except Exception as e:
            error = str(e)
            close_conn(conn)
        if error == "":
            flash('Bid made succesfully!')
            return redirect("/see_auction?auction_id="+auction_id)

    if error!="":
        return render_template("make_user_bid.html", # Genererar budformuläret
                           auction_id=auction_id,
                           bid_amount=bid_amount_str,
                           error = error)



@userside_bp.route("/see_auction",methods=['GET', 'POST'])
@auth.login_required
def do_edit_auction_route(): #Hämtar auktionens ID från paramtern i GET
    auction_id = request.args.get('auction_id', "")

    conn = get_conn()

    (auction,bids) = get_action_with_bids(conn,auction_id)
    close_conn(conn)
    # Data som skall visas
    item_description = auction.item_description
    category = auction.category
    starting_bid_str = str(auction.starting_bid)
    auction_end_datetime_str = str(auction.auction_end_datetime)
    auction_end_datetime_str = auction_end_datetime_str.replace("T"," ")
    #Genererar sida i html för att se nuvarande auktioner och dess detaljer..
    return render_template("see_auction.html",
                        auction_id = auction_id,
                        item_description=item_description,
                        category=category,
                        starting_bid=starting_bid_str,
                        auction_end_datetime=auction_end_datetime_str,
                        bids = bids)