"""KBO 관련 뉴스 크롤러 — Google News RSS"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

_RSS_BASE = "https://news.google.com/rss/search"


def _fetch_rss(query: str) -> list[dict]:
    url = f"{_RSS_BASE}?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "xml")
    articles = []
    for item in soup.find_all("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        pub_el = item.find("pubDate")
        source_el = item.find("source")

        title = title_el.get_text(strip=True) if title_el else ""
        # Google News 제목은 "기사제목 - 언론사" 형식
        if " - " in title:
            title, _ = title.rsplit(" - ", 1)

        articles.append({
            "title": title,
            "link": link_el.get_text(strip=True) if link_el else "",
            "date": pub_el.get_text(strip=True)[:25] if pub_el else "",
            "source": source_el.get_text(strip=True) if source_el else "",
            "description": "",
        })
    return articles


def get_kbo_news() -> list[dict]:
    """Google News RSS로 KBO 최신 뉴스를 가져온다."""
    return _fetch_rss("KBO 야구")


def get_team_news(team: str) -> list[dict]:
    """
    팀별 뉴스.
    team: 팀 이름 (예: '삼성', 'LG', '두산', 'KIA')
    """
    return _fetch_rss(f"KBO {team}")


if __name__ == "__main__":
    print("=== KBO 최신 뉴스 ===")
    news = get_kbo_news()
    for n in news[:10]:
        print(f"  [{n['source']}] {n['title']}")
        print(f"    {n['date']}")
