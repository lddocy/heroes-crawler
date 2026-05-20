# HEROES 앱 기능 명세

키움 히어로즈 팬 전용 앱. 히어로즈 정보가 항상 메인.
팀 컬러: `#570514` (버건디)

---

## 탭 구조 (하단 탭바 5개)

| 탭 | 경로 | 설명 |
|---|---|---|
| 실시간 | `/` | 오늘 경기 스코어 |
| 순위 | `/ranking` | KBO 팀 순위 |
| 기록 | `/stats` | 팀/선수 스탯 |
| 일정 | `/schedule` | 캘린더 + 티켓팅 |
| 팬허브 | `/fan` | 인스타그램 + 히어로즈샵 |

---

## 기능 상세

### 1. 실시간 스코어 (`/`)
- 히어로즈 경기 카드 최상단 강조 (버건디 배경, 크게)
  - 진행 중: 이닝, 현재 스코어, LIVE 배지 + 초록 점 애니메이션
  - 경기 전: 시간, 선발 투수
  - 종료: 최종 스코어
- 오늘의 다른 KBO 경기는 하단 리스트로 표시

---

### 2. 순위 (`/ranking`)
- KBO 팀 순위 테이블
- 키움 행 버건디 하이라이트
- 표시 항목: 순위, 팀명, 경기 수, 승/패/무, 승률, 게임차

---

### 3. 기록 (`/stats`)
- 상단 탭: **히어로즈 선수** / **KBO 전체**
- 히어로즈 탭: 타자·투수 서브탭, 히어로즈 선수만 필터
- KBO 전체 탭: 타율 TOP / ERA TOP 리스트
- 팀 기록 섹션 (시즌 득점, 평균자책, 실책 등)

---

### 4. 일정 (`/schedule`)
#### 캘린더
- 히어로즈 경기 일정만 표시하는 월간 캘린더
- **홈 경기**: 버건디(`#570514`) 배경 날짜 셀
- **원정 경기**: 흰색 배경, 버건디 텍스트
- 날짜 클릭 → 상세 모달: 상대팀, 시간, 경기장

#### 티켓팅 바로가기
- 경기 상세 모달 내 "티켓 구매" 버튼
- **nol티켓(인터파크) URL 포맷**
  - 팀 전체 일정 페이지: `https://ticket.interpark.com/Contents/Sports/GoodsInfo?SportsCode=07001&TeamCode=PB003`
  - 모바일: `https://ticket.interpark.com/m-ticket/Sports/GoodsInfo?SportsCode=07001&TeamCode=PB003`
  - 개별 경기: `https://tickets.interpark.com/goods/{GOODS_NO}` → GOODS_NO는 경기별 동적 값 (크롤러로 수집 필요)
- **1차: 팀 페이지 URL로 이동** → `ticket.interpark.com/Contents/Sports/GoodsInfo?SportsCode=07001&TeamCode=PB003`
- 2차 (추후): 경기별 GOODS_NO 크롤링 후 해당 경기 직접 연결

---

### 5. 팬 허브 (`/fan`)
#### 히어로즈 인스타그램 ⏸ 보류
- Graph API → 관리자 권한 필요, 불가
- iframe → Instagram X-Frame-Options으로 차단
- **가장 나중에 다시 검토**

#### 히어로즈샵
- 공식 온라인 샵 바로가기
- 신상품·추천 상품 카드 미리보기 (웹뷰 or 외부 링크)

---

## 미결 사항

- [ ] 백엔드 API 설계 (Spring Boot)
- [ ] 크롤러 → DB 저장 연동
- [ ] Instagram Graph API 메타 개발자 계정 등록 및 액세스 토큰 발급
- [ ] 경기별 nol티켓 GOODS_NO 수집 크롤러 추가 (1차는 팀 페이지 URL로 대체)
- [ ] 히어로즈샵 웹뷰 vs 외부 링크 결정
- [ ] 푸시 알림 여부 (경기 시작 알림 등)
