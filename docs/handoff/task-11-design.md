# Design brief, stage 1 (copied from the design request given to the designer)

## Direction
- Calm and simple. Remaining time must be seen first.
- Light and dark theme. No breakage at 360-412dp width. Buttons at least 48dp high; scroll so large font stays readable.
- Buttons that start a lock or are hard to undo are clearly distinct from normal buttons.
- Do not copy existing apps' screens, icons or names.

## Screens (design every state)
| Screen | Shows | Actions | States |
|---|---|---|---|
| 홈 | 남은 시간(가장 크게), 현재 상태, 다음 초기화 시각, 다음 초기화부터 적용될 변경 안내 | 즉시 잠금, 설정, 설정 안내, 비상 해제 | 시작 전, 사용 중, 10분 이하, 한도 잠금, 즉시 잠금, 권한 꺼짐 잠금 |
| 요일별 설정 | 월~일마다 하루 한도(분)와 하루 시작 시각 | 시간 선택, 허용앱 고르기, 저장 | 기본, 입력 오류, 다음 초기화 적용 대기 |
| 허용앱 | 검색칸, 앱 목록(아이콘, 이름, 체크) | 선택, 완료 | 기본, 검색 결과 없음, 브라우저·스토어 선택 경고 창 |
| 즉시 잠금 (작은 창) | 30분·1시간·2시간 버튼, 직접 입력(1~1440분), "끝나기 전에는 취소할 수 없어요" 경고 | 시작, 닫기 | 기본, 입력 오류 |
| 설정 안내 | 5단계: 기기 소유자, 사용 정보 접근, 접근성, 알림, 배터리 제한 해제 | 단계별 열기, 잠금 시작 | 미완료, 완료, 필수 3단계 전에는 잠금 시작 비활성 |
| 비상 해제 | 설명, 현재 상태, 남은 대기 시간 | 요청, 요청 취소, 해제 확인 | 요청 전, 24시간 대기 중, 확인 가능(24시간 동안), 만료, 해제 완료 |

The system dialog for a suspended app is not designed. Notifications use the system look; only a small icon is needed. The ongoing notification text is "하루잠금 실행 중"; remaining time appears only in the 10/5/1 minute warnings.

## Delivery rules (the designer will later replace res/ files; Kotlin must keep working unchanged)
- XML layouts, not Compose. Only Android framework Views. No Material Components, AndroidX UI, external fonts.
- Theme name `Theme.Harulock`, parent in the `android:Theme.Material` NoActionBar family.
- Every screen's top layout has `android:fitsSystemWindows="true"`.
- Screen text in `strings.xml`, colors in `colors.xml`; every state text is in `strings.xml`.
- State color names: `status_normal`, `status_warning`, `status_locked`.
- Icons are newly drawn vector drawables.

## Layout files and element IDs (res/layout/; prefixes tv text, btn button, input field, img image, cb checkbox)
| File | IDs |
|---|---|
| activity_main.xml | tv_status, tv_remaining, tv_next_reset, tv_pending_change, btn_instant_lock, btn_settings, btn_setup, btn_release |
| activity_settings.xml | day_mon, day_tue, day_wed, day_thu, day_fri, day_sat, day_sun (each an include of item_day), btn_allowed_apps, tv_pending_notice, btn_save |
| item_day.xml | tv_day, input_limit, btn_start_time, tv_error |
| activity_allowed_apps.xml | input_search, list_apps (ListView), tv_empty, btn_done |
| item_app.xml | img_icon, tv_app_name, cb_allowed |
| dialog_instant_lock.xml | btn_30m, btn_1h, btn_2h, input_minutes, tv_warning, tv_error, btn_start, btn_cancel |
| activity_setup.xml | step_owner, step_usage, step_accessibility, step_notification, step_battery (each an include of item_setup_step), btn_arm |
| item_setup_step.xml | img_state, tv_title, tv_desc, btn_action |
| activity_release.xml | tv_release_desc, tv_release_state, tv_release_remaining, btn_request, btn_cancel_request, btn_confirm |

## Other files (res/)
- values/colors.xml, values-night/colors.xml
- values/styles.xml, values/dimens.xml, values/strings.xml
- drawable/ic_step_done.xml, drawable/ic_step_todo.xml, drawable/ic_notification.xml (single white color)
- mipmap-anydpi-v26/ic_launcher.xml, drawable/ic_launcher_foreground.xml, drawable/ic_launcher_background.xml
- background/button drawables the layouts need
