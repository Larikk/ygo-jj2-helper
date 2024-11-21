import json
import os
import configparser
import sys

from jjpy.carddb.carddb import CardDB

CHANGE_DIR = "data/banlist/changes/"

BANNED = "banned"
LIMITED = "limited"
SEMILIMITED = "semilimited"
UNLIMITED = "unlimited"


sectionTitlesWithCardNames = [
    BANNED,
    LIMITED,
    SEMILIMITED,
    UNLIMITED,
]


def emptyLfList():
    return {
        BANNED: [],
        LIMITED: [],
        SEMILIMITED: [],
        "changes": [],
    }


def parseChangeFile(cardDb, path):
    parser = configparser.ConfigParser(
        allow_no_value=True,
        delimiters=("="),
        comment_prefixes=None,
    )

    parser.read(path)

    parsedFile = dict()
    encounteredCards = []
    errorEncountered = False

    for section in parser.sections():
        cardsInSection = []
        for cardname in parser[section]:
            card, ok = cardDb.getCardByName(cardname)
            if not ok:
                print("Invalid name encountered", path, cardname)
                errorEncountered = True

            if card in encounteredCards:
                print("Card was listed twice in change file", path, cardname)
                errorEncountered = True
            encounteredCards.append(card)

            cardsInSection.append(card)
        parsedFile[section] = cardsInSection

    if errorEncountered:
        print("Fatal error. Invalid file", path)
        sys.exit()

    name = path.split("/")[-1].split(".")[0]
    parsedFile["name"] = name

    return parsedFile


def parseAllChangeFiles(cardDb):
    files = os.listdir(CHANGE_DIR)
    files = filter(lambda f: f.startswith("jj2-"), files)
    files = sorted(files)

    parsedFiles = []
    for file in files:
        path = CHANGE_DIR + file
        parsedFile = parseChangeFile(cardDb, path)
        parsedFiles.append(parsedFile)

    return parsedFiles


def applyChanges(baseList, changeFile):
    lf = [BANNED, LIMITED, SEMILIMITED]

    newList = None

    if baseList is None:
        newList = emptyLfList()
    else:
        newList = {}
        for status in lf:
            newList[status] = list(baseList[status])
        newList["changes"] = []

    newList["name"] = changeFile["name"]

    for sectionTitle in sectionTitlesWithCardNames:
        for card in changeFile[sectionTitle]:
            _from = UNLIMITED
            to = sectionTitle

            for status in lf:
                if card in newList[status]:
                    newList[status].remove(card)
                    _from = status
                    break

            if to != UNLIMITED:
                newList[to].append(card)

            newList["changes"].append({
                "from": _from,
                "to": to,
                "card": card,
            })

    return newList


def buildBanlists(cardDb):
    changeFiles = parseAllChangeFiles(cardDb)

    prevList = None
    lfLists = []
    for changeFile in changeFiles:
        lfList = applyChanges(prevList, changeFile)
        lfLists.append(lfList)
        prevList = lfList

    return lfLists


if __name__ == "__main__":
    cardDb = CardDB()
    lfLists = buildBanlists(cardDb)
    print(json.dumps(lfLists, indent=4, ensure_ascii=False))
