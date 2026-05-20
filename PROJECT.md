# HEROES 앱 프로젝트 문서

키움 히어로즈 팬 전용 KBO 정보 앱

---

## 아키텍처 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                   Client (Mobile Web)                │
│              heroes-fe  React + Vite                 │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP /api
                        ▼
┌─────────────────────────────────────────────────────┐
│              heroes-be  Spring Boot                  │
│         REST API  (포트 8080)                        │
└───────────┬───────────────────────┬─────────────────┘
            │ JPA                   │ Redis
            ▼                       ▼
┌───────────────────┐   ┌───────────────────────────┐
│     MariaDB       │   │     Redis                 │
│  (메인 데이터)     │   │  (캐싱 - 순위/스코어)      │
└───────────────────┘   └───────────────────────────┘
            ▲
            │ 주기적 저장 (cron)
            │
┌───────────────────────────────────────────────────┐
│            crawler  Python 3.13                   │
│         KBO 공식 + Google News RSS                │
└───────────────────────────────────────────────────┘
            ▲
            │ HTTP
            ▼
┌─────────────────────────────────────────────────────┐
│  외부 데이터 소스                                     │
│  - KBO 공식 (koreabaseball.com) ASMX API            │
│  - Google News RSS                                   │
│  - nol티켓 (ticket.interpark.com)                   │
└─────────────────────────────────────────────────────┘
```

---

## 프로젝트 구조

```
baseball/
├── PROJECT.md               # 이 파일
├── FEATURES.md              # 기능 명세
│
├── kbo_crawler/             # Python 크롤러
│   ├── __init__.py
│   ├── team_ranking.py      # 팀 순위 (KBO 공식 HTML)
│   ├── player_stats.py      # 타자/투수 스탯 (KBO 공식 HTML)
│   ├── live_score.py        # 실시간 스코어 (KBO ASMX GetKboGameList)
│   ├── schedule.py          # 경기 일정 (KBO ASMX GetScheduleList)
│   └── news.py              # 뉴스 (Google News RSS)
├── main.py                  # 크롤러 CLI 진입점
├── requirements.txt
│
├── heroes-be/               # Spring Boot 백엔드
│   └── src/main/java/
│       └── {패키지}/
│           ├── game/        # 실시간 스코어 도메인
│           ├── ranking/     # 팀 순위 도메인
│           ├── stats/       # 선수 스탯 도메인
│           ├── schedule/    # 경기 일정 도메인
│           ├── news/        # 뉴스 도메인
│           └── common/      # 공통 (예외처리, 응답 포맷)
│
└── heroes-fe/               # React 프론트엔드
    └── src/
        ├── api/             # axios 도메인별 API 함수
        │   └── _client.ts   # axios 인스턴스 (baseURL: /api)
        ├── components/
        │   ├── common/      # Layout, 공통 UI
        │   └── features/    # 도메인별 컴포넌트
        │       ├── live/
        │       ├── ranking/
        │       ├── stats/
        │       ├── schedule/
        │       └── fan/
        ├── pages/           # 라우트 페이지
        ├── stores/          # Zustand 전역 상태
        ├── hooks/           # 커스텀 훅
        ├── types/           # 공유 TypeScript 타입
        └── lib/             # 유틸, 상수, mockData
```

---

## 기술 스택

| 레이어 | 기술 |
|---|---|
| 프론트엔드 | React 18, Vite, TypeScript, Tailwind CSS |
| 상태관리 | Zustand, React Query (@tanstack/react-query) |
| 라우팅 | React Router v6 |
| 아이콘 | Iconify (`@iconify/react`) |
| 백엔드 | Spring Boot 3, Java 17 |
| ORM | Spring Data JPA |
| DB | MariaDB |
| 캐시 | Redis |
| 크롤러 | Python 3.13, requests, BeautifulSoup4, pandas |
| 인프라 | Docker, Docker Compose |

---

## 데이터 흐름

```
[크롤러 cron 실행]
      │
      ├─ 팀 순위      → DB: team_ranking
      ├─ 선수 스탯    → DB: player_stats
      ├─ 경기 일정    → DB: schedule
      ├─ 실시간 스코어 → DB: game_score  (자주 갱신, Redis 캐싱)
      └─ 뉴스         → DB: news

[클라이언트 요청]
      │
      └─ /api/{domain} → Spring Boot → DB or Redis → JSON 응답
```

---

## DB 테이블 (예정)

| 테이블 | 주요 컬럼 | 갱신 주기 |
|---|---|---|
| `team_ranking` | rank, team, games, win, lose, draw, win_rate | 1일 1회 |
| `game_score` | game_id, date, home, away, home_score, away_score, status, inning | 5분 간격 (시즌 중) |
| `schedule` | game_id, date, time, home, away, stadium | 1일 1회 |
| `batter_stats` | name, team, avg, hr, rbi, ... | 1일 1회 |
| `pitcher_stats` | name, team, era, w, l, sv, whip, ... | 1일 1회 |
| `news` | title, link, source, published_at | 1시간 1회 |

---

## API 엔드포인트 (예정)

| Method | URL | 설명 |
|---|---|---|
| GET | `/api/games/today` | 오늘 경기 전체 |
| GET | `/api/ranking` | KBO 팀 순위 |
| GET | `/api/stats/batters` | 타자 스탯 |
| GET | `/api/stats/pitchers` | 투수 스탯 |
| GET | `/api/schedule?year=&month=` | 월별 경기 일정 |
| GET | `/api/news` | 최신 뉴스 |

---

## 탭 구조 (프론트)

| 탭 | 경로 | 상태 |
|---|---|---|
| 실시간 | `/` | ✅ UI 완성 (목업) |
| 순위 | `/ranking` | 🔲 미구현 |
| 기록 | `/stats` | 🔲 미구현 |
| 일정 | `/schedule` | 🔲 미구현 |
| 팬허브 | `/fan` | 🔲 미구현 |

---

## 진행 현황

### 완료
- [x] Python 크롤러 전체 (5개 모듈, KBO 공식 API 기반으로 수정)
- [x] React 프로젝트 세팅 (Vite + TS + Tailwind + Router + Query + Zustand)
- [x] 앱 기본 레이아웃 (모바일 앱 스타일, 하단 탭바)
- [x] 실시간 스코어 페이지 UI (히어로즈 카드 + 다른 경기 리스트)
- [x] 로고 / 파비콘 / 테마 색상 설정

### 진행 중
- [ ] Spring Boot 백엔드 프로젝트 세팅 (IntelliJ)

### 예정
- [ ] DB 스키마 작성 (Flyway 마이그레이션)
- [ ] 크롤러 → DB 저장 기능 추가 (SQLAlchemy)
- [ ] Spring Boot REST API 구현
- [ ] 프론트 나머지 페이지 UI (순위, 기록, 일정, 팬허브)
- [ ] 프론트 API 연결 (목업 → 실제 API)
- [ ] Docker Compose 통합 (MariaDB + Redis)
