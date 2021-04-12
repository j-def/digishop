from django.shortcuts import render, HttpResponse
import pyodbc
from data_manager import manager, queue
import json
import datetime
import paypalrestsdk
from paypalrestsdk import Payment
import requests
import random
import string
import re
import math
import sendgrid
from digishop_emailer import emailer
dbserver = 'REGCONSERVER1'
dbdatabase = 'digishop'
dbusername = 'belotecainventory'
dbpassword = 'belotecainventory'

# Create your views here.
def home(request):
    try:
        request.session['username']
        return render(request, "homepage.html", {"userAccountImage": "loggedIn"})
    except:
        return render(request, "homepage.html", {
        "userAccountImage": "loggedOut"})


def login(request):
    return render(request, "login.html")

def signup(request):
    return render(request, "signup.html")

def test_username(request):
    if request.method == "GET":
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT username from users where username=?", (request.GET["username"]))
        if cursor.fetchone() == None:
            cnxn.close()
            return HttpResponse("invalid")
        else:
            cnxn.close()
            return HttpResponse("valid")

def test_email(request):
    if request.method == "GET":
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT email from users where email=?", (request.GET["email"]))
        if cursor.fetchone() == None:
            cnxn.close()
            return HttpResponse("invalid")
        else:
            cnxn.close()
            return HttpResponse("valid")


def test_login(request):
    if request.method == "GET":
        username = request.GET["username"]
        password = request.GET["password"]
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT username, password from users where username=? AND password=?", (username,password))
        if cursor.fetchone() == None:
            return HttpResponse("invalid")
        else:
            request.session["username"] = username
            return HttpResponse("valid")

def finalize_signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        email = request.POST["email"]
        if len(password) < 6:
            return HttpResponse("Password does not meet requirements.")
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT username from users WHERE username=?", username)
        if cursor.fetchone() == None:
            cursor.execute("INSERT INTO users (username, password, wallet_balance,email) VALUES(?,?,'0',?)", (username, password, email))
            cnxn.commit()
        else:
            return HttpResponse("Username in use. Pick a new one")
        cnxn.close()
        return HttpResponse("success")

def logout(request):
    del request.session["username"]
    return render(request, "redirect.html", {"url": "/"})

def query_1(request):
    if request.method == "GET":
        dataRequest = request.GET['request']
        m = manager()
        if dataRequest == "allNames":
            return HttpResponse(';'.join(m.grab_player_names()))
        if dataRequest == "nameMoments":
            name = request.GET['name']
            jsonResp = m.grab_player_moments_with_name(name)
            jsonResponse = []
            for item in jsonResp:
                date = datetime.datetime.strptime(item['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ")
                jsonResponse.append({"playSeries": item['set']['flowSeriesNumber'], "playType": item['set']['flowName'], "playId": item['id'], "playTeam": item['play']['stats']['teamAtMoment'], "playCategory": item['play']['stats']['playCategory'], "playDate":"%s-%s-%s" % (date.year, date.month, date.day)})

            return HttpResponse(json.dumps(jsonResponse), content_type="application/json")

def moment_page(request):
    if request.method == "GET":
        try:
            request.session['username']
            userAccountImage = "loggedIn"
        except:
            userAccountImage = "loggedOut"
        momentData = manager().grab_moment_by_id(request.GET['momentId'])
        playerName = momentData['play']['stats']['playerName']
        date = datetime.datetime.strptime(momentData['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ")
        momentDate = "%s-%s-%s" % (date.year, date.month, date.day)
        momentCategory = momentData['play']['stats']['playCategory']
        return render(request, "moment-page.html", {"playerName": playerName,
                                                    "momentDate": momentDate,
                                                    "momentCategory": momentCategory,
                                                    "momentId": request.GET['momentId'],
                                                    "userAccountImage": userAccountImage})

def statistics_table(request):
    if request.method == "GET":
        momentData = manager().grab_moment_by_id(request.GET['momentId'])
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT COUNT(moment_id) FROM listings WHERE moment_id=?", (request.GET['momentId']))
        responseJson = {
            "set": momentData['set']['flowName'],
            "series": "Series "+str(momentData['set']['flowSeriesNumber']),
            "playerTeam": momentData['play']['stats']['teamAtMoment'],
            "playCategory": momentData['play']['stats']['playCategory'],
            "image": manager().grab_moment_icon_by_id(request.GET['momentId']),
            "circulationCount": momentData['circulationCount'],
            "date": datetime.datetime.fromisoformat(momentData['play']['stats']['dateOfMoment'][:-1]).strftime('%m-%d-%Y'),
            "name": momentData['play']['stats']['playerName'],
            "imagePrefix": momentData['assetPathPrefix'],
            "listings": "Listings: "+ str(cursor.fetchone()[0])
        }
        return HttpResponse(json.dumps(responseJson), content_type="application/json")

def listings_table(request):
    import math
    if request.method == "GET":
        momentId = request.GET['momentId']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT moment_id, price, owner_username, serial, listing_id, listed_timestamp from listings WHERE moment_id=? ORDER BY serial ASC", momentId)
        respJson = [{"serial": item[3], "price": item[1], "listing": item[4], "daysListed": math.floor((int(datetime.datetime.now().timestamp())-int(item[5]))/(24*60*60))} for item in cursor.fetchall()]
        cnxn.close()
        return HttpResponse(json.dumps(respJson), content_type="application/json")

def sold_listings_table(request):
    if request.method == "GET":
        momentId = request.GET['momentId']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT serial, price, sold_timestamp from sold_listings WHERE moment_id=? AND status != 'cancelled' ORDER BY serial ASC", momentId)
        respJson = [{"serial": item[0], "price": item[1], "dateSold": str(datetime.datetime.fromtimestamp(int(item[2])).strftime("%m-%d-%Y"))} for item in cursor.fetchall()]
        cnxn.close()
        return HttpResponse(json.dumps(respJson), content_type="application/json")

def purchase_page(request):
    if request.method == "GET":
        try:
            purchaserUsername = request.session['username']
        except:
            return render(request, "redirect.html", {"url": "/login/"})
        listingId = request.GET["listingId"]
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT * from listings WHERE listing_id=?", listingId)
        momentId, distinctMomentId, price, ownerUsername, serial, listingId, listingTimestamp = cursor.fetchone()
        cnxn.close()
        m = manager()
        rjson = m.grab_moment_by_id(momentId)
        print(rjson)
        date = datetime.datetime.strptime(rjson['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ")
        momentDate = "%s-%s-%s" % (date.year, date.month, date.day)
        momentTitle = rjson['play']['stats']['playerName'] + " | " + rjson['play']['stats']['playCategory'] + " | " + momentDate
        serialNumber = str(serial) + "/" + str(rjson['circulationCount'])
        return render(request, "purchase.html", {"momentId": momentId, "momentTitle": momentTitle, "momentPrice": price,
                                                 "serialNumber": serialNumber, "listingId": listingId})

def generate_payment_paypal(request):
    if request.method == "GET":
        listingId = request.GET["listingId"]
        request.session["purchaseListingId"] = listingId

        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT * from listings WHERE listing_id=?", listingId)
        momentId, distinctMomentId, price, ownerUsername, serial, listingId, listingTimestamp = cursor.fetchone()
        cnxn.close()


        paypalrestsdk.configure({
            'mode': 'live',  # sandbox or live
            'client_id': 'ATusgTPA59uRaBrfFRy1JVtNSt5O7FBkkF1wMEwU-XyKkixH3CwIKRqrR9yb2UEckX9NkjVKY4ydlgUf',
            'client_secret': 'ECQS0iOl1Vyfc5ZZm_gn4TRcXXKqYAXdxDyvK4Zf3w3wXc4Fkt45Rx5M9DOhEnbI2Y5cDVZEMRbAW1Z9'})


        # Create payment object
        payment = Payment({
            "intent": "sale",

            # Set payment method
            "payer": {
                "payment_method": "paypal"
            },

            # Set redirect URLs
            "redirect_urls": {
                "return_url": "http://127.0.0.1:8000/purchase/complete/",
                "cancel_url": "http://127.0.0.1:8000/"
            },

            # Set transaction object
            "transactions": [{
                "amount": {
                    "total": str(price)+".00",
                    "currency": "USD"
                },
                "description": "Listing ID: "+listingId
            }]
        })

        if payment.create():
            # Extract redirect url
            for link in payment.links:
                if link.rel == "approval_url":
                    # Convert to str to avoid Google App Engine Unicode issue
                    # https://github.com/paypal/rest-api-sdk-python/pull/58
                    approval_url = str(link.href)
                    request.session['approval_url'] = approval_url
                if link.method == "REDIRECT":
                    # Capture redirect url
                    redirect_url = (link.href)
            return render(request, "redirect.html", {"url": redirect_url})
            # Redirect the customer to redirect_url
           
        else:
            print("Error while creating payment:")
            print(payment.error)


def make_payment(request):
    if request.method == "GET":
        purchaserUsername = request.session['username']
        listingId = request.session['purchaseListingId']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT * from listings WHERE listing_id=?", listingId)
        momentId, distinctMomentId, price, ownerUsername, serial, listingId, listingTimestamp = cursor.fetchone()
        cnxn.close()
        m = manager()
        rjson = m.grab_moment_by_id(momentId)
        date = datetime.datetime.strptime(rjson['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ")
        momentDate = "%s-%s-%s" % (date.year, date.month, date.day)
        momentTitle = rjson['play']['stats']['playerName'] + " | " + rjson['play']['stats'][
            'playCategory'] + " | " + momentDate
        serialNumber = str(serial) + "/" + str(rjson['circulationCount'])
        paypalPaymentId = request.GET["paymentId"]
        paypalToken = request.GET["token"]
        paypalPayerId = request.GET["PayerID"]
        return render(request, "purchase-complete.html", {"momentId": momentId, "momentTitle": momentTitle, "momentPrice": price,
                                                 "serialNumber": serialNumber, "listingId": listingId, "paypalPaymentId": paypalPaymentId,
                                                "paypalToken": paypalToken, "paypalPayerId": paypalPayerId})

def finalize_payment(request):
    if request.method == "GET":
        sendTo = request.GET['withdrawAccount']
        buyer = request.session['username']
        r = requests.get("https://www.nbatopshot.com/user/@" + sendTo + "/moments")
        rShaven = r.text[r.text.find("publicInfo"):r.text.rfind('"username"')]
        dapperId = rShaven[rShaven.find("\"dapperID\":\"") + len("\"dapperID\":\""):rShaven.find("\",\"username\":")]
        if len(sendTo) < 3 or dapperId == "":
            return HttpResponse(json.dumps({"status": "Invalid TopShot Username. Try a new one."}), content_type="application/json")
        paypalrestsdk.configure({
            'mode': 'live',  # sandbox or live
            'client_id': 'ATusgTPA59uRaBrfFRy1JVtNSt5O7FBkkF1wMEwU-XyKkixH3CwIKRqrR9yb2UEckX9NkjVKY4ydlgUf',
            'client_secret': 'ECQS0iOl1Vyfc5ZZm_gn4TRcXXKqYAXdxDyvK4Zf3w3wXc4Fkt45Rx5M9DOhEnbI2Y5cDVZEMRbAW1Z9'})
        payment = paypalrestsdk.Payment.find(request.GET["paypalPaymentId"])
        if payment.execute({"payer_id": request.GET["paypalPayerId"]}):

            print("Payment execute successfully")
            cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
            cursor = cnxn.cursor()
            cursor.execute("SELECT moment_id, distinct_moment_id, price, owner_username, serial, listed_timestamp FROM listings WHERE listing_id=?", (request.GET['listingId']))
            moment_id, distinct_moment_id, price, owner_username, serial, listed_timestamp = cursor.fetchone()
            cursor.execute("SELECT wallet_balance FROM users WHERE username=?", (owner_username))
            balance = float(cursor.fetchone()[0])
            newBalance = balance + ((float(price) * 0.92) - 0.30)
            #Not adding to the users wallet balance yet because moment has not been sent yet
            #cursor.execute("UPDATE users SET wallet_balance=? WHERE username=?", (newBalance, owner_username))
            order_id = ''.join([random.choice(string.ascii_uppercase+string.digits) for x in range(27)])
            cursor.execute("DELETE FROM listings WHERE listing_id=?", (request.GET['listingId']))
            cursor.execute("INSERT INTO sold_listings (moment_id, distinct_moment_id, price, owner_username, serial, listing_id,"
                           "listed_timestamp, sold_timestamp, buyer_username, paypal_transaction, status, withdraw_account, order_id) "
                           "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (moment_id,distinct_moment_id, price, owner_username,
                                                                  serial, request.GET['listingId'], listed_timestamp,
                                                                  str(int(datetime.datetime.now().timestamp())), buyer,
                                                                  request.GET["paypalPaymentId"], "awaiting_moment",
                                                                  sendTo, order_id))
            cnxn.commit()
            cnxn.close()
            e = emailer()
            e.sale_creation(buyer, owner_username, order_id)
            return HttpResponse(json.dumps({"status": "success"}),
                            content_type="application/json")


        else:
            return HttpResponse(json.dumps({"status": "Error Checking Out"}), content_type="application/json")


def user_account(request):
    try:
        clientUsername = request.session['username']
    except:
        return render(request, "redirect.html", {"url": "/login/"})
    return render(request, "account.html", {"username": clientUsername})

def retrieve_account_data(request):
    if request.method == "GET":
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT email, wallet_balance from users WHERE username=?", request.session['username'])
        email, walletBalance = cursor.fetchone()
        m = manager()
        cursor.execute("SELECT moment_id, price, serial, listing_id FROM listings WHERE owner_username=?", request.session['username'])
        userListings = [{"momentId": listing[0], "price": listing[1], "serial": listing[2], "listingId": listing[3], "momentImage": m.grab_moment_icon_by_id(listing[0]), "momentName": m.generate_moment_name_by_id(listing[0])} for listing in cursor.fetchall()]
        cnxn.close()
        respJson = {
            "email": email,
            "walletBalance": walletBalance,
            "activeListings": userListings
        }
        return HttpResponse(json.dumps(respJson), content_type="application/json")

def retrieve_completed_wallet_withdraws(request):
    if request.method == "GET":
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT withdraw_amount, withdraw_email from withdraw_requests WHERE status='sent' AND owner_account=?", request.session['username'])
        r = [{"amount": float(item[0]), "email": str(item[1])} for item in cursor.fetchall()]
        return HttpResponse(json.dumps(r), content_type="application/json")
def retrieve_account_sold_data(request):
    if request.method == "GET":
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        m = manager()

        cursor.execute("SELECT moment_id, price, serial, listing_id, CASE WHEN owner_username=? AND buyer_username=? THEN 'Sale/Purchase' WHEN owner_username=? THEN 'Sale' WHEN buyer_username=? THEN 'Purchase' END AS owner FROM sold_listings WHERE (owner_username=? OR buyer_username=?) AND status='sent'", (request.session['username'],request.session['username'],request.session['username'],request.session['username'],request.session['username'],request.session['username']))
        userListings = [{"momentId": listing[0], "price": listing[1], "serial": listing[2], "listingId": listing[3], "momentImage": m.grab_moment_icon_by_id(listing[0]), "momentName": m.generate_moment_name_by_id(listing[0]), "transactionType": listing[4]} for listing in cursor.fetchall()]
        return HttpResponse(json.dumps(userListings), content_type="application/json")

def retrieve_account_pending_withdraws(request):
    if request.method == "GET":
        ownerUsername = request.session['username']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        m = manager()
        cursor.execute("SELECT moment_id, serial, withdraw_account, price, sold_timestamp FROM sold_listings WHERE buyer_username=? AND status=?", (ownerUsername, "awaiting_moment"))

        return HttpResponse(json.dumps([{"imagePrefix": m.grab_moment_icon_by_id(item[0]),
          "serial": item[1],
          "name": m.generate_moment_name_by_id(item[0]),
            "daysRemaining": (7 - math.floor((int(datetime.datetime.now().timestamp()) - int(item[4])) / 86400)),
         "saleAmount": item[3],
            "sendTo": item[2]} for item in cursor.fetchall()]),
            content_type="application/json")

def retrieve_account_pending_paypal_withdraws(request):
    if request.method == "GET":
        ownerUsername = request.session['username']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT withdraw_email, withdraw_amount FROM withdraw_requests WHERE owner_account=? AND status='awaiting_withdraw'", (ownerUsername))
        respJson = [{"amount": str(item[1]), "email": item[0]} for item in cursor.fetchall()]
        return HttpResponse(json.dumps(respJson), content_type="application/json")

def retrieve_account_pending_sales(request):
    if request.method == "GET":
        ownerUsername = request.session['username']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        m = manager()
        cursor.execute("SELECT moment_id, serial, withdraw_account, listing_id, price, sold_timestamp FROM sold_listings WHERE owner_username=? AND status=?", (ownerUsername, "awaiting_moment"))

        return HttpResponse(json.dumps([{"imagePrefix": m.grab_moment_icon_by_id(item[0]),
            "listingId": item[3],
          "serial": item[1],
          "name": m.generate_moment_name_by_id(item[0]),
         "daysRemaining": (7 - math.floor((int(datetime.datetime.now().timestamp()) - int(item[5])) / 86400) ),
            "pendingBalance": str(round(float((float(item[4])*0.92)-0.3), 2)),
            "sendTo": item[2]} for item in cursor.fetchall()]),
            content_type="application/json")


def about_us(request):
    userAccountImage = "loggedOut"
    try:
        request.session['username']
        userAccountImage = "loggedIn"
    except:
        pass
    return render(request, "aboutus.html", {"userAccountImage": userAccountImage})

def terms_of_service(request):
    userAccountImage = "loggedOut"
    try:
        request.session['username']
        userAccountImage = "loggedIn"
    except:
        pass
    return render(request, "terms.html", {"userAccountImage": userAccountImage})

def privacy_policy(request):
    userAccountImage = "loggedOut"
    try:
        request.session['username']
        userAccountImage = "loggedIn"
    except:
        pass
    return render(request, "privacy.html", {"userAccountImage": userAccountImage})



def listing_page(request):
    try:
        request.session['username']
        return render(request, "listing-page.html")
    except:
        return render(request, "redirect.html", {"url": "/login/"})

def step_1_search_username_listings(request):
    if request.method == 'GET':
        username = request.GET['listing-username-input']
        r = requests.get("https://www.nbatopshot.com/user/@" + username + "/moments")
        rShaven = r.text[r.text.find("publicInfo"):r.text.rfind('"username"')]
        dapperId = rShaven[rShaven.find("\"dapperID\":\"") + len("\"dapperID\":\""):rShaven.find("\",\"username\":")]
        headers = {
            'accept': "*/*",
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://www.nbatopshot.com',
            'referer': 'https://www.nbatopshot.com/',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'x-id-token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik9EQkVPRGxDUXpWR1JVUXhSRUl5UkRRNE1rVTJNekkzTlVaR1JUWkNPRFJCUkRZNU9URXhOUSJ9.eyJnaXZlbl9uYW1lIjoiam9zaHVhIiwiZmFtaWx5X25hbWUiOiJkZWZlc2NoZSIsIm5pY2tuYW1lIjoiam9zaHVhLmRlZmVzY2hlIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYmxtIiwibmFtZSI6Impvc2h1YSBkZWZlc2NoZSIsInBpY3R1cmUiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vZGFwcGVyLXByb2ZpbGUtaWNvbnMvYXZhdGFyLWRlZmF1bHQucG5nIiwibG9jYWxlIjoiZW4iLCJ1cGRhdGVkX2F0IjoiMjAyMS0wMy0xMFQwOToyMTo1MS43NTZaIiwiZW1haWwiOiJqb3NodWEuZGVmZXNjaGVAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOi8vYXV0aC5tZWV0ZGFwcGVyLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExMTE3MTQ2NTc3ODE2MDAzNjg5NSIsImF1ZCI6Ijc1NktDdmlpdTZWQVMxbmJldGpVams2NE9jWjBZdjhyIiwiaWF0IjoxNjE1ODcwNDUwLCJleHAiOjE2MTU4NzEzNTB9.ctU2LLT1bLWZda34jaWDBtRvD-HZkuQwqZFLjelL69HoWw5HfLVwVlrwwlp19GbO1wO11H4x_J3Yb6WWVDzYpIBkT2tatwio0Ggxk9dPFXZaKY5ww8mefIuT2x5iINUrlRUOxAkvwZthDGU8yGEYHqoNz4T2hFKkTJ-oJtJCDZR2O_1j8duHnLK8qijMeuKYDKpvBPABsgVMFy8dzUcSZR_9y3X_rzl5wr5OuqdHYknYz0TYiuR10Y2Ufc8omSbyc4u6nhTqGWo3S3RNYNStOGN1H36EE1xutxo4w519InVCmuKMRfPE2TNCOmLGI0ooRxkvHcx7oppeHsNBWqevCg'
        }
        dataPayload = """{"operationName":"SearchMintedMoments","variables":{"sortBy":"ACQUIRED_AT_DESC","byOwnerDapperID":[\"""" + dapperId + """\"],"bySets":[],"bySeries":[],"bySetVisuals":[],"byPlayers":[],"byPlays":[],"byTeams":[],"byForSale":null,"searchInput":{"pagination":{"cursor":"","direction":"RIGHT","limit":35}}},"query":"query SearchMintedMoments($sortBy: MintedMomentSortType, $byOwnerDapperID: [String], $bySets: [ID], $bySeries: [ID], $bySetVisuals: [VisualIdType], $byPlayers: [ID], $byPlays: [ID], $byTeams: [ID], $byForSale: ForSaleFilter, $searchInput: BaseSearchInput!) {  searchMintedMoments(input: {sortBy: $sortBy, filters: {byOwnerDapperID: $byOwnerDapperID, bySets: $bySets, bySeries: $bySeries, bySetVisuals: $bySetVisuals, byPlayers: $byPlayers, byPlays: $byPlays, byTeams: $byTeams, byForSale: $byForSale}, searchInput: $searchInput}) {    data {      sortBy      filters {        byOwnerDapperID        bySets        bySeries        bySetVisuals        byPlayers        byPlays        byTeams        byForSale        __typename      }      searchSummary {        count {          count          __typename        }        pagination {          leftCursor          rightCursor          __typename        }        data {          ... on MintedMoments {            size            data {              ...MomentDetails              __typename            }            __typename          }          __typename        }        __typename      }      __typename    }    __typename  }}fragment MomentDetails on MintedMoment {  id  version  sortID  set {    id    flowName    flowSeriesNumber    setVisualId    __typename  }  setPlay {    ID    flowRetired    circulationCount    __typename  }  assetPathPrefix  play {    id    stats {      playerID      playerName      primaryPosition      teamAtMomentNbaId      teamAtMoment      dateOfMoment      playCategory      __typename    }    __typename  }  price  listingOrderID  flowId  owner {    dapperID    username    profileImageUrl    __typename  }  flowSerialNumber  forSale  __typename}"}"""
        r = requests.post("https://api.nbatopshot.com/marketplace/graphql?SearchMintedMoments", headers=headers,
                          data=dataPayload)
        user_moments = json.loads(r.text)['data']['searchMintedMoments']['data']['searchSummary']['data']
        json.dump(user_moments, open("cheeeeese.json", 'w'))

        momentDataStriped = [{"id": x["id"]+":"+str(x['flowSerialNumber'])+"/"+str(x['setPlay']['circulationCount']),
                              "idMAIN": x["setPlay"]["ID"]+":"+str(x['flowSerialNumber'])+"/"+str(x['setPlay']['circulationCount']),
                              "image": manager().grab_moment_icon_by_id(x["setPlay"]["ID"]),
                              "type": manager().grab_moment_by_id(x["setPlay"]["ID"])['play']['stats']['playCategory'] ,
                              "serial": str(x['flowSerialNumber'] )+ "/" + str(x['setPlay']['circulationCount']),
                              "name": x['play']['stats']['playerName'],
                              "set": manager().grab_moment_by_id(x["setPlay"]["ID"])['set']['flowName'],
                              "series": "Series " + str(manager().grab_moment_by_id(x["setPlay"]["ID"])['set']['flowSeriesNumber']),
                              "date": "%s-%s-%s" % (datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").year, datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").month, datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").day)} for x in user_moments['data']]
        momentDataStriped = {"user": momentDataStriped, 'status': True}
        if len(momentDataStriped) < 20:
            momentDataStriped = {'user': '', 'status': 'Account does not meet TopShot trading guidelines.'}
        return HttpResponse(json.dumps(momentDataStriped), content_type="application/json")

def step_2a_await_item(request):
    if request.method == 'POST':
        username = request.session["username"]
        momentId = request.POST['listing-moment-id']
        momentIdMAIN = request.POST['listing-moment-idMAIN']
        listingMomentJson = {
            "timestamp": str(datetime.datetime.now().timestamp()),
            "momentId": momentId,
            "momentIdMAIN": momentIdMAIN,
            "username": username,
            "received": False
        }
        currentStatus = json.loads(open("current_accounts_inuse.json","r").read())
        returnUsername = "No Available Accounts. Try again in a few minutes"
        for userStatus in currentStatus:
            momentAlreadyAwaiting = False
            for awaitingMoment in userStatus['inuse']:
                #5 Minute Timer on moments to be sent
                if awaitingMoment['momentId'] == listingMomentJson['momentId'] and float(listingMomentJson['timestamp']) - float(awaitingMoment['timestamp']) > 300:
                    m = manager()
                    if m.check_user_for_moment_by_id(userStatus['username'], momentId) == False:
                        returnUsername = userStatus['username']
                        userStatus['inuse'].append(listingMomentJson)
                        break
                if awaitingMoment['momentId'] == listingMomentJson['momentId'] and float(listingMomentJson['timestamp']) - float(awaitingMoment['timestamp']) <= 300:
                    momentAlreadyAwaiting = True
            if momentAlreadyAwaiting == False:
                m = manager()
                if m.check_user_for_moment_by_id(userStatus['username'], momentId) == True:
                    returnUsername = userStatus['username']
                    userStatus['inuse'].append(listingMomentJson)
                    break
        json.dump(currentStatus, open("current_accounts_inuse.json", "w"))
        listingMomentJson['sendingUsername'] = returnUsername
        if returnUsername != "No Available Accounts. Try again in a few minutes":
            request.session['awaitJson'] = listingMomentJson
        respJson = {
            'name': returnUsername,
        }
        return HttpResponse(json.dumps(respJson), content_type="application/json")

def step_2b_await_item(request):
    if request.method == "GET":
        username = request.session["username"]
        waitingMoment = request.session['awaitJson']
        username = waitingMoment['sendingUsername']
        r = requests.get("https://www.nbatopshot.com/user/@" + username + "/moments")
        rShaven = r.text[r.text.find("publicInfo"):r.text.rfind('"username"')]
        dapperId = rShaven[rShaven.find("\"dapperID\":\"") + len("\"dapperID\":\""):rShaven.find("\",\"username\":")]
        headers = {
            'accept': "*/*",
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://www.nbatopshot.com',
            'referer': 'https://www.nbatopshot.com/',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'x-id-token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik9EQkVPRGxDUXpWR1JVUXhSRUl5UkRRNE1rVTJNekkzTlVaR1JUWkNPRFJCUkRZNU9URXhOUSJ9.eyJnaXZlbl9uYW1lIjoiam9zaHVhIiwiZmFtaWx5X25hbWUiOiJkZWZlc2NoZSIsIm5pY2tuYW1lIjoiam9zaHVhLmRlZmVzY2hlIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYmxtIiwibmFtZSI6Impvc2h1YSBkZWZlc2NoZSIsInBpY3R1cmUiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vZGFwcGVyLXByb2ZpbGUtaWNvbnMvYXZhdGFyLWRlZmF1bHQucG5nIiwibG9jYWxlIjoiZW4iLCJ1cGRhdGVkX2F0IjoiMjAyMS0wMy0xMFQwOToyMTo1MS43NTZaIiwiZW1haWwiOiJqb3NodWEuZGVmZXNjaGVAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOi8vYXV0aC5tZWV0ZGFwcGVyLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExMTE3MTQ2NTc3ODE2MDAzNjg5NSIsImF1ZCI6Ijc1NktDdmlpdTZWQVMxbmJldGpVams2NE9jWjBZdjhyIiwiaWF0IjoxNjE1ODcwNDUwLCJleHAiOjE2MTU4NzEzNTB9.ctU2LLT1bLWZda34jaWDBtRvD-HZkuQwqZFLjelL69HoWw5HfLVwVlrwwlp19GbO1wO11H4x_J3Yb6WWVDzYpIBkT2tatwio0Ggxk9dPFXZaKY5ww8mefIuT2x5iINUrlRUOxAkvwZthDGU8yGEYHqoNz4T2hFKkTJ-oJtJCDZR2O_1j8duHnLK8qijMeuKYDKpvBPABsgVMFy8dzUcSZR_9y3X_rzl5wr5OuqdHYknYz0TYiuR10Y2Ufc8omSbyc4u6nhTqGWo3S3RNYNStOGN1H36EE1xutxo4w519InVCmuKMRfPE2TNCOmLGI0ooRxkvHcx7oppeHsNBWqevCg'
        }
        dataPayload = """{"operationName":"SearchMintedMoments","variables":{"sortBy":"ACQUIRED_AT_DESC","byOwnerDapperID":[\"""" + dapperId + """\"],"bySets":[],"bySeries":[],"bySetVisuals":[],"byPlayers":[],"byPlays":[],"byTeams":[],"byForSale":null,"searchInput":{"pagination":{"cursor":"","direction":"RIGHT","limit":12}}},"query":"query SearchMintedMoments($sortBy: MintedMomentSortType, $byOwnerDapperID: [String], $bySets: [ID], $bySeries: [ID], $bySetVisuals: [VisualIdType], $byPlayers: [ID], $byPlays: [ID], $byTeams: [ID], $byForSale: ForSaleFilter, $searchInput: BaseSearchInput!) {  searchMintedMoments(input: {sortBy: $sortBy, filters: {byOwnerDapperID: $byOwnerDapperID, bySets: $bySets, bySeries: $bySeries, bySetVisuals: $bySetVisuals, byPlayers: $byPlayers, byPlays: $byPlays, byTeams: $byTeams, byForSale: $byForSale}, searchInput: $searchInput}) {    data {      sortBy      filters {        byOwnerDapperID        bySets        bySeries        bySetVisuals        byPlayers        byPlays        byTeams        byForSale        __typename      }      searchSummary {        count {          count          __typename        }        pagination {          leftCursor          rightCursor          __typename        }        data {          ... on MintedMoments {            size            data {              ...MomentDetails              __typename            }            __typename          }          __typename        }        __typename      }      __typename    }    __typename  }}fragment MomentDetails on MintedMoment {  id  version  sortID  set {    id    flowName    flowSeriesNumber    setVisualId    __typename  }  setPlay {    ID    flowRetired    circulationCount    __typename  }  assetPathPrefix  play {    id    stats {      playerID      playerName      primaryPosition      teamAtMomentNbaId      teamAtMoment      dateOfMoment      playCategory      __typename    }    __typename  }  price  listingOrderID  flowId  owner {    dapperID    username    profileImageUrl    __typename  }  flowSerialNumber  forSale  __typename}"}"""
        r = requests.post("https://api.nbatopshot.com/marketplace/graphql?SearchMintedMoments", headers=headers,
                          data=dataPayload)
        user_moments = json.loads(r.text)['data']['searchMintedMoments']['data']['searchSummary']['data']
        momentDataStriped = [
            {"id": x["id"] + ":" + str(x['flowSerialNumber']) + "/" + str(x['setPlay']['circulationCount']),
             "idMain":x["setPlay"]["ID"] + ":" + str(x['flowSerialNumber']) + "/" + str(x['setPlay']['circulationCount']),
             "assetPrefix": x['assetPathPrefix'], "serialNumber": x['flowSerialNumber'],
             "serialNumberCap": x['setPlay']['circulationCount'],
             "name": x['play']['stats']['playerName'] + " - " + x['set']['flowName'] + " (Series " + str(
                 x['set']['flowSeriesNumber']) + ")",
             "date": "%s-%s-%s" % (
             datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").year,
             datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").month,
             datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").day)} for x in
            user_moments['data']]

        if float(datetime.datetime.now().timestamp()) - float(waitingMoment['timestamp']) > 300:
            return HttpResponse(json.dumps({"received": False,
                                            "message": "Time limit ran out and moment was not received. Please try again",
                                            "await": False}),
                                content_type="application/json")
        for moment in momentDataStriped:
            if moment['id'] == waitingMoment['momentId']:
                print("Moment found")

                waitingMoment = request.session['awaitJson']
                print(waitingMoment)
                awaitingUsername = waitingMoment['sendingUsername']
                del waitingMoment['sendingUsername']

                
                currentAccounts = json.load(open("current_accounts_inuse.json", "r"))

                
                for account in currentAccounts:
                    if account['username'] == awaitingUsername:
                        for moment in account['inuse']:
                            if moment['momentId'] == waitingMoment['momentId']:
                                account['inuse'].remove(waitingMoment)
                
                json.dump(currentAccounts, open("current_accounts_inuse.json", "w"))
                waitingMoment['sendingUsername'] = awaitingUsername

                waitingMoment['received'] = True
                print("1111111")
                print(request.session['awaitJson'])
                return HttpResponse(json.dumps({"received": True,
                                                "message": "The moment was received successfully.",
                                                "await": False}),
                                    content_type="application/json")

        else:
            return HttpResponse(json.dumps({"received": False,
                                            "message": "",
                                            "await": True}),
                                content_type="application/json")

def step_3_finalize_price(request):
    if request.method == "POST":
        listPrice = request.POST['finalPrice']
        momentId = request.POST['momentId']
        distinctMomentId = request.POST['distinctMomentId']
        owner = request.session['username']
        try:
            if int(listPrice) < 1 or int(listPrice) > 9999:
                return HttpResponse(json.dumps({'status': 'Price Invalid. Must be greater than $1 and less than $10,000.'}),
                                    content_type="application/json")
        except:
            return HttpResponse(json.dumps({'status': 'Price Invalid'}),
                                content_type="application/json")
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT distinct_moment_id from listings WHERE distinct_moment_id=?", (distinctMomentId.split(":")[0]))
        if len(cursor.fetchall()) > 0:
            return HttpResponse(json.dumps({'status': 'Moment is already currently listed. Contact support if you believe this is a mistake.'}),
                                content_type="application/json")
        insertData = {
            "momentId": momentId.split(":")[0],
            "distinctMomentId": distinctMomentId.split(":")[0],
            "price": str(int(listPrice)),
            "owner_username": owner,
            "serial": str(momentId.split(":")[1].split("/")[0]),
            "listingId": ''.join([random.choice(string.ascii_uppercase+string.digits) for x in range(15)])
        }

        cursor.execute("SELECT listing_id from listings WHERE listing_id=?", (insertData['listingId']))
        if len(cursor.fetchall()) > 0:
            insertData['listingId'] = ''.join([random.choice(string.ascii_uppercase+string.digits) for x in range(15)])
        cursor.execute("INSERT INTO listings (moment_id, distinct_moment_id, price, owner_username, serial, listing_id, listed_timestamp) VALUES (?,?,?,?,?,?,?)",
                       (insertData['momentId'],insertData['distinctMomentId'],insertData['price'],insertData['owner_username'],insertData['serial'],insertData['listingId'],int(datetime.datetime.now().timestamp())))
        cnxn.commit()
        cnxn.close()
        request.session['awaitJson'] = {}
        return HttpResponse(json.dumps({'status': 'success',
                                       'momentId': insertData['momentId']}),
                            content_type="application/json")

def update_listing_price(request):
    if request.method == "POST":
        listingId = request.POST['listingId']
        newPrice = int(request.POST['newPrice'])
        owner = request.session['username']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("UPDATE listings SET price=? WHERE owner_username=? AND listing_id=?", (newPrice, owner, listingId))
        cnxn.commit()
        cnxn.close()
        return HttpResponse(json.dumps({
            'status': 'success'
        }),
        content_type="application/json")

def remove_listing_and_return_moment(request):
    if request.method == "POST":
        listingId = request.POST['listingId']
        owner = request.session['username']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT moment_id, price, serial, listed_timestamp,  from listings WHERE owner_username=? AND listing_id=?", (owner, listingId))
        listingInfo = cursor.fetchone()
        cursor.execute("DELETE FROM listings WHERE owner_username=? AND listing_id=?", (owner, listingId))
        cnxn.commit()
        cursor.execute("INSERT INTO cancelled_listings (moment_id, price, owner_username, serial, listing_id, listed_timestamp,"
                       "cancelled_timestamp, status) VALUES (?,?,?,?,?,?,?,?)",
                       (listingInfo[0], listingInfo[1], owner, listingInfo[2], listingId, listingInfo[3], str(int(datetime.datetime.now().timestamp())),
                        "complete"))
        cnxn.commit()
        cnxn.close()
        sale_cancelled
        return HttpResponse(json.dumps({"status": "success"}), content_type="application/json")

def wallet_withdraw(request):
    if request.method == "POST":
        try:
            withdrawAmount = float(request.POST['withdrawAmount'])
            withdrawEmail = request.POST['withdrawEmail']
            if bool(re.match(r'.+[@].+[.].+', withdrawEmail)) == False or withdrawAmount < 10:
                return HttpResponse(json.dumps({'status': 'Invalid withdraw information'}),
                                    content_type="application/json")
            ownerAccount = request.session['username']
        except:
            return HttpResponse(json.dumps({'status': 'Invalid withdraw information'}), content_type="application/json")
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT wallet_balance FROM users WHERE username=?", (ownerAccount))
        currentBalance = float(cursor.fetchone()[0])
        newBalance = currentBalance - withdrawAmount
        if newBalance >= 0:
            cursor.execute("UPDATE users SET wallet_balance=? WHERE username=?", (newBalance, ownerAccount))
            withdrawId = ''.join([random.choice(string.ascii_uppercase+string.digits) for x in range(15)])
            cursor.execute("INSERT INTO withdraw_requests (owner_account, withdraw_amount, withdraw_email, withdraw_timestamp, status, id, notes) VALUES (?,?,?,?,?,?,?)",
                           (ownerAccount, withdrawAmount, withdrawEmail, str(int(datetime.datetime.now().timestamp())),
                            "awaiting_withdraw",
                            withdrawId,
                            f"Withdraw from user. {currentBalance} - {withdrawAmount} = {newBalance}"))
            cnxn.commit()
            cnxn.close()
            e = emailer()
            e.wallet_withdraw(ownerAccount, withdrawId)
            return HttpResponse(json.dumps({'status': 'success'}), content_type="application/json")
        else:
            return HttpResponse(json.dumps({'status': 'insufficient balance'}), content_type="application/json")

def promoted_listings(request):
    if request.method == "GET":
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT DISTINCT TOP 20 moment_id, price, serial FROM listings")
        m = manager()
        respJson = [{"image": m.grab_moment_icon_by_id(item[0]),
        "id": item[0],
          "name": m.grab_moment_by_id(item[0])['play']['stats']['playerName'],
         "series": "Series "+str(m.grab_moment_by_id(item[0])['set']['flowSeriesNumber']),
         "type": m.grab_moment_by_id(item[0])['play']['stats']['playCategory'] ,
         "set": m.grab_moment_by_id(item[0])['set']['flowName'],
          "date": "%s-%s-%s" % (datetime.datetime.strptime(m.grab_moment_by_id(item[0])['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").year, datetime.datetime.strptime(m.grab_moment_by_id(item[0])['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").month, datetime.datetime.strptime(m.grab_moment_by_id(item[0])['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").day),
          "serial": str(item[2])+"/"+str(m.grab_moment_by_id(item[0])['circulationCount']),
          "price": item[1]} for item in cursor.fetchall()]
        cnxn.close()
        return HttpResponse(json.dumps(respJson), content_type="application/json")

def mark_as_shipped(request):
    if request.method == "GET":
        owner = request.session['username']
        listingId = request.GET['listingId']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT withdraw_account, moment_id, distinct_moment_id, serial, price, paypal_transaction, status, sold_timestamp, owner_username, buyer_username, order_id FROM sold_listings WHERE owner_username=? AND listing_id=?", (owner, listingId))
        withdraw_account, moment_id, distinct_moment_id, serial, price, paypal_transaction, status, sold_timestamp, owner, buyer, order_id = cursor.fetchone()
        if status == "awaiting_moment":
            daysRemaining = 7 - math.floor((int(datetime.datetime.now().timestamp()) - int(sold_timestamp)) / 86400)

            if manager().check_user_for_moment_by_id_specific(withdraw_account,
                                                               distinct_moment_id + ":" + serial + "/" + str(
                                                                   manager().grab_moment_by_id(moment_id)[
                                                                       'circulationCount'])):
                cursor.execute("UPDATE sold_listings SET status='sent' WHERE owner_username=? AND listing_id=?", (owner, listingId))
                cursor.execute("UPDATE users SET wallet_balance=convert (float, wallet_balance)+? WHERE username=?", (float((float(price)*0.92)-0.3)), owner)
                cnxn.commit()
                cnxn.close()
                e = emailer()
                e.sale_completed(owner, buyer, order_id)
                return HttpResponse(json.dumps({'status': 'success'}), content_type="application/json")
            else:
                return HttpResponse(json.dumps({'status': 'Moment not sent'}), content_type="application/json")
        else:
            cnxn.close()
            return HttpResponse(json.dumps({'status': 'Moment not awaiting to be sent'}), content_type="application/json")

def password_reset_request_page(request):
    return render(request, "reset-request.html")

def password_reset_request(request):
    if request.method == "GET":
        emailReq = request.GET['email']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT username FROM users WHERE email=?", (emailReq))
        try:
            username = cursor.fetchone()[0]
        except:
            return HttpResponse(json.dumps({'status': 'Email is invalid'}),
                                content_type="application/json")
        cnxn.close()
        requestId = "".join([random.choice(string.ascii_uppercase+string.digits) for x in range(30)])
        r = json.load(open(r"C:\Users\joshu\OneDrive\Desktop\DigiShop - v2\digishop\password_changes.json", "r"))
        r.insert(0, {"username": username, "timestamp": int(datetime.datetime.now().timestamp()),
                                                               "id": requestId})
        json.dump(r, open(r"C:\Users\joshu\OneDrive\Desktop\DigiShop - v2\digishop\password_changes.json", "w"))
        sg = sendgrid.SendGridAPIClient(api_key="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")
        TEMPLATE_ID = "d-3da3afeab44e401aa2d57099ecf9687c"
        FROM_EMAIL = "donotreply@digishop.gg"
        TO_EMAILS = [(emailReq)]
        message = sendgrid.Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAILS)
        # pass custom values for our HTML placeholders
        message.dynamic_template_data = {
            'resetToken': requestId,
        }
        message.template_id = TEMPLATE_ID
        sg.send(message)
        return HttpResponse(json.dumps({'status': 'success'}),
                            content_type="application/json")


def password_reset(request):
    if request.method == "GET":
        requestId = request.GET['token']
        ownerj = json.load(open(r"C:\Users\joshu\OneDrive\Desktop\DigiShop - v2\digishop\password_changes.json", "r"))
        for o in ownerj:
            if o['id'] == requestId:
                if int(datetime.datetime.now().timestamp()) - int(o['timestamp']) <= 600:
                    owner = o['username']
                    break
        return render(request, "reset-password.html", {"username": owner, "requestId": requestId})

def password_reset_change(request):
    if request.method == "GET":
        requestId = request.GET['requestId']
        newpassword = request.GET['newpassword']
        if len(newpassword) < 6:
            return HttpResponse(json.dumps({'status': 'Password is invalid.'}),
                                content_type="application/json")
        ownerj = json.load(open(r"C:\Users\joshu\OneDrive\Desktop\DigiShop - v2\digishop\password_changes.json", "r"))
        test = False
        for o in ownerj:
            if o['id'] == requestId and int(o['timestamp']) - int(datetime.datetime.now().timestamp() > 600):
                owner = o['username']
                test = True
                break
        if test == False:
            return HttpResponse(json.dumps({'status': 'Request is invalid or has expired'}),
                                content_type="application/json")
        else:
            cnxn = pyodbc.connect(
                'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
            cursor = cnxn.cursor()
            cursor.execute("UPDATE users SET password=? WHERE username=?", (newpassword, owner))
            cnxn.commit()
            cnxn.close()
            return HttpResponse(json.dumps({'status': 'success'}),
                                content_type="application/json")

def live_market(request):
    try:
        request.session['username']
        return render(request, "live-market.html", {"userAccountImage": "loggedIn"})
    except:
        return render(request, "live-market.html", {
        "userAccountImage": "loggedOut"})

def live_market_moments(request):
    if request.method == "GET":
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()

        if request.GET['sortBy'] == "priceAsc":
            cursor.execute("SELECT moment_id, MIN(price) as min_price FROM listings GROUP BY moment_id ORDER BY min_price ASC")
        elif request.GET['sortBy'] == "priceDesc":
            cursor.execute("SELECT moment_id, MIN(price) as min_price FROM listings GROUP BY moment_id ORDER BY min_price DESC")
        else:
            cursor.execute("SELECT moment_id, MIN(price) FROM listings GROUP BY moment_id")
        initList = [[item[0], item[1]] for item in cursor.fetchall()]
        finalList = []
        for item in initList:
            momentData = manager().grab_moment_by_id(item[0])
            #Going through filters
            #First filter is team
            if request.GET['team'].lower() not in momentData['play']['stats']['teamAtMoment'].lower():
                continue
            #Second filter is player name
            if request.GET['player'].lower() not in momentData['play']['stats']['playerName'].lower():
                continue
            #Third filter is set
            if request.GET['set'].lower() not in momentData['set']['flowName'].lower():
                continue
            #Fourth filter is series
            if request.GET['series'] != "-" and int(request.GET['series']) != int(momentData['set']['flowSeriesNumber']):
                continue
            #Fifth filter is price low
            try:
                price = int(request.GET['priceLow'])
                if price > int(item[1]):
                    continue
            except:
                pass
            #Sixth filter is price high
            try:
                price = int(request.GET['priceHigh'])
                if price < int(item[1]):
                    continue
            except:
                pass

            finalList.append({'id': item[0],
                              'name': momentData['play']['stats']['playerName'],
                              'image': manager().grab_moment_icon_by_id(item[0]),
                              'serial': "Max. Serial: "+str(momentData['circulationCount']),
                              'type': momentData['play']['stats']['playCategory'],
                              'date': datetime.datetime.fromisoformat(momentData['play']['stats']['dateOfMoment'][:-1]).strftime('%m-%d-%Y'),
                              'set': momentData['set']['flowName'],
                              'series': "Series "+str(momentData['set']['flowSeriesNumber']),
                              'minPrice': str(item[1]),
                              'team': momentData['play']['stats']['teamAtMoment']})
        moreAvailable = False
        if len(finalList) > ((int(request.GET['page']) - 1) * 50) + 50:
            moreAvailable = True
        return HttpResponse(json.dumps({'more': moreAvailable, 'moments': finalList[
                                                                          ((int(request.GET['page']) - 1) * 50):((int(
                                                                              request.GET['page']) - 1) * 50) + 49]}),
                            content_type="application/json")

