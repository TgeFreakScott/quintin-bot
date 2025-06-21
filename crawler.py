import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE = "https://sordiavignti.xyz/"
visited = set()
lore_urls = []


def crawl(url):
    if url in visited or not url.startswith(BASE):
        return
    visited.add(url)
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        lore_urls.append(url)
        for a in soup.find_all("a", href=True):
            link = urljoin(BASE, a["href"])
            info = urlparse(link)
            norm = info.scheme + "://" + info.netloc + info.path
            crawl(norm)
    except:
        pass


crawl(BASE)

with open("master_lore.txt", "w", encoding="utf-8") as f:
    for url in lore_urls:
        try:
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator="\n").strip()
            title = soup.find("title").text if soup.find("title") else url
            f.write(f"### {title}\n\n{text}\n\n")
        except Exception as e:
            f.write(f"### ERROR {url}\n\nFailed to fetch: {e}\n\n")

print(f"Crawled {len(lore_urls)} pages. Saved to master_lore.txt")
