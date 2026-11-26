# SDD ledger — plan: docs/superpowers/plans/2026-11-26-stage1-core-lock.md
Spec: Claude Docs design doc (URL in plan header); not readable by subagents, plan Global Constraints stand in.

## Pre-flight scan
| Tasks | Interface | Finding |
|---|---|---|
| 1-2 | Settings/DayRule | consistent |
| 1-3 | Fixtures at() | consistent |
| 1,2,3 -> 4 | DayClock, Settings, MeterState/advance | consistent |
| 4-9 | Engine.step events since countedUntil | CONFLICT: late-logged events would be lost. Ruling R1 |
| 4-5 -> 9,12 | TrustedClock, EmergencyRelease | consistent |
| 4-6-8 | CoreState / StateCodec / StateStore | consistent |
| 7-9,10 | DeviceApps, shouldCloseSettings | consistent |
| 8-9 | unarmed settings have no defined storage. Ruling R2 |
| 8-11 | strings/res needed before Task 11. Ruling R3 |
| 9-10 | accessibility component name used before created. Ruling R4 |
| 9-12 | `released` file used before created; arm must delete. Ruling R5 |
| each task 1-7 | tests vs interfaces; counts 4,8,15,23,30,34,40 | consistent |
| each task 8-13 | no Android SDK here: build steps cannot run. Ruling R6 |

Ruling: R1 Task 9 reads events from countedUntil minus 10s (replay is idempotent) — avoids lost Resumed — cost: slightly more reads.
Ruling: R2 before arming, store Engine.arm(settings).copy(armed=false) — one storage path — cost: unused period fields.
Ruling: R3 Task 8 creates res/values/strings.xml with app_name "하루잠금"; later tasks add strings — manifest needs it — cost: none.
Ruling: R4 accessibility service class is app.harulock.service.SettingsWatchService — cost: none.
Ruling: R5 release files live in device-protected filesDir: release.txt, released; Task 12 adds deletion in Controller.arm — cost: none.
Ruling: R6 Tasks 8-13 are written and reviewed by reading only; PC build/device steps recorded as UNVERIFIED — cost: compile errors surface on PC.
Task 1: complete (commits 7f622b0..0d2217a, review clean)
  Minor (for final review): startOf ordering can break with DST gap across midnight (not Seoul); no tests for DayRule bounds / 7-day requirement / forward loop; test script leaves temp dir, no -jvm-target.
Ruling: R7 test counts in the plan are indicative; extra tests are allowed — coverage matters more than counts — cost: none.
Task 2: complete (commits 0d2217a..3666c8d, review clean)
  Minor (final review): no test for later start-time request / differing per-day starts; duplicate test; Settings has no defensive copy.
  Carry to Task 9: caller must replace stored pending with Change.pending even when null.
Ruling: R8 Task 9 maps only ACTIVITY_PAUSED to Paused (not STOPPED) — a late STOPPED for an old instance would drop the live one — cost: stale resumed entry if PAUSED is ever missing.
Ruling: R9 Task 9 appends synthetic Screen/Keyguard events at `now` from PowerManager/KeyguardManager after real events — boot may not log screen-on — cost: none.
Ruling: R10 Task 9 shifts event times by (trustedNow - wallNow) and reads since countedUntil - offset - 10s — event stamps are wall clock — cost: small attribution error on clock corrections.
Task 3: complete (commits 3666c8d..6ded661, review clean)
  Minor (final review): inaccurate comment UsageMeter.kt:30; missing direct tests (keyguard off resume, game->home, two free apps).
Ruling: R11 picture-in-picture / paused-but-visible apps do not consume time in stage 1 — not detectable from usage events; report to user and list in TEST.md — cost: a PiP video over home is a loophole.
Ruling: R12 24h floor applies to the first period after a start change only (as spec says); later weekday-start differences and travel time-zone shifts may make shorter days — still at most one budget per date at unchanged zone — cost: one budget can arrive some hours early.
Ruling: R13 Task 9 must run Engine.step before storing any settings request — else a loosening could apply at once after an unprocessed boundary — cost: none.
Task 4: complete (commits 6ded661..da945c8, review clean)
  Minor (final review): untested maxOf guard Engine.kt:94; comment Engine.kt:69.
  Carry to Task 9: Controller.arm refuses when already armed; one TrustedClock value for step/instant/lockReasons/synthetic events; step before reading lock reasons; skip warning when remaining is 0.
  Carry to Task 11/13: changing start to earlier time can stretch one day up to ~48h; show in UI notice / TEST.md.
Ruling: R14 (Task 5 Important, plan-mandated) forward wall time is accepted after reboot — manual time change is blocked by DISALLOW_CONFIG_DATE_TIME + auto time, and refusing it would stall resets after power-off — cost: if the OS restriction is ever bypassed, a forward change + reboot shortens waits. Report to user.
Task 5: complete (commits da945c8..0629884, review clean after ruling R14)
  Minor (final review): negative elapsed delta not clamped; 'window' naming/KDoc in EmergencyRelease.
  Note: same-boot clock lags until next reboot if wall was behind at first anchor.
Task 6: complete (commits 0629884..3a483f5, review clean)
  Minor (final review): no cross-field validation in decode; duplicate set lines accepted.
  Carry to Task 8: persist encoded text byte-for-byte (no added newline).
Task 7: fix round 1/5 (1 addressed, 0 open; commits 6701dae..27025ef)
Task 7: complete (commits 3a483f5..27025ef, review clean)
Ruling: R15 Task 8 builds dialers = current default dialer + system apps handling ACTION_DIAL, and also treats com.google.android.apps.safetyhub and com.sec.android.app.safetyassurance as never suspended (pass via dialers) — emergency safety is the spec's failure condition — cost: those apps consume no time.
Ruling: R16 Task 9 treats Empty like Corrupt for cleanup once (unsuspendAll + relax when device owner, no notification) — damaged prefs XML reads as Empty — cost: none.
Ruling: R17 Task 9 calls Enforcer.apply only on lock/allowed/package changes plus every 30s, not every 1s tick — battery — cost: up to 30s to re-suspend after outside change.
Task 8: complete (commits 27025ef..9ae71a4, review clean; PC build UNVERIFIED)
  Minor (final review): Enforcer relies only on prefs for unsuspend; FLAG_SUSPENDED by other suspender; exempt DEFAULT_INPUT_METHOD; back up debug.keystore (put in SETUP.md).
  Carry to Task 12: cross-process stale prefs after release (end main process on release); no release build before release feature tested.
Ruling: R18 homes should be current default home + system HOME apps only (any app declaring HOME is currently free and unsuspendable) — real bypass; fix in final fix wave — cost: a newly chosen third-party launcher stays free while it is default.
Task 9: minor (deferred, fix wave): failed event read still advances countedUntil (Controller.kt:201); two commits per second + decode per save; showWhenLocked loophole for TEST.md.
  Carry to Task 11: call arm/requestSettings/instantLock off the main thread.
  Carry to Task 12: release must use Controller.exclusive.
  Note: do not arm on device before Task 10 exists.
Task 9: fix round 1/5 (0 addressed, 1 open — unsuspendAll can never succeed because 'android' is always returned as failed; commits 534d50e..9acc742)
Task 9: fix round 2/5 (1 addressed, 0 open; commits 9acc742..1f4d14c)
Task 9: complete (commits 9ae71a4..1f4d14c, review clean; PC build UNVERIFIED)
Task 10: complete (commits 1f4d14c..ec8354b, review clean; PC build UNVERIFIED)
  Minor (fix wave): SettingsWatchService needs one extra settled re-check ~300-500ms after the latest event (immediate check may see stale/empty root; ignored performGlobalAction result).
  Minor (final review): only active window inspected (split screen/pop-up); if reproduced add flagRetrieveInteractiveWindows.
  Carry to Task 13: device checks - pages hosted outside com.android.settings, accessibility-data-sensitive views (Android 14+), title-only app name, scrolling lists, 600-node cap, main-thread delay, restricted settings with adb install.
Ruling: R19 Task 11 screens edit on top of (pending ?: active) and replace only their own part (week or allowed), load+request inside Controller.exclusive — else saving one screen drops a waiting change or stale other part — cost: none.
Ruling: R20 defaults before first configuration: every day 120 min, start 05:00, no allowed apps — spec gives none, user's own example is 05:00 — cost: user edits them.
Ruling: R21 Task 11 creates activity_release.xml but leaves btn_release disabled; Task 12 wires it — ReleaseActivity is Task 12 — cost: none.
Ruling: R22 instant-lock preset buttons fill input_minutes; only btn_start locks — a lock cannot be cancelled, avoid one-tap mistakes — cost: one extra tap.
