"""KBO 실시간 스코어 크롤러 — KBO 공식 ASMX API"""

import requests
from datetime import date


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.koreabaseball.com/",
    "X-Requested-With": "XMLHttpRequest",
}

_STATUS_MAP = {
    "0": "경기 전",
    "1": "경기 전",
    "2": "진행 중",
    "3": "종료",
    "4": "취소",
    "5": "우천취소",
}

# 2021년부터 srId 확장
_SR_ID = "0,1,3,4,5,6,7,8,9"


def get_today_games(game_date: date | None = None) -> list[dict]:
    """KBO 공식 API로 오늘(또는 지정일) 경기 목록 + 스코어를 가져온다."""
    game_date = game_date or date.today()
    date_str = game_date.strftime("%Y%m%d")

    resp = requests.post(
        "https://www.koreabaseball.com/ws/Main.asmx/GetKboGameList",
        headers=HEADERS,
        data={"leId": "1", "srId": _SR_ID, "date": date_str},
    )
    resp.raise_for_status()
    data = resp.json()

    games = []
    for g in data.get("game", []):
        away_score = g.get("T_SCORE_CN")
        home_score = g.get("B_SCORE_CN")

        # 경기 전이면 점수 None 처리
        result_ck = g.get("GAME_RESULT_CK", 0)
        state = g.get("GAME_STATE_SC", "1")
        if state in ("0", "1") and not result_ck:
            away_score = None
            home_score = None
        else:
            try:
                away_score = int(away_score)
                home_score = int(home_score)
            except (TypeError, ValueError):
                away_score = None
                home_score = None

        inning = g.get("GAME_INN_NO")
        tb = g.get("GAME_TB_SC_NM", "")
        inning_txt = f"{inning}회 {tb}".strip() if inning else ""

        games.append({
            "game_id": g.get("G_ID"),
            "date": game_date.isoformat(),
            "time": g.get("G_TM", ""),
            "status": _STATUS_MAP.get(str(state), state),
            "stadium": g.get("S_NM", ""),
            "home_team": g.get("HOME_NM", ""),
            "away_team": g.get("AWAY_NM", ""),
            "home_score": home_score,
            "away_score": away_score,
            "home_pitcher": g.get("B_PIT_P_NM", "").strip(),
            "away_pitcher": g.get("T_PIT_P_NM", "").strip(),
            "inning": inning_txt,
            "tv": g.get("TV_IF", ""),
        })

    return games


if __name__ == "__main__":
    print(f"=== 오늘 ({date.today()}) KBO 경기 ===")
    games = get_today_games()
    if not games:
        print("오늘 예정된 경기가 없습니다.")
    for g in games:
        score = f"{g['away_score']} - {g['home_score']}" if g["away_score"] is not None else "vs"
        print(f"  {g['away_team']} {score} {g['home_team']} | {g['stadium']} | {g['status']} | {g['time']}")
