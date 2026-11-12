# THE SCYTHER · 낫 TODAY

『수확자(Scythe)』를 바탕으로 만든 HateSlop 학회 프로젝트입니다. 수습 수확자가 되어 이윤제의 집을 탐색하고, 인물과 대화하며 단서를 모은 뒤 최종 판단과 엔딩까지 진행합니다.

저장소: [jaehakie/THE-SCYTHER](https://github.com/jaehakie/THE-SCYTHER)

## 주요 기능

- 팀이 제공한 시작 화면에서 START를 누르면 준비 장면부터 새 임무를 시작합니다.
- 입력창이 있는 8개 장면에서 스승·이윤제와 자유대화하고, 명확한 선택 의도는 기존 분기로 연결합니다.
- Character Card, 현재 장면, 공개 가능한 관련 Lorebook, 같은 상대와 나눈 최근 6턴을 답변에 반영합니다.
- 물건 탐색, 단서 노트, 경고, 서버 기준 3초 무음 장면과 60초 최종 판단을 제공합니다.
- 최종 선택·단서·경고·보고에 따른 엔딩과 수확일지를 연결합니다. 일반 엔딩과 배드엔딩 모두 최종 결과 화면에서 엔딩 모음에 보관합니다.
- 대사 타이핑·상황 설명 페이드인·영상·홀로그램이 완료된 뒤 계속·선택·대화 전송을 활성화합니다.
- 이전 장면 다시 보기는 선택·단서·경고 등 진행 기록을 유지합니다.
- 장면별 이미지·영상·음향, 음소거, 계율 다시 보기, 브라우저에 보관하는 엔딩 모음을 제공합니다.

화면은 HTML/CSS/JavaScript, 서버는 Python/FastAPI입니다. 생성 모드는 서버 환경변수로 설정하며, `mock`은 키 없이 연결을 확인하는 명시적인 모의 응답 모드입니다.

## 로컬 실행

Python 3.11 환경에서 검증했습니다. `.python-version`도 3.11을 지정합니다.

```powershell
git clone https://github.com/jaehakie/THE-SCYTHER.git
cd THE-SCYTHER
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

브라우저에서 <http://127.0.0.1:8000>을 엽니다. 서버를 닫을 때는 실행한 터미널에서 `Ctrl+C`를 누릅니다. 기존 `.env`가 있다면 복사로 덮어쓰지 말고 필요한 항목만 수정하세요.

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m uvicorn app:app --reload
```

## 환경변수

`app.py`가 루트의 `.env`를 시작할 때 읽습니다. 프로세스 환경변수가 우선합니다. `.env`를 바꾼 뒤에는 서버를 재시작하세요. API 키는 서버에서만 사용하며 Git에 올리지 않습니다.

| 변수 | 값 |
| --- | --- |
| `CHAT_MODE` | `openai` 또는 `mock`. 미설정 시 `openai`, `.env.example`은 `mock` |
| `OPENAI_API_KEY` | `openai` 모드에서 필요한 API 키 |
| `OPENAI_MODEL` | 팀이 선택한 `gpt-6-luna`; 이용 가능한 모델 ID로 교체 가능 |
| `LLM_TIMEOUT_SECONDS` | 기본 45초, 허용 1~50초. 브라우저 요청 제한은 60초 |

실제 생성 답변은 `CHAT_MODE=openai`, 유효한 키와 모델이 필요합니다. 키가 없거나 요청에 실패하면 오류를 표시하고 같은 입력으로 재시도할 수 있으며, 모의 응답으로 자동 전환하지 않습니다. `GET /health`의 `dialogue_mode`는 설정 모드이며 모델 API의 가용성 검사 결과는 아닙니다.

## Render 배포

이 저장소는 Render 배포를 준비한 상태이며, GitHub 업로드만으로 Render 서비스가 생성되지는 않습니다.

Render에서 **New → Web Service**로 이 저장소의 `main`을 연결합니다.

| 항목 | 설정 |
| --- | --- |
| Runtime | Python 3 |
| Root Directory | 저장소 최상위이므로 비워두기 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health Check Path | `/health` |
| Instance Type | 첫 시연은 Free로 시작 가능 |
| Auto Deploy | 처음에는 Off로 두고 필요한 시점에 수동 배포 |

Render 환경변수에는 `CHAT_MODE=openai`, `OPENAI_MODEL=gpt-6-luna`, `LLM_TIMEOUT_SECONDS=45`와 API 키를 등록합니다. 로컬 `.env`는 전송하지 않습니다. Python 버전은 `.python-version`을 사용합니다.

같은 설정을 담은 `render.yaml`도 제공합니다. Blueprint로 생성할 경우 API 키를 별도로 입력하며, 자동 배포는 꺼져 있습니다. 생성·배포는 Render에서 직접 시작해야 합니다.

배포 후 `/health`, START→준비 장면, 자유대화·반박, 단서 이미지·음향·영상, 최종 선택·엔딩을 확인하세요. 다른 브라우저에서도 접속해 세션이 분리되는지 확인합니다.

공식 안내: [FastAPI 배포](https://render.com/docs/deploy-fastapi), [무료 서비스 제한](https://render.com/docs/free)

## 데이터와 리소스 편집

| 위치 | 내용 |
| --- | --- |
| `data/character.json` | 이윤제의 말투·가치관·배경·지식 범위·예시 대화와 시작 장면·첫 인사 |
| `data/mentor.json` | 스승의 캐릭터 설정 |
| `data/dialogue-scenes.json` | 자유 입력이 있는 8개 장면의 상대와 상황 |
| `data/lorebook.json` | 공개 조건·키워드·근거 상태가 있는 세계관 항목 |
| `services/story.py` | 장면·선택지·계율·단서·이미지·영상 연결 |
| `services/endings.py` | 팀이 확정한 엔딩 흐름과 결과 분류 |
| `public/assets/audio/audio-config.json` | 장면별 배경음악·효과음·재생 시작 위치 |
| `public/assets/images/`, `videos/`, `sounds/` | 게임에서 사용하는 시각·음향 자료 |
| `public/assets/start-screen/` | 시작 화면 코드와 배경·로고 |
| `public/assets/fonts/` | Galmuri 글꼴과 SIL Open Font License |

JSON의 인물 설정과 문구는 코드 수정 없이 편집할 수 있습니다. 분기 ID와 공개 조건을 바꿀 때는 해당 이야기 로직도 함께 확인하세요. 확인된 기획과 임시 해석은 데이터의 근거·상태 필드로 구분합니다.

## 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_assets.py
node --check public/assets/js/app.js
```

`check_assets.py`는 장면·메뉴·글꼴·음향·영상 참조의 파일 존재 여부, 빈 파일, Linux 대소문자, GitHub 단일 파일 크기 제한을 확인합니다.

모바일·PC UI 검증에는 실행 중인 모의 모드 서버, Playwright와 로컬 Edge가 필요합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:CHAT_MODE='mock'
.\.venv\Scripts\python.exe -m uvicorn app:app --port 8000
# 다른 터미널에서
.\.venv\Scripts\python.exe scripts/verify_ui.py
```

검증 캡처와 보고서는 로컬 `reference/qa/`에 생성되며 Git에 올리지 않습니다. 모의 모드 검증은 실제 모델의 말투·사실성·답변 품질 검증과 구분합니다.

## 현재 저장 범위와 제한

- 서버 세션은 메모리에 보관하며 마지막 이용 후 12시간 만료, 최대 500개입니다. 한 프로세스·한 인스턴스로 실행합니다.
- 서버 재시작·Render 절전·재배포 시 진행 기록과 대화 맥락이 사라집니다. 영구 DB는 연결하지 않았습니다.
- Render Free는 요청이 15분 없으면 절전 상태가 될 수 있고 다음 접속 시 준비 시간이 필요합니다.
- 엔딩 모음은 해당 브라우저·접속 주소의 IndexedDB에 저장합니다. 다른 기기·다른 주소로 자동 공유하지 않으며 브라우저 데이터 삭제 시 사라집니다.
- 배드엔딩도 최종 결과 화면에 도달하면 자동 보관합니다. 종료 원인과 이미지·문구를 함께 기록하며 수확일지 입력은 추가하지 않습니다. 같은 플레이의 새로고침·재시도로 기록을 중복 생성하지 않습니다. 이 변경 전에 저장하지 않았던 과거 배드엔딩은 자동 복원하지 않습니다.
- 다른 두 후보는 잠긴 빈 슬롯입니다. 장기 기억·사진 전송·임베딩 검색·사용자 계정은 구현 범위에 포함하지 않았습니다.

캐릭터 카드와 Lorebook 구성은 [SillyTavern](https://github.com/SillyTavern/SillyTavern)의 설계를 참고해 자체 구현했습니다. 협업과 커밋 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md)를 따릅니다.
