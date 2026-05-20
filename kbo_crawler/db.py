"""
DB 저장 모듈 — SQLAlchemy + MariaDB

각 크롤러 결과를 DB에 upsert / 교체 저장한다.

환경변수 (또는 .env):
    DB_HOST      기본: localhost
    DB_PORT      기본: 3307
    DB_NAME      기본: heroes
    DB_USER      기본: heroes
    DB_PASSWORD  기본: heroes
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


# ─────────────────────────────────────────────
# 엔진
# ─────────────────────────────────────────────

def _engine():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    name = os.getenv("DB_NAME", "heroes")
    user = os.getenv("DB_USER", "heroes")
    pw   = os.getenv("DB_PASSWORD", "heroes")
    url  = f"mysql+pymysql://{user}:{pw}@{host}:{port}/{name}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True)


# ─────────────────────────────────────────────
# 타입 변환 헬퍼
# ─────────────────────────────────────────────

def _int(val, default=0) -> int:
    try:
        v = str(val).replace(",", "").strip()
        return int(float(v)) if v not in ("", "-", "N/A") else default
    except (ValueError, TypeError):
        return default


def _float(val, default=0.0) -> float:
    try:
        v = str(val).replace(",", "").strip()
        return float(v) if v not in ("", "-", "N/A") else default
    except (ValueError, TypeError):
        return default


def _ip(val, default=0.0) -> float:
    """이닝 표기 "45 2/3" → 45.667 변환"""
    try:
        s = str(val).strip()
        if " " in s:
            parts = s.split()
            whole = int(parts[0])
            num, den = parts[1].split("/")
            return whole + int(num) / int(den)
        return float(s) if s not in ("", "-", "N/A") else default
    except (ValueError, TypeError, ZeroDivisionError):
        return default


# ─────────────────────────────────────────────
# schedule + game_score (live_score 크롤러용)
# ─────────────────────────────────────────────

def save_schedule_and_scores(games: list[dict]) -> int:
    """
    live_score.get_today_games() 결과를 schedule + game_score 테이블에 upsert.
    schedule 테이블도 live_score 데이터로 채운다 (game_id를 제공하는 소스가 이것뿐).
    """
    if not games:
        return 0

    now = datetime.now()
    engine = _engine()

    with engine.begin() as conn:
        for g in games:
            if not g.get("game_id"):
                continue

            # ── schedule 테이블 upsert ──────────────────
            conn.execute(text("""
                INSERT INTO schedule
                    (game_id, game_date, game_time, home_team, away_team, stadium, tv, created_at, updated_at)
                VALUES
                    (:game_id, :game_date, :game_time, :home_team, :away_team, :stadium, :tv, :now, :now)
                ON DUPLICATE KEY UPDATE
                    game_time  = VALUES(game_time),
                    home_team  = VALUES(home_team),
                    away_team  = VALUES(away_team),
                    stadium    = VALUES(stadium),
                    tv         = VALUES(tv),
                    updated_at = :now
            """), {
                "game_id":   g["game_id"],
                "game_date": g["date"],
                "game_time": g["time"],
                "home_team": g["home_team"],
                "away_team": g["away_team"],
                "stadium":   g["stadium"],
                "tv":        g.get("tv", ""),
                "now":       now,
            })

            # ── game_score 테이블 upsert ────────────────
            conn.execute(text("""
                INSERT INTO game_score
                    (game_id, status, home_score, away_score, inning, home_pitcher, away_pitcher, updated_at)
                VALUES
                    (:game_id, :status, :home_score, :away_score, :inning, :home_pitcher, :away_pitcher, :now)
                ON DUPLICATE KEY UPDATE
                    status       = VALUES(status),
                    home_score   = VALUES(home_score),
                    away_score   = VALUES(away_score),
                    inning       = VALUES(inning),
                    home_pitcher = VALUES(home_pitcher),
                    away_pitcher = VALUES(away_pitcher),
                    updated_at   = :now
            """), {
                "game_id":      g["game_id"],
                "status":       g["status"],
                "home_score":   g.get("home_score"),
                "away_score":   g.get("away_score"),
                "inning":       g.get("inning", ""),
                "home_pitcher": g.get("home_pitcher", ""),
                "away_pitcher": g.get("away_pitcher", ""),
                "now":          now,
            })

    print(f"[DB] schedule + game_score: {len(games)}경기 저장 완료")
    return len(games)


# ─────────────────────────────────────────────
# team_ranking
# ─────────────────────────────────────────────

# KBO 공식 사이트 컬럼명 → DB 컬럼명
_RANKING_COL_MAP = {
    "순위":  "rank_no",
    "팀명":  "team_name",
    "경기":  "games_played",
    "승":    "wins",
    "패":    "losses",
    "무":    "ties",
    "승률":  "win_pct",
    "게임차": "games_behind",
    "연속":  "streak",
}


def save_team_ranking(df) -> int:
    """team_ranking.get_team_ranking() DataFrame을 team_ranking 테이블에 upsert."""
    if df.empty:
        return 0

    df = df.rename(columns=_RANKING_COL_MAP)
    now = datetime.now()
    engine = _engine()
    count = 0

    with engine.begin() as conn:
        for _, row in df.iterrows():
            team_name = str(row.get("team_name", "")).strip()
            if not team_name:
                continue

            gb_raw = str(row.get("games_behind", "0")).strip()
            games_behind = 0.0 if gb_raw in ("-", "", "N/A") else _float(gb_raw)

            conn.execute(text("""
                INSERT INTO team_ranking
                    (team_name, rank_no, games_played, wins, losses, ties, win_pct, games_behind, streak, updated_at)
                VALUES
                    (:team_name, :rank_no, :games_played, :wins, :losses, :ties, :win_pct, :games_behind, :streak, :now)
                ON DUPLICATE KEY UPDATE
                    rank_no      = VALUES(rank_no),
                    games_played = VALUES(games_played),
                    wins         = VALUES(wins),
                    losses       = VALUES(losses),
                    ties         = VALUES(ties),
                    win_pct      = VALUES(win_pct),
                    games_behind = VALUES(games_behind),
                    streak       = VALUES(streak),
                    updated_at   = :now
            """), {
                "team_name":    team_name,
                "rank_no":      _int(row.get("rank_no", 0)),
                "games_played": _int(row.get("games_played", 0)),
                "wins":         _int(row.get("wins", 0)),
                "losses":       _int(row.get("losses", 0)),
                "ties":         _int(row.get("ties", 0)),
                "win_pct":      _float(row.get("win_pct", 0)),
                "games_behind": games_behind,
                "streak":       str(row.get("streak", "")).strip(),
                "now":          now,
            })
            count += 1

    print(f"[DB] team_ranking: {count}팀 저장 완료")
    return count


# ─────────────────────────────────────────────
# batter_stats
# ─────────────────────────────────────────────

# KBO 공식 사이트 타자 스탯 컬럼명 → DB 컬럼명
# 실제 크롤러 반환 컬럼: 순위, 선수명, 팀명, AVG, G, PA, AB, R, H, 2B, 3B, HR, TB, RBI, SAC, SF
_BATTER_COL_MAP = {
    "선수명": "player_name",
    "팀명":   "team",
    "AVG":    "avg",
    "G":      "games",
    "AB":     "at_bats",
    "H":      "hits",
    "HR":     "home_runs",
    "RBI":    "rbi",
    "R":      "runs",
}


def save_batter_stats(df) -> int:
    """
    player_stats.get_batter_stats() DataFrame을 batter_stats 테이블에 저장.
    매일 전체 교체 방식 (DELETE → INSERT).
    """
    if df.empty:
        return 0

    df = df.rename(columns=_BATTER_COL_MAP)
    now = datetime.now()
    engine = _engine()
    count = 0

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM batter_stats"))

        for _, row in df.iterrows():
            player_name = str(row.get("player_name", "")).strip()
            if not player_name:
                continue

            conn.execute(text("""
                INSERT INTO batter_stats
                    (player_name, team, games, at_bats, hits, home_runs, rbi, runs,
                     stolen_bases, avg, obp, slg, ops, updated_at)
                VALUES
                    (:player_name, :team, :games, :at_bats, :hits, :home_runs, :rbi, :runs,
                     :stolen_bases, :avg, :obp, :slg, :ops, :now)
            """), {
                "player_name":  player_name,
                "team":         str(row.get("team", "")).strip(),
                "games":        _int(row.get("games")),
                "at_bats":      _int(row.get("at_bats")),
                "hits":         _int(row.get("hits")),
                "home_runs":    _int(row.get("home_runs")),
                "rbi":          _int(row.get("rbi")),
                "runs":         _int(row.get("runs")),
                "stolen_bases": _int(row.get("stolen_bases", 0)),  # KBO 스탯 페이지에 없음
                "avg":          _float(row.get("avg")),
                "obp":          _float(row.get("obp", 0)),          # KBO 스탯 페이지에 없음
                "slg":          _float(row.get("slg", 0)),          # KBO 스탯 페이지에 없음
                "ops":          _float(row.get("ops", 0)),          # KBO 스탯 페이지에 없음
                "now":          now,
            })
            count += 1

    print(f"[DB] batter_stats: {count}명 저장 완료")
    return count


# ─────────────────────────────────────────────
# pitcher_stats
# ─────────────────────────────────────────────

# KBO 공식 사이트 투수 스탯 컬럼명 → DB 컬럼명
# 실제 크롤러 반환 컬럼: 순위, 선수명, 팀명, ERA, G, W, L, SV, HLD, WPCT, IP, H, HR, BB, HBP, SO, R, ER, WHIP
_PITCHER_COL_MAP = {
    "선수명": "player_name",
    "팀명":   "team",
    "ERA":    "era",
    "G":      "games",
    "W":      "wins",
    "L":      "losses",
    "SV":     "saves",
    "HLD":    "holds",
    "IP":     "innings_pitched",
    "SO":     "strikeouts",
    "BB":     "walks",
    "WHIP":   "whip",
}


def save_pitcher_stats(df) -> int:
    """
    player_stats.get_pitcher_stats() DataFrame을 pitcher_stats 테이블에 저장.
    매일 전체 교체 방식 (DELETE → INSERT).
    """
    if df.empty:
        return 0

    df = df.rename(columns=_PITCHER_COL_MAP)
    now = datetime.now()
    engine = _engine()
    count = 0

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM pitcher_stats"))

        for _, row in df.iterrows():
            player_name = str(row.get("player_name", "")).strip()
            if not player_name:
                continue

            conn.execute(text("""
                INSERT INTO pitcher_stats
                    (player_name, team, games, wins, losses, saves, holds,
                     era, innings_pitched, strikeouts, walks, whip, updated_at)
                VALUES
                    (:player_name, :team, :games, :wins, :losses, :saves, :holds,
                     :era, :innings_pitched, :strikeouts, :walks, :whip, :now)
            """), {
                "player_name":    player_name,
                "team":           str(row.get("team", "")).strip(),
                "games":          _int(row.get("games")),
                "wins":           _int(row.get("wins")),
                "losses":         _int(row.get("losses")),
                "saves":          _int(row.get("saves")),
                "holds":          _int(row.get("holds")),
                "era":            _float(row.get("era")),
                "innings_pitched":_ip(row.get("innings_pitched")),
                "strikeouts":     _int(row.get("strikeouts")),
                "walks":          _int(row.get("walks")),
                "whip":           _float(row.get("whip")),
                "now":            now,
            })
            count += 1

    print(f"[DB] pitcher_stats: {count}명 저장 완료")
    return count
