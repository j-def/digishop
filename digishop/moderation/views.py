from django.shortcuts import render, HttpResponse
import json
from datetime import timezone, datetime
import random
import pyodbc
import string
from digishop_emailer import emailer

ADMIN_LIST = ["jdefesche"]
dbserver = 'REGCONSERVER1'
dbdatabase = 'digishop'
dbusername = 'belotecainventory'
dbpassword = 'belotecainventory'


def home(request):
    if request.session["username"] in ADMIN_LIST:
        return render(request, "admin-home.html")
    else:
        return render(request, "redirect.html", {'url':'/'})

def grab_todo_list(request):
    if request.session["username"] in ADMIN_LIST:
        todoJson = json.load(open("todo.json", "r"))
        respJson = []
        for todo in todoJson:
            respJson.append({"title": todo['title'], "status": todo['status'], "id": todo["id"]})
        return HttpResponse(json.dumps(respJson), content_type="application/json")
    else:
        return render(request, "redirect.html", {'url':'/'})

def discussion_page(request):
    if request.method == "GET":
        discussionId = request.GET["id"]
        if request.session["username"] in ADMIN_LIST:
            todoJson = json.load(open("todo.json", "r"))
            for todo in todoJson:
                if todo['id'] == discussionId:
                    discussionTitle = todo['title']
            return render(request, "admin-discussion.html", {"discussionId": discussionId, "discussionTitle": discussionTitle} )
        else:
            return render(request, "redirect.html", {'url':'/'})

def get_discussion_messages(request):
    if request.method == "GET":
        id = request.GET["discussionId"]
        if request.session["username"] in ADMIN_LIST:
            todoJson = json.load(open("todo.json", "r"))
            respJson = []
            for todo in todoJson:
                if todo["id"] == id:
                    respJson = todo['discussion']
            respJson.reverse()
            return HttpResponse(json.dumps(respJson), content_type="application/json")

def add_discussion_message(request):
    if request.method == "GET":
        if request.session["username"] in ADMIN_LIST:
            timestamp = str(int(datetime.now(tz=timezone.utc).timestamp() * 1000))
            message = request.GET["message"]
            sender = request.session["username"]
            discussionId = request.GET["discussionId"]
            todoJson = json.load(open("todo.json", "r"))
            for todo in todoJson:
                if todo['id'] == discussionId:
                    discussionResults = todo["discussion"]
                    discussionResults.append({"username": sender, "message": message, "timestamp": timestamp})
                    todo["discussion"] = discussionResults
            json.dump(todoJson, open("todo.json","w"))
            discussionResults.reverse()
            return HttpResponse(json.dumps(discussionResults), content_type="application/json")
        else:
            return render(request, "redirect.html", {'url':'/'})

def create_discussion(request):
    if request.method == "GET":
        if request.session["username"] in ADMIN_LIST:
            timestamp = str(int(datetime.now(tz=timezone.utc).timestamp() * 1000))
            title = request.GET["title"]
            sender = request.session["username"]
            discussionId = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            todoJson = json.load(open("todo.json", "r"))
            todoJson.append({
                "title": title,
                "created_timestamp": timestamp,
                "id": discussionId,
                "status": "open",
                "created_by": sender,
                "discussion": []
            })
            json.dump(todoJson, open("todo.json", "w"))

            return HttpResponse("Success")

def withdraw_table(request):
    if request.session["username"] in ADMIN_LIST:
        return render(request, "withdraw-table.html")

def grab_withdraw_requests(request):
    if request.method == "GET":
        if request.session["username"] in ADMIN_LIST:
            cnxn = pyodbc.connect(
                'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
            cursor = cnxn.cursor()
            cursor.execute("SELECT owner_account, withdraw_amount, withdraw_email, withdraw_timestamp, id FROM withdraw_requests WHERE status='awaiting_withdraw'", )
            respJson = [{"username": item[0], "amount": float(item[1]), "email": item[2], "id": item[4]} for item in cursor.fetchall()]
            return HttpResponse(json.dumps(respJson), content_type="application/json")

def mark_withdraw_as_sent(request):
    if request.method == "GET":
        if request.session["username"] in ADMIN_LIST:
            markid = request.GET["markId"]
            cnxn = pyodbc.connect(
                'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
            cursor = cnxn.cursor()
            cursor.execute("UPDATE withdraw_requests SET status='sent', completed_timestamp=?  WHERE id=?", (str(int(datetime.now().timestamp())),markid))
            cursor.execute("SELECT owner_account FROM withdraw_requests WHERE id=?", (markid))
            owner = cursor.fetchone()[0]
            cnxn.commit()
            cnxn.close()
            e = emailer()
            e.payout_completed(owner, markid)
            return HttpResponse(json.dumps({'status': 'success'}), content_type="application/json")
