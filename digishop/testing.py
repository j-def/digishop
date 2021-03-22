import requests
username = "blma"
r = requests.get("https://www.nbatopshot.com/user/@" + username + "/moments")
rShaven = r.text[r.text.find("publicInfo"):r.text.rfind('"username"')]
dapperId = rShaven[rShaven.find("\"dapperID\":\"") + len("\"dapperID\":\""):rShaven.find("\",\"username\":")]
print(len(dapperId))