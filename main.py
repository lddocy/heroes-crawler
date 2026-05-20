"""
KBO 리그 데이터 종합 크롤러

사용법:
    python main.py                   # 전체 데이터 수집 (콘솔 출력)
    python main.py --db              # 전체 수집 + DB 저장
    python main.py --live            # 실시간 스코어만
    python main.py --live --db       # 실시간 스코어 수집 + DB 저장
    python main.py --ranking --db    # 팀 순위 수집 + DB 저장
    python main.py --stats --db      # 선수 스탯 수집 + DB 저장
    python main.py --schedule        # 경기 일정 조회 (출력만)
    python main.py --save            # CSV로 저장
    python main.py --cron            # 주기 실행 모드 (daemon)
"""

import argparse
import os
from datetime import datetime

import schedule as cron  # 주기 실행 라이브러리 (kbo_crawler.schedule과 구분)
import time

from kbo_crawler.team_ranking import get_team_ranking, get_team_ranking_statiz
from kbo_crawler.player_stats import get_batter_stats, get_pitcher_stats
from kbo_crawler.live_score import get_today_games
from kbo_crawler.schedule import get_monthly_schedule

OUTPUT_DIR = "data"


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# 개별 수집 함수
# ─────────────────────────────────────────────

def run_ranking(save: bool = False, db: bool = False):
    print("\n" + "=" * 60)
    print("  KBO 팀 순위")
    print("=" * 60)

    df = get_team_ranking()
    if df.empty:
        print("  공식 사이트 실패 → Statiz로 시도합니다...")
        df = get_team_ranking_statiz()

    if df.empty:
        print("  [ERROR] 팀 순위 데이터를 가져올 수 없습니다.")
        return

    print(df.to_string(index=False))

    if save:
        ensure_output_dir()
        df.to_csv(f"{OUTPUT_DIR}/team_ranking.csv", index=False, encoding="utf-8-sig")
        print(f"  → {OUTPUT_DIR}/team_ranking.csv 저장 완료")

    if db:
        from kbo_crawler.db import save_team_ranking
        save_team_ranking(df)


def run_live(save: bool = False, db: bool = False):
    print("\n" + "=" * 60)
    print(f"  오늘의 KBO 경기 ({datetime.now().strftime('%Y-%m-%d')})")
    print("=" * 60)

    games = get_today_games()
    if not games:
        print("  오늘 예정된 경기가 없습니다.")
        return

    for g in games:
        if g["away_score"] is not None:
            score = f"{g['away_score']} : {g['home_score']}"
        else:
            score = "vs"
        pitcher = ""
        if g.get("away_pitcher") or g.get("home_pitcher"):
            pitcher = f" | 선발: {g.get('away_pitcher', '?')} vs {g.get('home_pitcher', '?')}"
        print(f"  {g['away_team']} {score} {g['home_team']} | {g['stadium']} | {g['status']}{pitcher}")

    if save:
        import pandas as pd
        ensure_output_dir()
        pd.DataFrame(games).to_csv(
            f"{OUTPUT_DIR}/live_{datetime.now().strftime('%Y%m%d')}.csv",
            index=False, encoding="utf-8-sig"
        )

    if db:
        from kbo_crawler.db import save_schedule_and_scores
        save_schedule_and_scores(games)


def run_stats(save: bool = False, db: bool = False):
    print("\n" + "=" * 60)
    print("  KBO 타자 스탯 (TOP 15)")
    print("=" * 60)

    batters = get_batter_stats()
    if not batters.empty:
        print(batters.head(15).to_string(index=False))
        if save:
            ensure_output_dir()
            batters.to_csv(f"{OUTPUT_DIR}/batter_stats.csv", index=False, encoding="utf-8-sig")
        if db:
            from kbo_crawler.db import save_batter_stats
            save_batter_stats(batters)

    print("\n" + "=" * 60)
    print("  KBO 투수 스탯 (TOP 15)")
    print("=" * 60)

    pitchers = get_pitcher_stats()
    if not pitchers.empty:
        print(pitchers.head(15).to_string(index=False))
        if save:
            ensure_output_dir()
            pitchers.to_csv(f"{OUTPUT_DIR}/pitcher_stats.csv", index=False, encoding="utf-8-sig")
        if db:
            from kbo_crawler.db import save_pitcher_stats
            save_pitcher_stats(pitchers)


def run_schedule(save: bool = False):
    print("\n" + "=" * 60)
    print("  이번 달 KBO 일정")
    print("=" * 60)

    df = get_monthly_schedule()
    if df.empty:
        print("  일정을 가져올 수 없습니다.")
        return

    print(df.to_string(index=False))
    if save:
        ensure_output_dir()
        df.to_csv(f"{OUTPUT_DIR}/schedule.csv", index=False, encoding="utf-8-sig")


# ─────────────────────────────────────────────
# cron 작업 정의
# ─────────────────────────────────────────────

def _job_live():
    """실시간 스코어 수집 → DB 저장 (5분마다)"""
    print(f"\n[CRON] 실시간 스코어 수집 {datetime.now().strftime('%H:%M:%S')}")
    try:
        games = get_today_games()
        if games:
            from kbo_crawler.db import save_schedule_and_scores
            save_schedule_and_scores(games)
        else:
            print("[CRON] 오늘 경기 없음")
    except Exception as e:
        print(f"[CRON][ERROR] 실시간 스코어: {e}")


def _job_daily():
    """팀 순위 + 선수 스탯 수집 → DB 저장 (매일 06:00)"""
    print(f"\n[CRON] 일별 데이터 수집 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        from kbo_crawler.db import save_team_ranking, save_batter_stats, save_pitcher_stats

        df_rank = get_team_ranking()
        if df_rank.empty:
            df_rank = get_team_ranking_statiz()
        if not df_rank.empty:
            save_team_ranking(df_rank)

        batters = get_batter_stats()
        if not batters.empty:
            save_batter_stats(batters)

        pitchers = get_pitcher_stats()
        if not pitchers.empty:
            save_pitcher_stats(pitchers)

    except Exception as e:
        print(f"[CRON][ERROR] 일별 수집: {e}")


def run_cron():
    """주기 실행 모드 — 프로세스가 떠있는 동안 계속 실행"""
    print("=" * 60)
    print("  KBO 크롤러 — cron 모드 시작")
    print(f"  실시간 스코어: 5분마다")
    print(f"  순위·스탯:     매일 06:00")
    print("=" * 60)

    # 시작 시 즉시 1회 실행
    _job_daily()
    _job_live()

    cron.every(5).minutes.do(_job_live)
    cron.every().day.at("06:00").do(_job_daily)

    while True:
        cron.run_pending()
        time.sleep(10)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="KBO 리그 데이터 크롤러")
    parser.add_argument("--live",     action="store_true", help="실시간 스코어")
    parser.add_argument("--ranking",  action="store_true", help="팀 순위")
    parser.add_argument("--stats",    action="store_true", help="선수 스탯")
    parser.add_argument("--schedule", action="store_true", help="경기 일정")
    parser.add_argument("--db",       action="store_true", help="DB에 저장")
    parser.add_argument("--save",     action="store_true", help="CSV로 저장")
    parser.add_argument("--cron",     action="store_true", help="주기 실행 모드")
    args = parser.parse_args()

    if args.cron:
        run_cron()
        return

    run_all = not any([args.live, args.ranking, args.stats, args.schedule])

    print("=" * 60)
    print("  KBO 리그 데이터 크롤러")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if run_all or args.ranking:
        run_ranking(save=args.save, db=args.db)

    if run_all or args.live:
        run_live(save=args.save, db=args.db)

    if run_all or args.stats:
        run_stats(save=args.save, db=args.db)

    if run_all or args.schedule:
        run_schedule(save=args.save)

    print("\n" + "=" * 60)
    print("  수집 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
