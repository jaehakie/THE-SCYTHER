# 팀 작업과 변경 통합

## 브랜치와 Pull Request

`main`은 팀이 함께 실행할 수 있는 기준 버전입니다. 첫 업로드 이후 기능별 브랜치에서 작업하고, Pull Request로 변경 내용을 확인한 뒤 합칩니다.

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/character-dialogue
```

브랜치 이름은 `feat/…`, `fix/…`, `docs/…`처럼 목적이 드러나게 정합니다. 위 이름은 예시입니다.

변경한 파일만 선택해서 커밋하고 자신의 브랜치를 push합니다.

```bash
git status --short
git add services/dialogue.py
git commit -m "feat: 캐릭터 대화 모델 연결"
git push -u origin feat/character-dialogue
```

GitHub에서 해당 브랜치 → `main` Pull Request를 열고, 변경 내용과 확인 방법을 적습니다. 리뷰 후 merge하고 다음 작업 전에 `main`을 다시 받습니다. 다른 팀원이 사용 중인 브랜치의 이력을 임의로 바꾸거나 force push하지 않습니다.

## 커밋 메시지

형식은 `type: 변경 내용`입니다. 필요할 때 `feat(dialogue): …`처럼 범위를 붙일 수 있습니다. 제목은 짧게 쓰고 한 커밋에는 관련된 변경을 담습니다.

| 접두어 | 용도 | 예시 |
| --- | --- | --- |
| `feat:` | 새 기능·사용자가 경험하는 기능 추가 | `feat: 단서에 따른 캐릭터 반응 추가` |
| `fix:` | 잘못된 동작 수정 | `fix: 단서가 중복 등록되는 문제 수정` |
| `docs:` | 문서·설명·주석 수정 | `docs: 로컬 실행 방법 보완` |
| `refactor:` | 기능은 유지하면서 코드 구조 개선 | `refactor: 장면 데이터와 진행 로직 분리` |
| `test:` | 테스트 추가·수정 | `test: 사용자별 진행 기록 분리 검증` |
| `style:` | 동작을 바꾸지 않는 코드 서식 | `style: Python 코드 들여쓰기 정리` |
| `chore:` | 의존성·개발 도구·환경 설정 | `chore: 개발 의존성 업데이트` |
| `ci:` | 자동 검사·배포 워크플로 설정 | `ci: Pull Request 테스트 추가` |

`style:`은 화면 디자인 기능 변경을 뜻하지 않습니다. 사용자 화면 기능은 `feat:` 또는 `fix:`로 기록합니다. 일반적인 설명·주석 변경에는 별도 `comment:` 대신 `docs:`를 사용합니다.

## 프로듀서 콘텐츠 전달

- 장면·단서·인물 이미지에는 고유 ID, 사용 장면, 공개 조건, 설명, 파일 버전을 함께 전달합니다.
- `services/story.py`, `services/endings.py`, `public/assets/audio/audio-config.json`에서 실제 사용 자료를 확인합니다. 자료 변경 후 `python scripts/check_assets.py`로 참조와 파일명을 검증합니다.
- 스토리에서 확정한 사실과 검토 중인 설정을 구분합니다. 확인되지 않은 의혹을 확정 사실로 바꾸지 않습니다.
- 큰 원본 영상 등은 코드 저장소에 무조건 추가하지 말고 공유 위치와 실제 게임용 파일을 구분합니다. GitHub에 올리기 전 파일 크기를 확인합니다.

## 합치기 전 확인

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

화면을 바꿨다면 로컬 서버를 실행해 실제 흐름도 확인합니다. Edge가 설치되어 있으면 `scripts/verify_ui.py`를 사용할 수 있습니다. 실행법은 아래 검증 항목에 있습니다.

- `.venv/`, 캐시, 개인 IDE 설정, 로컬 비밀정보는 올리지 않습니다.
- API 키·DB 비밀번호는 실제 값 대신 환경변수 이름과 설정 방법만 공유합니다.
- 임시 예시 대화와 실제 AI 연결 상태를 구분해서 설명합니다.
- 현재 메모리 세션은 서버 재시작·다중 프로세스에서 유지되지 않습니다. 이 제한을 해결하기 전에는 기록이 영구 저장된다고 설명하지 않습니다.

## 실행 환경과 설정

처음 실행하는 Windows 환경의 명령은 [README](README.md#로컬에서-실행하기)에 있습니다. Python 3.11을 사용하며, macOS/Linux에서는 저장소 루트에서 아래 명령으로 실행합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m uvicorn app:app --reload
```

기존 `.env`가 있다면 필요한 항목만 편집합니다. `app.py`가 시작할 때 루트의 `.env`를 읽으며, 이미 설정된 프로세스 환경변수가 우선합니다. 변경한 값은 서버 재시작 후 적용됩니다.

| 변수 | 설정 |
| --- | --- |
| `CHAT_MODE` | `openai` 또는 `mock`. 미설정 시 `openai`, `.env.example`은 `mock` |
| `OPENAI_API_KEY` | `openai` 모드에서 사용할 서버 측 API 키 |
| `OPENAI_MODEL` | 사용할 Responses API 모델 ID. 예제에는 팀이 선택한 `gpt-6-luna` 설정 |
| `LLM_TIMEOUT_SECONDS` | 기본 45초, 허용 1~50초. 브라우저 요청 제한은 60초 |

`openai` 모드는 키와 모델이 필요합니다. 생성 요청이 실패하면 화면에서 같은 입력을 재시도할 수 있습니다. `mock`은 명시적으로 선택하는 모의 응답 모드입니다. `GET /health`의 `dialogue_mode`에는 설정한 모드가 표시됩니다. 실제 모델 연결과 답변 품질은 대화를 보내 별도로 확인합니다.

## 콘텐츠 편집 위치

| 위치 | 내용 |
| --- | --- |
| `data/character.json` | 이윤제의 말투·가치관·배경·지식 범위·예시 대화·시작 장면·첫 인사 |
| `data/mentor.json` | 스승의 캐릭터 설정 |
| `data/dialogue-scenes.json` | 자유 입력이 있는 8개 장면의 상대와 상황 |
| `data/lorebook.json` | 공개 조건·키워드·근거 상태가 있는 세계관 항목 |
| `services/story.py` | 장면·선택지·계율·단서·이미지·영상 연결 |
| `services/endings.py` | 확정된 엔딩 흐름과 결과 분류 |
| `services/navigation.py` | 뒤로보기가 가능한 사건·선택 경계 |
| `public/assets/audio/audio-config.json` | 장면별 배경음악·효과음·재생 시작 위치 |
| `public/assets/images/`, `videos/`, `sounds/` | 게임에 사용하는 시각·음향 자료 |
| `public/assets/start-screen/` | 시작 화면 코드와 배경·로고 |
| `public/assets/fonts/` | Galmuri 글꼴과 라이선스 |

JSON의 인물 설정과 문구는 해당 파일에서 편집합니다. 분기 ID나 공개 조건을 바꿀 때는 연결된 이야기 로직과 테스트를 함께 확인합니다. 확인된 기획과 임시 해석은 데이터의 근거·상태 필드로 구분합니다.

## 검증

저장소 루트에서 다음 명령을 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_assets.py
node --check public/assets/js/app.js
node --check public/assets/js/audio.js
node --check public/assets/js/endings.js
node --check public/assets/js/rules.js
node --check public/assets/start-screen/main.js
```

`check_assets.py`는 장면·메뉴·글꼴·음향·영상 참조를 따라가며 파일 존재 여부, 빈 파일, Linux 대소문자, GitHub 단일 파일 크기 제한을 확인합니다.

브라우저 검증에는 Playwright와 로컬 Edge가 필요합니다. 모의 서버를 실행하고 다른 터미널에서 검사합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:CHAT_MODE='mock'
.\.venv\Scripts\python.exe -m uvicorn app:app --port 8000
```

```powershell
.\.venv\Scripts\python.exe scripts/verify_ui.py
.\.venv\Scripts\python.exe scripts/verify_scene_completion_ui.py
.\.venv\Scripts\python.exe scripts/verify_ending_collection_ui.py
```

다른 포트를 사용한다면 검사 터미널에 `NOTTODAY_TEST_URL`을 지정합니다. 캡처와 보고서는 로컬 `reference/qa/`에 생성됩니다. README에 사용하는 미리보기는 `.github/images/`에서 관리합니다.

| 검사 | 확인 범위 |
| --- | --- |
| `tests/` | 프롬프트 공개 범위, 세션 분리, 선택 검증, 타이머·엔딩, 뒤로보기, 재시도·동시 요청 |
| `verify_ui.py` | 모바일·PC의 이야기 진행, 영상·단서, 새로고침, 실제 시간 초과 |
| `verify_scene_completion_ui.py` | 전체 장면의 연출 완료 전 진행 차단과 입력·영상 완료 처리 |
| `verify_ending_collection_ui.py` | 일반·배드엔딩 보관, 새 게임·재접속, 중복 저장, 저장 실패·재시도 |

기존 스크립트 경로의 경고 누적은 `test_legacy_warning_escalation_enters_discipline_ending`에서 검증합니다. 현재 자유대화 생성 경로에는 같은 경고 누적 처리가 연결되지 않은 상태이므로, 이 테스트의 통과 결과를 생성 경로의 경고 동작까지 검증한 것으로 설명하지 않습니다.

## 배포 구성

[render.yaml](render.yaml)에 기존 Render 서비스용 구성을 보관합니다. 배포 환경의 변수는 서비스 설정에서 관리합니다.

| 항목 | 저장소 설정 |
| --- | --- |
| Python | `.python-version`의 3.11 |
| 빌드 | `pip install -r requirements.txt` |
| 실행 | `python -m uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1` |
| 상태 확인 | `/health` |
| 인스턴스 | 1개, 자동 배포 꺼짐 |
| 대화 | `CHAT_MODE=openai`, `OPENAI_MODEL`, `OPENAI_API_KEY`, `LLM_TIMEOUT_SECONDS` |

세션은 단일 프로세스의 메모리에 보관하며, 마지막 이용 후 12시간 만료·최대 500개로 관리합니다. 여러 워커나 인스턴스를 사용하려면 세션 저장 구조를 먼저 변경해야 합니다.

배포 확인에는 START부터 준비 장면으로 진입하는 흐름, 자유대화와 반박, 단서 이미지·음향·영상, 최종 선택과 엔딩을 포함합니다. 다른 브라우저의 세션 분리와 같은 브라우저의 엔딩 모음 유지도 확인합니다.
