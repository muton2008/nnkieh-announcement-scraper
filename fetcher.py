import requests
from lxml import etree
from typing import Dict, List
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/"
}

def get_full_content(url: str) -> str:
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        if res.status_code != 200:
            return ""

        soup = BeautifulSoup(res.text, "html.parser")
        content_div = soup.find("div", class_="entry-content clr", itemprop="text")
        
        if content_div:
            # 1. 處理附件 (wp-block-file)
            attachments = []
            file_blocks = content_div.find_all("div", class_="wp-block-file")
            for block in file_blocks:
                link_tag = block.find("a") # 取得第一個 <a> 通常是檔名
                if link_tag:
                    file_name = link_tag.get_text(strip=True)
                    file_url = link_tag.get("href")
                    attachments.append(f"【附件檔案】：{file_name} (下載位址: {file_url})")
            
            # 2. 移除不需要的元素 (如 Post Views)
            for extra in content_div.find_all("div", class_="post-views"):
                extra.decompose()

            # 3. 取得原本的文字內容
            main_text = content_div.get_text(separator="\n", strip=True)

            # 4. 組合文字與附件資訊
            if attachments:
                attachment_info = "\n".join(attachments)
                return f"{main_text}\n\n{attachment_info}".strip()
            
            return main_text
            
        return ""
    except Exception as e:
        print(f"爬取失敗: {e}")
        return ""

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

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        post_id = qs.get("p", [None])[0]

        real_url = f"https://www.nnkieh.tn.edu.tw/news/{title}/{post_id}"

        description = get_full_content(real_url) or item.xpath("description/text()")[0]

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
