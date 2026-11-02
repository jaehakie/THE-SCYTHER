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
- `reference/assets.json`에서 현재 이미지와 원본 참조를 확인할 수 있습니다.
- 스토리에서 확정한 사실과 검토 중인 설정을 구분합니다. 확인되지 않은 의혹을 확정 사실로 바꾸지 않습니다.
- 큰 원본 영상 등은 코드 저장소에 무조건 추가하지 말고 공유 위치와 실제 게임용 파일을 구분합니다. GitHub에 올리기 전 파일 크기를 확인합니다.

## 합치기 전 확인

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

화면을 바꿨다면 로컬 서버를 실행해 실제 흐름도 확인합니다. Edge가 설치되어 있으면 `scripts/verify_ui.py`를 사용할 수 있습니다. 실행법은 README에 있습니다.

- `.venv/`, 캐시, 개인 IDE 설정, 로컬 비밀정보는 올리지 않습니다.
- API 키·DB 비밀번호는 실제 값 대신 환경변수 이름과 설정 방법만 공유합니다.
- 임시 예시 대화와 실제 AI 연결 상태를 구분해서 설명합니다.
- 현재 메모리 세션은 서버 재시작·다중 프로세스에서 유지되지 않습니다. 이 제한을 해결하기 전에는 기록이 영구 저장된다고 설명하지 않습니다.
