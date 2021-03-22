import requests
import json
player = "203932"

def grab_players():
    rurl = "https://api.nba.dapperlabs.com/marketplace/graphql?SearchTags"
    rdata = """{"operationName":"SearchTags","variables":{"setsInput":{}},"query":"query SearchTags($setsInput: SearchSetsInput!) {  allPlayers {    size    data {      id      name      __typename    }    __typename  }  allTeams {    size    data {      id      name      __typename    }    __typename  }  searchSets(input: $setsInput) {    searchSummary {      data {        ... on Sets {          data {            id            ... on Set {              flowName              setVisualId              flowSeriesNumber              __typename            }            __typename          }          __typename        }        __typename      }      __typename    }    __typename  }}"}"""
    rheaders = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://www.nbatopshot.com",
        "referer": "https://www.nbatopshot.com/",
        "sec-ch-ua": '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
    }
    r = requests.post(rurl, headers=rheaders, data=rdata)
    rjson = json.loads(r.text)
    rjsonList = [(moment['id'], moment['name']) for moment in rjson['data']['allPlayers']['data']]
    rjsonModified = {}
    for item in rjsonList:
        rjsonModified[item[0]] = item[1]
    json.dump(rjsonModified, open("players.json", 'w'))
    return rjsonList
def grab_player_moments(player):
    rurl = "https://api.nba.dapperlabs.com/marketplace/graphql?SearchMomentListingsDefault"
    rdata = """{"operationName":"SearchMomentListingsDefault","variables":{"byPrice":{"min":null,"max":null},"byPower":{"min":null,"max":null},"bySerialNumber":{"min":null,"max":null},"byGameDate":{"start":null,"end":null},"byCreatedAt":{"start":null,"end":null},"byPrimaryPlayerPosition":[],"bySets":[],"bySeries":[],"bySetVisuals":[],"byPlayStyle":[],"bySkill":[],"byPlayers":["%s"],"byTagNames":[],"byTeams":[],"byListingType":["BY_USERS"],"searchInput":{"pagination":{"cursor":"","direction":"RIGHT","limit":96}},"orderBy":"UPDATED_AT_DESC"},"query":"query SearchMomentListingsDefault($byPlayers: [ID], $byTagNames: [String!], $byTeams: [ID], $byPrice: PriceRangeFilterInput, $orderBy: MomentListingSortType, $byGameDate: DateRangeFilterInput, $byCreatedAt: DateRangeFilterInput, $byListingType: [MomentListingType], $bySets: [ID], $bySeries: [ID], $bySetVisuals: [VisualIdType], $byPrimaryPlayerPosition: [PlayerPosition], $bySerialNumber: IntegerRangeFilterInput, $searchInput: BaseSearchInput!, $userDapperID: ID) {  searchMomentListings(input: {filters: {byPlayers: $byPlayers, byTagNames: $byTagNames, byGameDate: $byGameDate, byCreatedAt: $byCreatedAt, byTeams: $byTeams, byPrice: $byPrice, byListingType: $byListingType, byPrimaryPlayerPosition: $byPrimaryPlayerPosition, bySets: $bySets, bySeries: $bySeries, bySetVisuals: $bySetVisuals, bySerialNumber: $bySerialNumber}, sortBy: $orderBy, searchInput: $searchInput, userDapperID: $userDapperID}) {    data {      filters {        byPlayers        byTagNames        byTeams        byPrimaryPlayerPosition        byGameDate {          start          end          __typename        }        byCreatedAt {          start          end          __typename        }        byPrice {          min          max          __typename        }        bySerialNumber {          min          max          __typename        }        bySets        bySeries        bySetVisuals        __typename      }      searchSummary {        count {          count          __typename        }        pagination {          leftCursor          rightCursor          __typename        }        data {          ... on MomentListings {            size            data {              ... on MomentListing {                id                version                circulationCount                flowRetired                set {                  id                  flowName                  setVisualId                  flowSeriesNumber                  __typename                }                play {                  description                  id                  stats {                    playerName                    dateOfMoment                    playCategory                    teamAtMomentNbaId                    teamAtMoment                    __typename                  }                  __typename                }                assetPathPrefix                priceRange {                  min                  max                  __typename                }                momentListingCount                listingType                userOwnedSetPlayCount                __typename              }              __typename            }            __typename          }          __typename        }        __typename      }      __typename    }    __typename  }}"}""" % player
    rheaders = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.nbatopshot.com",
    "referer": "https://www.nbatopshot.com/",
    "sec-ch-ua": '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
    "x-id-token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik9EQkVPRGxDUXpWR1JVUXhSRUl5UkRRNE1rVTJNekkzTlVaR1JUWkNPRFJCUkRZNU9URXhOUSJ9.eyJnaXZlbl9uYW1lIjoiam9zaHVhIiwiZmFtaWx5X25hbWUiOiJkZWZlc2NoZSIsIm5pY2tuYW1lIjoiam9zaHVhLmRlZmVzY2hlIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYmxtIiwibmFtZSI6Impvc2h1YSBkZWZlc2NoZSIsInBpY3R1cmUiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vZGFwcGVyLXByb2ZpbGUtaWNvbnMvYXZhdGFyLWRlZmF1bHQucG5nIiwibG9jYWxlIjoiZW4iLCJ1cGRhdGVkX2F0IjoiMjAyMS0wMy0wM1QwODoxMzo0OC4zODZaIiwiZW1haWwiOiJqb3NodWEuZGVmZXNjaGVAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOi8vYXV0aC5tZWV0ZGFwcGVyLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExMTE3MTQ2NTc3ODE2MDAzNjg5NSIsImF1ZCI6Ijc1NktDdmlpdTZWQVMxbmJldGpVams2NE9jWjBZdjhyIiwiaWF0IjoxNjE0NzU5NjMxLCJleHAiOjE2MTQ3NjA1MzF9.LKq0jBCGCA9aReVt5TSpcSTUNvCwaTNtAFEnZH2M97cuH7KuiNCvyMej3WghMWZK3bu5Qb_AvCFcKMopPDTtLGSvqBRvc1ESswWHBJHB3fIQ14GEmcbDXcBGW0DJ1xzLe097EFB1I8w_8Ey8o4E_0wwVQNWLkPpcovXPLDsICPF0LmR1yinJ9Z2cTXaWV8oEA-BCOCOLvlPQKTxw9bhnH3t9Y_3BiiVfWp51xWzfTEvW2GEsrKcb9S7VqcTEbtzYECEX73Ek1Zh273cqGxFXe_EiG4KVHKJh4YzHmCtkmwu8KIn8cSwUucQ4dbY4Ozi8scedfa6sWSW4EUDrK-lggg"
    }
    r = requests.post(rurl, headers=rheaders, data=rdata, json=rdata)
    rjson = json.loads(r.text)
    return rjson['data']['searchMomentListings']['data']['searchSummary']['data']['data']
basejson = {}
for player in grab_players():
    basejson[player[0]] = grab_player_moments(player[0])
json.dump(basejson, open("moments.json", "w"))

