"""KBO 팀 순위 크롤러 — KBO 공식 사이트 + Statiz"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_team_ranking(year: int | None = None) -> pd.DataFrame:
    """KBO 공식 사이트에서 팀 순위 테이블을 가져온다."""
    year = year or datetime.now().year
    url = "https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx"

    session = requests.Session()
    session.headers.update(HEADERS)

    # 초기 페이지 로드 (ASP.NET ViewState 필요)
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.select_one("table.tData")
    if not table:
        print("[WARN] 팀 순위 테이블을 찾을 수 없습니다.")
        return pd.DataFrame()

    # 헤더
    headers_row = table.select("thead th")
    columns = [th.get_text(strip=True) for th in headers_row]

    # 바디
    rows = []
    for tr in table.select("tbody tr"):
        cells = [td.get_text(strip=True) for td in tr.select("td")]
        if cells:
            rows.append(cells)

    df = pd.DataFrame(rows, columns=columns[:len(rows[0])] if rows else columns)
    df.attrs["fetched_at"] = datetime.now().isoformat()
    df.attrs["source"] = "koreabaseball.com"
    return df


def get_team_ranking_statiz(year: int | None = None) -> pd.DataFrame:
    """Statiz에서 팀 순위/성적을 가져온다 (더 상세한 스탯 포함)."""
    year = year or datetime.now().year
    url = f"https://statiz.co.kr/stat.php?opt=0&sopt=0&re=0&ession=0001&search={year}"

    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.select_one("table.table_type03")
    if not table:
        print("[WARN] Statiz 팀 순위 테이블을 찾을 수 없습니다.")
        return pd.DataFrame()

    headers_row = table.select("thead th")
    columns = [th.get_text(strip=True) for th in headers_row]

    rows = []
    for tr in table.select("tbody tr"):
        cells = [td.get_text(strip=True) for td in tr.select("td")]
        if cells:
            rows.append(cells)

    df = pd.DataFrame(rows, columns=columns[:len(rows[0])] if rows else columns)
    df.attrs["fetched_at"] = datetime.now().isoformat()
    df.attrs["source"] = "statiz.co.kr"
    return df


if __name__ == "__main__":
    print("=== KBO 팀 순위 (공식) ===")
    df = get_team_ranking()
    if not df.empty:
        print(df.to_string(index=False))

    print("\n=== KBO 팀 순위 (Statiz) ===")
    df2 = get_team_ranking_statiz()
    if not df2.empty:
        print(df2.to_string(index=False))
