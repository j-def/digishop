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
        if len(password) < 6:
            return HttpResponse("Password does not meet requirements.")
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT username from users WHERE username=?", username)
        if cursor.fetchone() == None:
            cursor.execute("INSERT INTO users (username, password, wallet_balance) VALUES(?,?,'0')", (username, password))
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
        responseJson = {
            "setName": momentData['set']['flowName'],
            "seriesNo": momentData['set']['flowSeriesNumber'],
            "playerTeam": momentData['play']['stats']['teamAtMoment'],
            "playCategory": momentData['play']['stats']['playCategory'],
            "imagePrefix": momentData['assetPathPrefix'],
            "circulationCount": momentData['circulationCount']
        }
        print(responseJson['imagePrefix'])
        return HttpResponse(json.dumps(responseJson), content_type="application/json")

def listings_table(request):
    import math
    if request.method == "GET":
        momentId = request.GET['momentId']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT * from listings WHERE moment_id=? ORDER BY serial ASC", momentId)
        respJson = [{"serial": item[3], "price": item[1], "listing": item[4], "daysListed": math.floor((int(datetime.datetime.now().timestamp())-int(item[5]))/(24*60*60))} for item in cursor.fetchall()]
        cnxn.close()
        return HttpResponse(json.dumps(respJson), content_type="application/json")

def sold_listings_table(request):
    if request.method == "GET":
        momentId = request.GET['momentId']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT serial, price, sold_timestamp from sold_listings WHERE moment_id=? ORDER BY serial ASC", momentId)
        respJson = [{"serial": item[0], "price": item[1], "date": datetime.datetime.utcfromtimestamp(int(item[2])).strftime('%Y-%m-%d')} for item in cursor.fetchall()]
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
        momentId, price, ownerUsername, serial, listingId, listingTimestamp = cursor.fetchone()
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
        momentId, price, ownerUsername, serial, listingId, listingTimestamp = cursor.fetchone()
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
        momentId, price, ownerUsername, serial, listingId, listingTimestamp = cursor.fetchone()
        cnxn.close()
        m = manager()
        rjson = m.grab_moment_by_id(momentId)
        print(rjson)
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
            cursor.execute("SELECT moment_id, price, owner_username, serial, listed_timestamp FROM listings WHERE listing_id=?", (request.GET['listingId']))
            moment_id, price, owner_username, serial, listed_timestamp = cursor.fetchone()
            cursor.execute("SELECT wallet_balance FROM users WHERE username=?", (owner_username))
            balance = float(cursor.fetchone()[0])
            newBalance = balance + ((float(price) * 0.92) - 0.30)
            cursor.execute("UPDATE users SET wallet_balance=? WHERE username=?", (newBalance, owner_username))
            cursor.execute("DELETE FROM listings WHERE listing_id=?", (request.GET['listingId']))
            cursor.execute("INSERT INTO sold_listings (moment_id, price, owner_username, serial, listing_id,"
                           "listed_timestamp, sold_timestamp, buyer_username, paypal_transaction, status, withdraw_account) "
                           "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (moment_id, price, owner_username, serial, request.GET['listingId'], listed_timestamp, str(int(datetime.datetime.now().timestamp())), buyer, request.GET["paypalPaymentId"], "awaiting_moment", sendTo))
            cnxn.commit()
            q = queue()
            if q.send_moment(request.GET['listingId'], moment_id, sendTo, serial, buyer, listed_timestamp):
                return HttpResponse(json.dumps({"status": "success"}),
                                content_type="application/json")
            else:
                return HttpResponse(json.dumps({"status": "Payment successful, but error sending moment. Contact Support."}),
                                    content_type="application/json")
            cnxn.close()
            q = queue()

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

def retrieve_account_sold_data(request):
    if request.method == "GET":
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        m = manager()

        cursor.execute("SELECT moment_id, price, serial, listing_id, CASE WHEN owner_username=? THEN 'Sale' WHEN buyer_username=? THEN 'Purchase' END AS owner FROM sold_listings WHERE owner_username=? OR buyer_username=?", (request.session['username'],request.session['username'],request.session['username'],request.session['username']))
        userListings = [{"momentId": listing[0], "price": listing[1], "serial": listing[2], "listingId": listing[3], "momentImage": m.grab_moment_icon_by_id(listing[0]), "momentName": m.generate_moment_name_by_id(listing[0]), "transactionType": listing[4]} for listing in cursor.fetchall()]
        return HttpResponse(json.dumps(userListings), content_type="application/json")

def retrieve_account_pending_withdraws(request):
    if request.method == "GET":
        ownerUsername = request.session['username']
        q = queue()
        m = manager()
        return HttpResponse(json.dumps([{"imagePrefix": m.grab_moment_icon_by_id(item['momentId']),
          "serial": item['momentSerial'],
          "name": m.generate_moment_name_by_id(item['momentId']),
            "sendTo": item['withdrawAccount']} for item in q.grab_pending_withdraws_by_username(ownerUsername)]),
            content_type="application/json")


def update_user_email(request):
    if request.method == "GET":
        newEmail = request.GET['email']
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("UPDATE users SET email=? WHERE username=?", (newEmail, request.session['username']))
        cnxn.commit()
        cnxn.close()
        return HttpResponse("success")

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
        dataPayload = """{"operationName":"SearchMintedMoments","variables":{"sortBy":"ACQUIRED_AT_DESC","byOwnerDapperID":[\"""" + dapperId + """\"],"bySets":[],"bySeries":[],"bySetVisuals":[],"byPlayers":[],"byPlays":[],"byTeams":[],"byForSale":null,"searchInput":{"pagination":{"cursor":"","direction":"RIGHT","limit":12}}},"query":"query SearchMintedMoments($sortBy: MintedMomentSortType, $byOwnerDapperID: [String], $bySets: [ID], $bySeries: [ID], $bySetVisuals: [VisualIdType], $byPlayers: [ID], $byPlays: [ID], $byTeams: [ID], $byForSale: ForSaleFilter, $searchInput: BaseSearchInput!) {  searchMintedMoments(input: {sortBy: $sortBy, filters: {byOwnerDapperID: $byOwnerDapperID, bySets: $bySets, bySeries: $bySeries, bySetVisuals: $bySetVisuals, byPlayers: $byPlayers, byPlays: $byPlays, byTeams: $byTeams, byForSale: $byForSale}, searchInput: $searchInput}) {    data {      sortBy      filters {        byOwnerDapperID        bySets        bySeries        bySetVisuals        byPlayers        byPlays        byTeams        byForSale        __typename      }      searchSummary {        count {          count          __typename        }        pagination {          leftCursor          rightCursor          __typename        }        data {          ... on MintedMoments {            size            data {              ...MomentDetails              __typename            }            __typename          }          __typename        }        __typename      }      __typename    }    __typename  }}fragment MomentDetails on MintedMoment {  id  version  sortID  set {    id    flowName    flowSeriesNumber    setVisualId    __typename  }  setPlay {    ID    flowRetired    circulationCount    __typename  }  assetPathPrefix  play {    id    stats {      playerID      playerName      primaryPosition      teamAtMomentNbaId      teamAtMoment      dateOfMoment      playCategory      __typename    }    __typename  }  price  listingOrderID  flowId  owner {    dapperID    username    profileImageUrl    __typename  }  flowSerialNumber  forSale  __typename}"}"""
        r = requests.post("https://api.nbatopshot.com/marketplace/graphql?SearchMintedMoments", headers=headers,
                          data=dataPayload)
        user_moments = json.loads(r.text)['data']['searchMintedMoments']['data']['searchSummary']['data']
        print(user_moments)

        momentDataStriped = [{"id": x["id"]+":"+str(x['flowSerialNumber'])+"/"+str(x['setPlay']['circulationCount']),"idMAIN": x["setPlay"]["ID"]+":"+str(x['flowSerialNumber'])+"/"+str(x['setPlay']['circulationCount']), "assetPrefix": x['assetPathPrefix'], "serialNumber": x['flowSerialNumber'],
                              "serialNumberCap": x['setPlay']['circulationCount'], "name": x['play']['stats']['playerName']+" - "+x['set']['flowName']+" (Series "+str(x['set']['flowSeriesNumber'])+")",
                              "date": "%s-%s-%s" % (datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").year, datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").month, datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").day)} for x in user_moments['data']]
        momentDataStriped = {"user": momentDataStriped}
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
        print(user_moments)
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
        try:
            if int(listPrice) < 1:
                return HttpResponse(json.dumps({'status': 'Price Invalid'}),
                                    content_type="application/json")
        except:
            return HttpResponse(json.dumps({'status': 'Price Invalid'}),
                                content_type="application/json")
        owner = request.session['username']
        m = manager()
        if m.check_user_for_moment_by_id(request.session['awaitJson']['sendingUsername'], request.session['awaitJson']['momentId']) == False:
            return HttpResponse(json.dumps({'status': 'Item Never Received'}),
                                content_type="application/json")
        insertData = {
            "momentId": request.session['awaitJson']['momentIdMAIN'].split(":")[0],
            "price": str(int(listPrice)),
            "owner_username": owner,
            "serial": str(request.session['awaitJson']['momentId'].split(":")[1].split("/")[0]),
            "listingId": ''.join([random.choice(string.ascii_uppercase+string.digits) for x in range(15)])
        }
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT listing_id from listings WHERE listing_id=?", (insertData['listingId']))
        if len(cursor.fetchall()) > 0:
            insertData['listingId'] = ''.join([random.choice(string.ascii_uppercase+string.digits) for x in range(15)])
        cursor.execute("INSERT INTO listings (moment_id, price, owner_username, serial, listing_id, listed_timestamp) VALUES (?,?,?,?,?,?)",
                       (insertData['momentId'],insertData['price'],insertData['owner_username'],insertData['serial'],insertData['listingId'],int(datetime.datetime.now().timestamp())))
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
        withdrawUser = request.POST['withdrawUser']
        owner = request.session['username']
        r = requests.get("https://www.nbatopshot.com/user/@" + withdrawUser + "/moments")
        rShaven = r.text[r.text.find("publicInfo"):r.text.rfind('"username"')]
        dapperId = rShaven[rShaven.find("\"dapperID\":\"") + len("\"dapperID\":\""):rShaven.find("\",\"username\":")]
        if len(withdrawUser) < 3 or dapperId == "":
            return HttpResponse(json.dumps({"status": "Invalid TopShot Username. Try a new one."}), content_type="application/json")
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
        cursor = cnxn.cursor()
        cursor.execute("SELECT moment_id, price, serial, listed_timestamp from listings WHERE owner_username=? AND listing_id=?", (owner, listingId))
        listingInfo = cursor.fetchone()
        q = queue()
        print(q.send_moment(listingId, listingInfo[0], withdrawUser, listingInfo[2], request.session['username'], listingInfo[3]))
        cursor.execute("DELETE FROM listings WHERE owner_username=? AND listing_id=?", (owner, listingId))
        cnxn.commit()
        cursor.execute("INSERT INTO cancelled_listings (moment_id, price, owner_username, serial, listing_id, listed_timestamp,"
                       "cancelled_timestamp, status, withdraw_account) VALUES (?,?,?,?,?,?,?,?,?)",
                       (listingInfo[0], listingInfo[1], owner, listingInfo[2], listingId, listingInfo[3], str(int(datetime.datetime.now().timestamp())),
                        "awaiting_withdraw", withdrawUser))
        cnxn.commit()
        cnxn.close()
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
            cnxn.commit()
            cnxn.close()
            q = queue()
            q.send_money(ownerAccount, str(withdrawAmount), withdrawEmail)
            return HttpResponse(json.dumps({'status': 'success'}), content_type="application/json")
        else:
            return HttpResponse(json.dumps({'status': 'insufficient balance'}), content_type="application/json")


