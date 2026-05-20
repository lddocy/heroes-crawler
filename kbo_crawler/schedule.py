"""KBO 경기 일정 크롤러 — KBO 공식 ASMX API"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.koreabaseball.com/Schedule/Schedule.aspx",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded",
}

_SR_ID = "0,9"  # 정규시즌 + 시범경기


def get_monthly_schedule(year: int | None = None, month: int | None = None) -> pd.DataFrame:
    """KBO 공식 ASMX API로 월별 경기 일정을 가져온다."""
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    resp = requests.post(
        "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList",
        headers=HEADERS,
        data={
            "leId": "1",
            "srIdList": _SR_ID,
            "seasonId": str(year),
            "gameMonth": f"{month:02d}",
            "teamId": "",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    rows_raw = data.get("rows", [])
    if not rows_raw:
        return pd.DataFrame()

    games = []
    current_date = ""

    for row_obj in rows_raw:
        cells = row_obj.get("row", [])
        if not cells:
            continue

        # date 셀
        date_cell = next((c for c in cells if c.get("Class") == "day"), None)
        if date_cell and date_cell.get("Text"):
            current_date = date_cell["Text"]

        # 경기 정보 셀 (play 클래스)
        play_cell = next((c for c in cells if c.get("Class") == "play"), None)
        if not play_cell:
            continue

        play_html = play_cell.get("Text", "")
        soup = BeautifulSoup(play_html, "lxml")
        teams = [span.get_text(strip=True) for span in soup.select("span")]
        scores = [em.get_text(strip=True) for em in soup.select("em")]

        # 시간 셀
        time_cell = next((c for c in cells if c.get("Class") == "time"), None)
        time_text = BeautifulSoup(time_cell["Text"], "lxml").get_text(strip=True) if time_cell else ""

        # 구장
        stadium_text = ""
        for c in cells:
            txt = c.get("Text", "")
            if txt and not c.get("Class") and len(txt) <= 10 and not re.search(r'btn|href', txt):
                stadium_text = txt
                break

        games.append({
            "date": current_date,
            "time": time_text,
            "away_team": teams[0] if len(teams) > 0 else "",
            "home_team": teams[-1] if len(teams) > 1 else "",
            "score": scores[0] if scores else "",
            "stadium": stadium_text,
        })

    df = pd.DataFrame(games)
    df.attrs["fetched_at"] = datetime.now().isoformat()
    return df


if __name__ == "__main__":
    print("=== 이번 달 KBO 일정 ===")
    df = get_monthly_schedule()
    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("일정을 가져올 수 없습니다.")
