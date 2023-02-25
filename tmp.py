import requests
from bs4 import BeautifulSoup

html = requests.get("https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes").text

soup = BeautifulSoup(html, "html.parser")

for tr in soup.find_all("tbody")[1].find_all("tr"):
    if tr is not None:
        print(' '.join([elem.text for elem in tr.find_all("td")[1:3]]))
