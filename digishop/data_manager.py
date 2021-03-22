import json
import requests
import datetime
class manager:
    def grab_player_names(self):
        return json.load(open("players.json", 'r')).values()
    def grab_player_ids(self):
        return json.load(open("players.json", 'r')).keys()
    def grab_player_dict(self):
        return json.load(open("players.json", 'r'))
    def grab_player_name(self, id):
        return json.load(open("players.json", 'r'))[id]
    def grab_player_id(self, name):
        return {v: k for k, v in json.load(open("players.json", 'r')).items()}[name]
    def grab_player_moments_with_id(self, id):
        return json.load(open("moments.json", 'r'))[id]
    def grab_player_moments_with_name(self, name):
        return json.load(open("moments.json", 'r'))[self.grab_player_id(name)]
    def grab_moment_by_id(self, id):
        momentsList = json.load(open("moments.json", 'r')).values()
        momentsListModified = []
        for item in momentsList:
            for subitem in item:
                momentsListModified.append(subitem)
        for item in momentsListModified:
            if item['id'] == id:
                return item
        return {}
    def grab_moment_icon_by_id(self, id):
        momentsList = list(json.load(open("moments.json", 'r')).values())
        for momentListLocal in momentsList:
            for moment in momentListLocal:
                if moment['id'] == id:
                    return moment['assetPathPrefix']+"Hero_2880_2880_Black.jpg"
        return ""
    def generate_moment_name_by_id(self, id):
        momentsList = list(json.load(open("moments.json", 'r')).values())
        for momentListLocal in momentsList:
            for moment in momentListLocal:
                if moment['id'] == id:
                    print(moment)
                    return moment['play']['stats']['playerName'] + " | " + moment['set']['flowName']+"(Series "+str(moment['set']['flowSeriesNumber']) + ")"
        return ""
    def check_user_for_moment_by_id(self, username, id):
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
             "idMAIN": x["setPlay"]["ID"] + ":" + str(x['flowSerialNumber']) + "/" + str(
                 x['setPlay']['circulationCount']), "assetPrefix": x['assetPathPrefix'],
             "serialNumber": x['flowSerialNumber'],
             "serialNumberCap": x['setPlay']['circulationCount'],
             "name": x['play']['stats']['playerName'] + " - " + x['set']['flowName'] + " (Series " + str(
                 x['set']['flowSeriesNumber']) + ")",
             "date": "%s-%s-%s" % (
             datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").year,
             datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").month,
             datetime.datetime.strptime(x['play']['stats']['dateOfMoment'], "%Y-%m-%dT%H:%M:%SZ").day)} for x in
            user_moments['data']]
        for moment in momentDataStriped:
            if moment['id'] == id:
                return True
        return False

class queue:
    def send_moment(self, listing_id, moment_id, withdraw_account, moment_serial, owner):
        try:
            queueJson = json.load(open("withdraw_requests.json", "r"))
            queueJson['moments'].append({
              "withdrawAccount": withdraw_account,
              "listedTimestamp": str(int(datetime.datetime.now().timestamp())),
              "momentId": moment_id,
              "momentSerial": moment_serial,
              "listingId": listing_id,
              "owner": owner
            })
            json.dump(queueJson, open("withdraw_requests.json", "w"))
            return True
        except:
            return False

    def send_moment(self, listing_id, moment_id, withdraw_account, moment_serial, owner, listed_timestamp):
        try:
            queueJson = json.load(open("withdraw_requests.json", "r"))
            queueJson['moments'].append({
                "withdrawAccount": withdraw_account,
                "listedTimestamp": listed_timestamp,
                "momentId": moment_id,
                "momentSerial": moment_serial,
                "listingId": listing_id,
                "owner": owner
            })
            json.dump(queueJson, open("withdraw_requests.json", "w"))
            return True
        except:
            return False
    def send_money(self, owner, amount, paypalEmail):
        try:
            queueJson = json.load(open("withdraw_requests.json", "r"))
            queueJson['wallet'].append({
                "owner": owner,
                "withdrawAmount": amount,
                "withdrawEmail": paypalEmail
            })
            json.dump(queueJson, open("withdraw_requests.json", "w"))
            return True
        except:
            return False
    def grab_pending_withdraws_by_username(self, username):
        queueJson = json.load(open("withdraw_requests.json", "r"))
        userQueue = []
        for queueItem in queueJson['moments']:
            if queueItem['owner'] == username:
                userQueue.append(queueItem)
        
        print(userQueue)
        return userQueue
