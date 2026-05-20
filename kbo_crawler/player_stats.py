"""KBO 선수 스탯 크롤러 — KBO 공식 사이트"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = "https://www.koreabaseball.com/Record/Player"


def _parse_kbo_table(url: str) -> pd.DataFrame:
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.select_one("table.tData01")
    if not table:
        return pd.DataFrame()

    columns = [th.get_text(strip=True) for th in table.select("thead th")]
    rows = []
    for tr in table.select("tbody tr"):
        cells = []
        for td in tr.select("td"):
            a = td.select_one("a")
            cells.append(a.get_text(strip=True) if a else td.get_text(strip=True))
        if cells:
            rows.append(cells)

    if not rows:
        return pd.DataFrame()

    col_count = len(rows[0])
    df = pd.DataFrame(rows, columns=columns[:col_count])
    df.attrs["fetched_at"] = datetime.now().isoformat()
    df.attrs["source"] = "koreabaseball.com"
    return df


def get_batter_stats(year: int | None = None) -> pd.DataFrame:
    """시즌 타자 스탯 (KBO 공식)."""
    year = year or datetime.now().year
    url = f"{BASE_URL}/HitterBasic/Basic1.aspx?leId=1&srId=0&seasonId={year}"
    df = _parse_kbo_table(url)
    if not df.empty:
        df.attrs["category"] = "batter"
    return df


def get_pitcher_stats(year: int | None = None) -> pd.DataFrame:
    """시즌 투수 스탯 (KBO 공식)."""
    year = year or datetime.now().year
    url = f"{BASE_URL}/PitcherBasic/Basic1.aspx?leId=1&srId=0&seasonId={year}"
    df = _parse_kbo_table(url)
    if not df.empty:
        df.attrs["category"] = "pitcher"
    return df


def get_batter_stats_detail(year: int | None = None) -> pd.DataFrame:
    """타자 상세 스탯 (장타율, 출루율, OPS 등)."""
    year = year or datetime.now().year
    url = f"{BASE_URL}/HitterBasic/Basic2.aspx?leId=1&srId=0&seasonId={year}"
    return _parse_kbo_table(url)


def get_pitcher_stats_detail(year: int | None = None) -> pd.DataFrame:
    """투수 상세 스탯 (WHIP, 피안타율 등)."""
    year = year or datetime.now().year
    url = f"{BASE_URL}/PitcherBasic/Basic2.aspx?leId=1&srId=0&seasonId={year}"
    return _parse_kbo_table(url)


if __name__ == "__main__":
    print("=== KBO 타자 스탯 (상위) ===")
    batters = get_batter_stats()
    if not batters.empty:
        print(batters.head(10).to_string(index=False))

    print("\n=== KBO 투수 스탯 (상위) ===")
    pitchers = get_pitcher_stats()
    if not pitchers.empty:
        print(pitchers.head(10).to_string(index=False))
