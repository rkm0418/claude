package app.harulock.admin

import android.app.admin.DeviceAdminReceiver
import android.content.ComponentName
import android.content.Context

/** 기기 소유자로 등록하는 수신기. 동작은 [Guard]와 [Enforcer]가 맡는다. */
class AdminReceiver : DeviceAdminReceiver() {
    companion object {
        fun component(ctx: Context): ComponentName = ComponentName(ctx, AdminReceiver::class.java)
    }
}
