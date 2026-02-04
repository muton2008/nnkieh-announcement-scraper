import requests
from lxml import etree
from typing import Dict, List
from urllib.parse import urlparse, parse_qs

NS = {
    "dc": "http://purl.org/dc/elements/1.1/"
}

def fetcher():
    response = requests.get("https://www.nnkieh.tn.edu.tw/feed/")
    response.raise_for_status()

    tree = etree.fromstring(response.content)
    items = tree.xpath("//item")

    announcements: List[Dict] = []

    for item in items:
        title = item.xpath("title/text()")[0]

        guid = item.xpath("guid/text()")
        url = guid[0] if guid else item.xpath("link/text()")[0]

        creator = item.xpath("dc:creator/text()", namespaces=NS)
        dc = creator[0] if creator else "unknown"

        pub_date = item.xpath("pubDate/text()")[0]

        category = item.xpath("category/text()")

        description = item.xpath("description/text()")
        description = description[0] if description else ""

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        post_id = qs.get("p", [None])[0]

        announcements.append({
            "title": title,
            "url": url,
            "author": dc,
            "published": pub_date,
            "category": category,
            "description": description,
            "post_id": post_id
        })

    #print(announcements[0]) debug
    return announcements

if __name__ == "__main__":
    print(fetcher())
