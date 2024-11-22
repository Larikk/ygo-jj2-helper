import glob
import os
import sys
from jjpy.carddb.carddb import CardDB
from . import common

DEPLOYMENT_DIR = "../ygo-jj2-edopro-lflists/"

ACTIVE_LISTS = {
    "jj2-2002-p0",
}


def parseYear(name):
    parts = name.split("-")
    year = parts[1]
    return year


def prettifyName(name):
    return name.replace("-", " ").upper()


def startOfYear(year):
    return f"{year}-01-01"


def endOfYear(year):
    return f"{year}-31-12"


def createCardPool(cardDb, lfList, startdate="2000-01-01", enddate="3000-12-31"):

    def filterFunc(c): return startdate <= c["date"] <= enddate
    cards = cardDb.filter(filterFunc)

    unlimitedIds = set()
    for card in cards:
        id = card["id"]
        unlimitedIds.add(id)

    bannedCards = []
    limitedCards = []
    semilimitedCards = []
    unlimitedCards = []

    statusToCollectionMapping = {
        common.BANNED: bannedCards,
        common.LIMITED: limitedCards,
        common.SEMILIMITED: semilimitedCards,
    }

    for status, collection in statusToCollectionMapping.items():
        for card in lfList[status]:
            id = card["id"]
            unlimitedIds.remove(id)
            collection.append(card)

    for id in unlimitedIds:
        card, _ = cardDb.getCardById(id)
        unlimitedCards.append(card)

    pool = {
        common.BANNED: bannedCards,
        common.LIMITED: limitedCards,
        common.SEMILIMITED: semilimitedCards,
        common.UNLIMITED: unlimitedCards,
    }

    def sortKey(card): return card["name"].lower()
    for _, collection in pool.items():
        collection.sort(key=sortKey)

    return pool


def formatCard(n, id, name):
    return f"{id} {n}".ljust(20) + f"-- {name}\n"


def createConfFileContent(prettyName, cardPool, junior=False):
    order = [
        common.BANNED, common.LIMITED, common.SEMILIMITED, common.UNLIMITED
    ]

    s = f"#[{prettyName}]\n!{prettyName}\n$whitelist\n"
    if junior:
        s += formatCard(1, 1, "Junior Journey Format")

    for i in range(len(order)):
        sectionTitle = order[i]
        n = i
        s += f"# {sectionTitle.upper()}\n"
        for card in cardPool[sectionTitle]:
            s += formatCard(n, card["id"], card["name"])

    return s


def writeConfFile(name, content):
    path = DEPLOYMENT_DIR

    if name.startswith("jj2-") and not name.endswith("-preview") and name not in ACTIVE_LISTS:
        path = path + "archive/"

    os.makedirs(path, exist_ok=True)

    path = path + name + ".conf"
    with open(path, "w") as f:
        f.write(content)


def createConfFile(cardPool, fileName, prettyName):
    fileContent = createConfFileContent(prettyName, cardPool)
    writeConfFile(fileName, fileContent)


def cleanDeploymentDir():
    files = glob.glob(DEPLOYMENT_DIR + "/**/*.conf", recursive=True)
    for file in files:
        os.remove(file)


def getJuniorRoyaleChanges():
    files = glob.glob(common.CHANGE_DIR + "jr-*.ini")
    if len(files) > 1:
        print("Multiple Junior Royale files found")
        sys.exit()

    if len(files) == 0:
        return None

    return files[0]


def createRegularLfList(cardDb, lfList):
    name = lfList["name"]
    prettyName = prettifyName(name)
    year = parseYear(name)
    enddate = endOfYear(year)
    cardPool = createCardPool(cardDb, lfList, enddate=enddate)
    createConfFile(cardPool, name, prettyName)


def createP0LfList(cardDb, lfList):
    year = parseYear(lfList["name"])
    year = int(year) + 1
    name = f"jj2-{year}-p0"
    enddate = endOfYear(year)
    prettyName = prettifyName(name)
    cardPool = createCardPool(cardDb, lfList, enddate=enddate)
    createConfFile(cardPool, name, prettyName)


def createPreviewLfList(cardDb, lastLfList):
    lastYear = parseYear(lastLfList["name"])
    nextYear = str(int(lastYear) + 1)
    startdate = startOfYear(nextYear)
    enddate = endOfYear(nextYear)
    name = f"jj2-{nextYear}-preview"
    prettyName = f"JJ2 {nextYear} Preview"
    lfList = common.emptyLfList()
    cardPool = createCardPool(
        cardDb, lfList, startdate=startdate, enddate=enddate)
    createConfFile(cardPool, name, prettyName)


def createNextThreeLfLists(cardDb, lastLfList):
    year = parseYear(lastLfList["name"])

    for i in range(1):
        year = int(year) + 1
        name = f"jj2-{year}-preliminary"
        enddate = endOfYear(year)
        prettyName = prettifyName(name)
        cardPool = createCardPool(cardDb, lastLfList, enddate=enddate)
        createConfFile(cardPool, name, prettyName)


def createJuniorRoyaleLfList(cardDb, lastLfList):
    jrFile = getJuniorRoyaleChanges()
    if jrFile is None:
        return

    jrFile = common.parseChangeFile(cardDb, jrFile)

    year = parseYear(lastLfList["name"])
    enddate = endOfYear(year)
    name = jrFile["name"]
    prettyName = prettifyName(name)

    jrLfList = common.applyChanges(lastLfList, jrFile)
    cardPool = createCardPool(cardDb, jrLfList, enddate=enddate)
    createConfFile(cardPool, name, prettyName)


def main():
    cleanDeploymentDir()
    cardDb = CardDB()
    lfLists = common.buildBanlists(cardDb)

    for lfList in lfLists:
        createRegularLfList(cardDb, lfList)
        # Create P0 format for next year
        if lfList["name"].endswith("-p2"):
            createP0LfList(cardDb, lfList)

    lastLfList = lfLists[-1]
    createNextThreeLfLists(cardDb, lastLfList)
    createPreviewLfList(cardDb, lastLfList)

    createJuniorRoyaleLfList(cardDb, lastLfList)


if __name__ == "__main__":
    main()
