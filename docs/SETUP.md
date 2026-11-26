# 하루잠금 설치 안내 (1단계, 시험판)

> **먼저 읽어 주세요**
>
> - 이 앱은 **아직 한 번도 빌드하거나 휴대폰에서 실행해 본 적이 없습니다.** 코드는 읽어서만 검토했습니다. 빌드가 실패하거나 앱이 바로 꺼질 수 있습니다.
> - 빌드나 명령이 실패하면 **오류 글 전체를 복사해서** Claude에게 보내 주세요. 짐작으로 고치지 마세요.
> - 처음에는 **시험판(debug)** 만 설치합니다. 시험판은 PC 명령으로 언제든 해제할 수 있습니다.
> - **정식판(release)은 시험판을 1주 이상 쓰고, 비상 해제까지 휴대폰에서 시험한 뒤에만** 설치합니다(8장). 정식판은 USB 디버깅을 막으므로 PC로 풀 수 없고, 비상 해제(24시간 대기)만 남습니다.
> - 시험 순서와 기록표는 [TEST.md](TEST.md)에 있습니다. **다른 시험보다 PC 해제 명령 시험을 먼저** 합니다.

설치 순서 한눈에 보기:

1. PC 준비 (Android Studio, 코드 받기, 빌드)
2. 휴대폰 백업
3. 계정 삭제, 보안 폴더·듀얼 메신저 제거
4. "보안 위험 자동 차단" 끄기
5. 개발자 옵션과 USB 디버깅 켜기
6. 설치와 기기 소유자 지정 (+ 해제 명령 먼저 시험)
7. 앱 안의 설정 안내 마치기, 잠금 시작

---

## 1. PC 준비

컴퓨터가 Windows인지 Mac인지에 따라 다른 부분은 따로 적었습니다.

### 1-1. Android Studio 설치

- https://developer.android.com/studio 에서 내려받아 설치합니다.
  - Windows: 내려받은 `.exe`를 실행하고 기본값으로 "Next"를 누릅니다.
  - Mac: `.dmg`를 열고 Android Studio를 "응용 프로그램" 폴더로 끌어 놓습니다. Apple 칩(M1 이후)인지 Intel인지 맞는 파일을 고릅니다.
- 처음 실행하면 설치 마법사가 나옵니다. "Standard"를 고르고 끝까지 진행합니다. 이때 Android SDK와 adb가 함께 설치됩니다.
- **JDK(자바)는 따로 설치하지 않아도 됩니다.** Android Studio 안에 들어 있는 JDK(JBR)를 씁니다.
- 컴퓨터 사양이 낮으면 첫 빌드에 10~30분 걸릴 수 있습니다. 다른 프로그램을 닫아 두세요.

### 1-2. 코드 받기 (GitHub `rkm0418/claude`, 브랜치 `harulock`)

둘 중 하나를 고릅니다. 처음이면 **가)** 가 쉽습니다.

**가) ZIP으로 받기**

1. 브라우저에서 https://github.com/rkm0418/claude 를 엽니다.
2. 왼쪽 위의 브랜치 버튼(보통 `main`)을 눌러 **`harulock`** 을 고릅니다.
3. 초록색 **Code** 버튼 → **Download ZIP**.
4. 압축을 풉니다. 폴더 이름은 `claude-harulock`처럼 됩니다.
   - **Windows: 경로에 한글이나 빈칸이 없는 곳**에 둡니다. 예: `C:\harulock`. 한글 경로에서는 빌드가 실패할 수 있습니다.
   - Mac: 예: `~/harulock`. ZIP으로 받으면 실행 권한이 빠질 수 있으니 1-4의 `chmod` 명령을 한 번 실행합니다.

**나) git으로 받기** (git이 설치되어 있을 때)

```bash
git clone -b harulock https://github.com/rkm0418/claude.git harulock
```

나중에 새 코드를 받을 때는 그 폴더에서 `git pull` 합니다.

### 1-3. Android Studio에서 열고 첫 동기화

1. Android Studio → **Open** → 받은 폴더(안에 `settings.gradle.kts`가 있는 폴더)를 고릅니다.
2. "Trust Project?"가 나오면 **Trust Project**.
3. 오른쪽 아래에 "Gradle sync" 진행 표시가 끝날 때까지 기다립니다. 처음에는 인터넷에서 많이 내려받습니다.
4. 자주 나오는 메시지:
   - **"Android Gradle Plugin 업그레이드" 제안**: 누르지 말고 닫습니다("Don't ask for this project" 또는 "Remind me later"). 버전을 바꾸면 다른 문제가 생길 수 있습니다.
   - **"Failed to find target android-36" / SDK가 없다는 오류**: 메시지 안의 "Install missing ..." 링크를 누르거나, 메뉴 **Tools → SDK Manager**에서 **Android 16 (API 36)** 을 체크해 설치합니다.
   - 그 밖의 빨간 오류: 아래 "Build" 창의 글을 전부 복사해서 보내 주세요.

Android Studio가 처음 열면서 `local.properties`(SDK 위치)를 만듭니다. 이 파일은 GitHub에 올리지 않습니다.

### 1-4. 터미널 준비 (명령 입력 창)

이 문서의 명령은 **받은 코드 폴더 안에서** 실행합니다. Android Studio 아래쪽의 **Terminal** 탭을 쓰면 이미 그 폴더에서 열립니다.

**Windows (PowerShell)** — Android Studio Terminal 탭은 보통 PowerShell입니다. 터미널을 새로 열 때마다 아래 두 줄을 먼저 붙여 넣습니다.

```powershell
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
Set-Alias adb "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
```

- Windows에서는 `./gradlew` 대신 **`.\gradlew.bat`** 를 씁니다. 예: `.\gradlew.bat :core:test`
- adb 위치: `C:\Users\<사용자이름>\AppData\Local\Android\Sdk\platform-tools\adb.exe`
- Android Studio를 다른 곳에 설치했다면 `jbr` 경로를 그 위치로 바꿉니다.

**Mac (터미널)** — 터미널을 새로 열 때마다 아래 두 줄을 먼저 붙여 넣습니다.

```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export PATH="$PATH:$HOME/Library/Android/sdk/platform-tools"
chmod +x gradlew   # ZIP으로 받았을 때 한 번만
```

- adb 위치: `~/Library/Android/sdk/platform-tools/adb`

확인: `adb version` 을 입력해 버전이 나오면 됩니다.

### 1-5. 핵심 로직 시험

```bash
./gradlew :core:test          # Mac
.\gradlew.bat :core:test      # Windows
```

- 끝에 **BUILD SUCCESSFUL** 이 나오면 통과입니다. 자세한 결과: `core/build/reports/tests/test/index.html`
- 참고: `tools/test-core.sh`는 Claude 작업 환경 전용입니다(`/opt/gradle/lib`을 씀). PC에서는 위 명령을 씁니다.
- 이 명령도 Android 설정을 함께 읽으므로 Android Studio와 SDK가 설치되어 있어야 합니다. (Claude 환경에서는 Google 저장소에 접속할 수 없어 이 Gradle 명령 자체는 아직 실행해 보지 못했습니다. 같은 시험 137개는 `tools/test-core.sh`로 통과했습니다.)

### 1-6. 시험판 빌드

```bash
./gradlew :app:assembleDebug        # Mac
.\gradlew.bat :app:assembleDebug    # Windows
```

- 결과 파일: `app/build/outputs/apk/debug/app-debug.apk`
- 메뉴로 해도 됩니다: **Build → Build Bundle(s) / APK(s) → Build APK(s)** (버전에 따라 **Build → Generate App Bundles or APKs → Generate APKs**).
- 실패하면 "Build" 창이나 터미널의 오류 글 전체를 복사해서 보내 주세요.
- **Android Studio의 초록색 실행(▶) 버튼은 쓰지 마세요.** 설치는 아래 adb 명령으로 합니다.

### 1-7. 서명 키(debug.keystore) 백업 — 꼭 하세요

첫 빌드 때 PC에 서명 키가 만들어집니다. 시험판과 정식판 모두 이 키로 서명합니다.

- Windows: `C:\Users\<사용자이름>\.android\debug.keystore`
- Mac: `~/.android/debug.keystore` (Finder에서 숨은 폴더는 `Cmd + Shift + .` 로 보입니다)

이 파일을 USB 메모리나 클라우드에 복사해 두세요. PC를 바꾸거나 키가 지워지면, 잠금 중인 앱을 업데이트할 수 없습니다(서명이 달라 설치가 거부되고, 잠금 중에는 앱을 지울 수도 없습니다). 이 키는 비밀번호가 없는 개발용 키라 GitHub에는 올리지 않습니다.

---

## 2. 휴대폰 백업 (꼭 먼저)

3장에서 계정과 보안 폴더를 지우면 일부 데이터가 사라질 수 있습니다. 먼저 백업합니다.

- **Smart Switch**(PC용)로 휴대폰 전체를 PC에 백업하는 것이 가장 쉽습니다.
- 사진·동영상: PC로 복사하거나 Google 포토 백업이 끝났는지 확인합니다.
- 카카오톡 등 메신저: 앱 안의 "대화 백업"을 합니다.
- **보안 폴더 안의 사진·파일·앱 데이터**: 보안 폴더를 지우면 함께 사라집니다. 먼저 밖으로 옮기거나 백업합니다.
- **듀얼 메신저로 만든 두 번째 앱**: 끄면 그 앱의 데이터가 지워집니다. 먼저 그 앱 안에서 백업합니다.
- Samsung Wallet(삼성 페이)·Samsung Pass: 삼성 계정을 지우면 카드나 저장된 로그인을 다시 등록해야 할 수 있습니다.
- 은행·인증서 앱: 계정 삭제로 보통 지워지지 않지만, 혹시 모르니 인증서 백업/내보내기를 해 둡니다.

## 3. 계정 삭제, 보안 폴더·듀얼 메신저 제거

기기 소유자 지정(`dpm set-device-owner`)은 **휴대폰에 계정이 하나도 없고, 사용자(보안 폴더 등)가 하나뿐일 때만** 됩니다.

1. **계정 삭제**: 설정 → 계정 및 백업 → 계정 관리 → 목록의 계정을 하나씩 눌러 **계정 삭제**.
   - Google, 삼성 계정, 그리고 목록에 보이는 **모든** 계정(메신저, 이메일 등).
   - 삼성 계정은 비밀번호를 물어봅니다. 비밀번호를 미리 확인해 두세요.
   - Google 계정을 지우면 도난 방지 기능(초기화 보호)과 동기화가 잠시 꺼집니다.
2. **보안 폴더 제거**: 보안 폴더 → 오른쪽 위 ⋮ → 설정 → 더보기(⋮) → **제거**. (2장 백업 먼저)
3. **듀얼 메신저 끄기**: 설정 → 유용한 기능 → 듀얼 메신저 → 켜진 앱을 모두 끕니다. (2장 백업 먼저)
4. 그 밖에 업무 프로필 같은 것이 있으면 제거합니다.

PC에 연결한 뒤(5장 이후) 아래로 확인할 수 있습니다.

```bash
adb shell pm list users       # "UserInfo{0:..." 한 줄만 있어야 함
adb shell dumpsys account     # 앞부분 "Accounts: 0" 이어야 함
```

**계정은 기기 소유자 지정이 끝난 뒤 다시 추가해도 됩니다.** 이 앱은 계정 추가를 막지 않습니다. 다만 나중에 정식판을 설치할 때(8장) 다시 모두 지워야 합니다. 보안 폴더와 듀얼 메신저는 잠금 중에는 새로 만들 수 없습니다.

## 4. "보안 위험 자동 차단" 끄기

이 기능이 켜져 있으면 USB로 보내는 명령과 앱 설치가 막힙니다.

- 설정 → **보안 및 개인정보 보호** → **보안 위험 자동 차단** → 끔.
- (삼성 서비스 안내 페이지로 메뉴 이름을 확인했습니다. One UI 버전에 따라 위치가 조금 다를 수 있으니, 안 보이면 설정 검색창에 "자동 차단"을 입력하세요.)
- 시험판을 쓰는 동안은 꺼 두어야 PC 해제 명령을 쓸 수 있습니다.

## 5. 개발자 옵션과 USB 디버깅

1. 설정 → **휴대전화 정보** → **소프트웨어 정보** → **빌드번호**를 7번 연속 누릅니다. 화면 잠금 PIN을 넣으면 "개발자 모드를 켰습니다"가 나옵니다.
2. 설정 맨 아래 **개발자 옵션** → **USB 디버깅** 켜기.
3. **Windows만**: 삼성 USB 드라이버를 설치합니다. 검색어 "Samsung Android USB Driver" → 삼성 개발자 사이트(developer.samsung.com)에서 받아 설치. Mac은 필요 없습니다.
4. USB 케이블로 PC에 연결합니다. 휴대폰에 **"USB 디버깅을 허용하시겠습니까?"** 가 뜨면 "이 컴퓨터에서 항상 허용"을 체크하고 **허용**.
5. PC에서 확인:

   ```bash
   adb devices
   ```

   `R5C...    device` 처럼 **device**가 보이면 됩니다. `unauthorized`면 휴대폰 화면의 허용 창을 확인하고, 아무것도 안 나오면 케이블(충전 전용 케이블은 안 됨), USB 드라이버, 4장 설정을 확인합니다.

## 6. 설치와 기기 소유자 지정

받은 코드 폴더 안에서 실행합니다.

```bash
adb install -t app/build/outputs/apk/debug/app-debug.apk
adb shell dpm set-device-owner app.harulock/.admin.AdminReceiver
adb shell dpm remove-active-admin app.harulock/.admin.AdminReceiver   # 시험판 해제
```

- 첫 줄: 시험판 설치. `-t`는 시험판(testOnly) 설치에 꼭 필요합니다. 끝에 `Success`가 나와야 합니다.
- 둘째 줄: 기기 소유자 지정. `Success: Device owner set to package ...` 가 나와야 합니다.
- 셋째 줄: **시험판 해제 명령.** 기기 소유자를 PC에서 바로 풉니다. 시험판에서만 됩니다.

**처음에는 이렇게 합니다** ([TEST.md](TEST.md) 0번):

1. 설치 → 소유자 지정 → `adb shell dpm list-owners` 로 `app.harulock` 이 보이는지 확인.
2. **잠금을 시작하기 전에** 해제 명령을 실행하고, 다시 `adb shell dpm list-owners` 로 사라졌는지 확인.
3. 해제가 되는 것을 본 뒤에만 다시 소유자를 지정하고 다음으로 넘어갑니다. **해제가 안 되면 멈추고 오류를 보내 주세요.**

자주 나오는 오류:

| 오류 글에 있는 말 | 뜻과 해결 |
|---|---|
| `already some accounts on the device` | 계정이 남아 있음. 3장을 다시 확인. `adb shell dumpsys account` 로 어떤 앱의 계정인지 보고 지웁니다. |
| `already several users` / `multiple users` | 보안 폴더·듀얼 메신저 등이 남아 있음. 3장 확인. |
| `INSTALL_FAILED_TEST_ONLY` | 설치 명령에 `-t`가 빠짐. |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | 서명 키가 다름. 1-7의 키를 쓰는 PC에서 빌드해야 함. |
| `Unknown admin` | 앱이 설치되지 않았거나 이름이 틀림. 명령을 그대로 복사. |
| `Not allowed to remove ...` / `testOnly` 관련 | 정식판이거나 `-t` 없이 설치된 앱. 해제 명령은 시험판에서만 됩니다. |

설치할 때 Play 프로텍트가 경고하면, 직접 만든 앱이므로 "그래도 설치"를 고릅니다.

### 시험판 앱 업데이트

새 코드로 다시 빌드한 뒤, 잠금 중이어도 아래로 덮어 설치할 수 있습니다(같은 서명 키 필요).

```bash
adb install -r -t app/build/outputs/apk/debug/app-debug.apk
```

## 7. 앱 안의 설정 안내 마치기, 잠금 시작

하루잠금 앱 → **설정 안내** 의 다섯 단계를 위에서부터 합니다.

1. 기기 소유자 (필수): 6장에서 끝났으면 완료로 바뀝니다.
2. 사용 정보 접근 (필수): "열기" → 하루잠금 켜기.
3. 접근성 (필수): "열기" → 설치된 앱(또는 설치된 서비스) → 하루잠금 → 켜기.
   - 스위치가 회색이라 안 켜지면 "제한된 설정"입니다. 설정 → 애플리케이션 → 하루잠금 → 오른쪽 위 ⋮ → **제한된 설정 허용** 을 누른 뒤 다시 켭니다. (adb로 설치한 앱에도 이 제한이 걸리는지는 확인하지 못했습니다. 걸리면 위 방법으로 풉니다.)
4. 알림 (권장): 허용.
5. 배터리 제한 해제 (권장): "열기" → 허용. 그리고 설정 → 애플리케이션 → 하루잠금 → 배터리 → **제한 없음** 도 확인합니다. (메뉴 이름은 One UI 버전에 따라 다를 수 있습니다.)

**4·5단계는 꼭 잠금 시작 전에 하세요.** 잠금 중에는 화면에 "하루잠금"이 보이는 설정 화면이 바로 닫힙니다.

**잠금 전에 허용앱을 정해 두세요.** 잠금 중에 허용앱을 추가하면 다음 초기화부터 적용됩니다. 잠금 중에는 허용앱과 전화(기본 전화 앱, 긴급 통화)만 쓸 수 있고, 나머지 앱은 "일시 중지됨"이 됩니다. 아래 앱은 넣을지 꼭 생각해 보세요.

- **시계(알람)**: 정지되면 아침 알람이 울리지 않을 수 있습니다(시험으로 확인 필요).
- **메시지(문자)**: 정지되면 문자를 볼 수 없고, 112·119 **문자 신고**도 이 앱으로 합니다.
- 인증 앱(PASS, 은행 OTP), 지도, 카메라 등 꼭 필요한 앱.

그다음 **요일별 설정**에서 요일마다 한도와 하루 시작 시각을 정합니다(저장하지 않으면 매일 120분, 05:00 시작, 허용앱 없음). 처음 시험할 때는 [TEST.md](TEST.md) 1번의 값으로 정합니다.

마지막으로 설정 안내 → **잠금 시작**.

## 8. 정식판으로 바꾸기 (1주 이상 시험한 뒤에만)

조건: 시험판을 **1주 이상** 썼고, [TEST.md](TEST.md)의 모든 항목, 특히 **비상 해제(24시간 완료 시험 포함)** 가 통과했을 것.

정식판은 잠금 중 **USB 디버깅을 막습니다.** PC 해제 명령이 듣지 않고, 풀려면 앱 안의 비상 해제(요청 후 24시간 대기)뿐입니다.

1. 해제: 시험판 해제 명령(6장 셋째 줄) 또는 앱의 비상 해제.
2. 삭제: `adb uninstall app.harulock` (설정과 기록도 지워집니다)
3. 빌드: `./gradlew :app:assembleRelease` (Windows: `.\gradlew.bat :app:assembleRelease`) → `app/build/outputs/apk/release/app-release.apk`
4. 설치: `adb install app/build/outputs/apk/release/app-release.apk` (`-t` 없이)
5. 소유자 설정: 3장대로 **계정을 다시 모두 지우고**, `adb shell dpm set-device-owner app.harulock/.admin.AdminReceiver`
6. 7장을 다시 합니다(권한, 허용앱, 요일별 설정, 잠금 시작).

## 9. 알아 두면 좋은 점 (현재 코드 기준)

- **긴급 통화와 기본 전화 앱은 절대 정지되지 않게** 만들었습니다. 기본 전화 앱, 전화 화면을 여는 시스템 앱, 긴급 관련 시스템 앱(삼성 안전 앱 등)은 정지 대상에서 빠지고 시간도 줄지 않습니다. 설치 직후 꼭 확인합니다([TEST.md](TEST.md) 2번). **시험 삼아 112·119에 실제로 전화하지 마세요.** 화면이 열리는지만 봅니다.
- 시간이 줄지 않는 곳: 홈 화면, 허용앱, 하루잠금 앱, 전화 앱, 화면이 꺼졌거나 잠금 화면일 때. **설정 앱을 쓰는 시간은 줄어듭니다.**
- 한도 줄이기와 허용앱 빼기는 바로 적용되고, 한도 늘리기·허용앱 추가·시작 시각 변경은 다음 초기화부터 적용됩니다.
- 하루 시작 시각을 **더 이른 시각으로** 바꾸면, 바뀌는 그 하루가 48시간 가까이 길어질 수 있고 그동안 한도는 한 번만 주어집니다. 요일마다 시작 시각이 다르거나 해외에서 시간대가 바뀌면 하루가 24시간보다 짧아질 수도 있습니다.
- 잠금 중 막히는 것: 이 앱 삭제·강제 종료·데이터 삭제, 안전 모드, 공장 초기화(설정 메뉴), 날짜·시간 직접 변경(자동 시간이 켜짐), 사용자·보안 폴더 추가. 정식판은 USB 디버깅도.
- 비상 해제 요청은 Android 13 이상에서 **인터넷 시각**이 필요합니다. 재부팅 후 인터넷에 한 번도 연결하지 않았으면 "인터넷에 연결한 뒤 다시 요청해 주세요"가 나옵니다. 요청 뒤 기다리기·취소·해제는 인터넷 없이 됩니다.
- 비상 해제 후 "자동 시간" 설정이 잠금 전 값으로 돌아오지 않을 수 있습니다. 그러면 설정 → 일반 → 날짜 및 시간에서 직접 바꿉니다.
- 알려진 빈틈(1단계에서는 막지 않음):
  - 화면 속 화면(PIP)으로 보는 영상은 시간이 줄지 않습니다.
  - 잠금 화면 위에 뜨는 앱 화면(예: 잠금 화면에서 연 카메라)은 시간이 줄지 않습니다.
  - **다른 홈 앱(런처)을 설치하면 그 앱은 잠기지 않습니다.** 고칠 예정입니다. 다른 런처를 설치하지 마세요.
  - 휴대폰의 시간 변경 제한이 뚫리면, 시간을 앞당기고 재부팅해 대기 시간을 줄일 수 있습니다.
  - 복구 모드(버튼 조합)의 초기화, 원격 초기화, 펌웨어 다시 설치는 앱이 막을 수 없습니다. 시험하지 마세요(데이터가 모두 지워집니다).

## 10. 2026년 Android 설치 규칙 참고

- **개발자 인증(Developer verification)**: Google은 2026년 9월 30일부터 브라질·인도네시아·싱가포르·태국에서, 2027년부터 전 세계에서 인증되지 않은 개발자의 앱 설치를 제한합니다. Google 안내에 따르면 **자기 기기에 adb로 설치하는 것은 계속 허용**됩니다. 한국은 2026년 첫 대상에 없습니다(2026-11 기준 Google 도움말과 기사로 확인).
- **제한된 설정**: Android 13부터, 파일이나 브라우저로 설치한 앱은 접근성 같은 민감한 설정을 바로 켤 수 없습니다. adb 설치에도 해당하는지는 확인하지 못했습니다. 걸리면 7장 3번의 "제한된 설정 허용"으로 풉니다.
- **시험판(testOnly) 설치**: `adb install -t` 로만 설치됩니다. 휴대폰에서 파일을 눌러 설치하는 방법은 안 됩니다.
