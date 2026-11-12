# ScreenShot Overlay App — Design

## Goal
Android app: on launch shows a small draggable overlay icon; tapping it captures the current screen and saves the PNG to a dedicated album (`Pictures/ScreenShots/`). Battery use must be minimal.

## Decisions
- Native Android, Kotlin, minSdk 26, targetSdk 34. Location: `ScreenShotApp/`.
- Approach A: MediaProjection, capture one frame only on tap; no continuous recording.
- Album name: `ScreenShots`.

## Components
1. **MainActivity** – requests "draw over other apps" and notification (Android 13+) permissions, requests MediaProjection consent once, starts CaptureService, finishes.
2. **CaptureService** – foreground service (type `mediaProjection`). Adds overlay icon via WindowManager (draggable, position remembered). Notification has a "Stop" action.
3. **Capture flow** – on tap: hide icon, create VirtualDisplay + ImageReader, grab one frame, release both immediately, show icon, toast "saved". Reuse the MediaProjection token (Android 14 forbids re-creating it per capture); create VirtualDisplay only on demand. Idle cost ≈ zero.
4. **ImageSaver** – MediaStore insert into `Pictures/ScreenShots/`, PNG, background thread. No storage permission needed.

## Error handling
- Permission denied → explain and exit.
- MediaProjection stopped by system → re-request consent.
- Save failure → toast.

## Testing
- Unit tests for pure logic (ImageSaver naming/path, bitmap conversion helpers); Gradle build verification.
- Overlay/capture behavior must be verified on a real device.
