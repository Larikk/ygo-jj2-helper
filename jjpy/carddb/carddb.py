import json
import math
import os
import time
from . import build

DB_PATH = "data/carddb/db.json"


def isDBStale(db):
    creationTime = db["creation_time"]
    now = math.floor(time.time())

    oneWeek = 60*60*24*7

    return abs(creationTime - now) > oneWeek


def readDb():
    with open(DB_PATH, "r") as f:
        return json.load(f)


class CardDB:
    def noneCard(self, id=-1, name="None"):
        return {
            "id": id,
            "name": name,
            "date": "0000-01-01",
            "unofficial_versions": [],
            "types": [],
            "alt_names": [],
        }

    def getCardById(self, id):
        if id not in self.idMap:
            print("No card for id", id)
            return self.noneCard(id=id), False

        return self.idMap[id], True

    def getCardByName(self, name):
        key = name.lower()

        if key not in self.nameMap:
            print("No card for name", name)
            return self.noneCard(name=name), False

        return self.nameMap[key], True

    def idToName(self, id):
        card, ok = self.getCardById(id)
        return card["name"], ok

    def nameToId(self, name):
        card, ok = self.getCardByName(name)
        return card["id"], ok

    def filter(self, filterFunc):
        hits = filter(filterFunc, self.cards)
        return list(hits)

    def __init__(self):
        fileExists = os.path.isfile(DB_PATH)
        if not fileExists:
            build.buildDatabase()

        db = readDb()

        if isDBStale(db):
            build.buildDatabase()
            db = readDb()

        cards = db["cards"]
        nameMap = dict()
        idMap = dict()

        for card in cards:
            idMap[card["id"]] = card

            key = card["name"].lower()
            nameMap[key] = card
            for altname in card["alt_names"]:
                key = altname.lower()
                nameMap[key] = card

        self.cards = cards
        self.idMap = idMap
        self.nameMap = nameMap


if __name__ == "__main__":
    db = CardDB()
    card = db.getCardByName("Kinetic Soldier")
    print(card)
    card = db.getCardByName("Cipher Soldier")
    print(card)
