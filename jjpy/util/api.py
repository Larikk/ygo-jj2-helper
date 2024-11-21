import requests


def apiRequest(url):
    response = requests.get(url)

    if not response.ok:
        print("Request failed:" + url)

    content = response.json()

    return content
