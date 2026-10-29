package expo.modules.shortsdetector

import android.content.Intent
import android.content.SharedPreferences
import android.provider.Settings
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

/**
 * RN 쪽에서 쓰는 네이티브 브릿지. AccessibilityService(ShortsDetectorAccessibilityService)랑
 * SharedPreferences(PREFS_NAME)를 같이 써서 "몇 분 면제할지"/"지금 면제 중인지"를 주고받음.
 */
class ShortsDetectorModule : Module() {

  private val prefs: SharedPreferences
    get() = appContext.reactContext!!.getSharedPreferences(PREFS_NAME, 0)

  override fun definition() = ModuleDefinition {
    Name("ShortsDetector")

    // 안드로이드 접근성 설정 화면을 열어줌 — 접근성 서비스는 앱이 직접 켤 수 없고
    // 유저가 설정에서 수동으로 켜야 함(보안상 제약).
    Function("openAccessibilitySettings") {
      val context = appContext.reactContext ?: return@Function
      val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).apply {
        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
      }
      context.startActivity(intent)
    }

    // 지금 우리 AccessibilityService가 켜져있는지 확인(설정 화면에 "켜짐" 표시해주려고).
    Function("isAccessibilityServiceEnabled") {
      val context = appContext.reactContext ?: return@Function false
      val enabled = Settings.Secure.getString(
        context.contentResolver,
        Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
      ) ?: ""
      val serviceId = "${context.packageName}/$ACCESSIBILITY_SERVICE_CLASS"
      enabled.split(":").any { it.equals(serviceId, ignoreCase = true) }
    }

    // MainActivity가 감지 서비스에 의해 재실행된 거라면 "puzzle"을 돌려줌(그 외엔 null).
    // 한 번 읽으면 지워서 같은 트리거로 두 번 반응 안 하게 함.
    Function("consumeLaunchTrigger") {
      val activity = appContext.currentActivity ?: return@Function null
      val trigger = activity.intent?.getStringExtra(EXTRA_TRIGGER)
      activity.intent?.removeExtra(EXTRA_TRIGGER)
      trigger
    }

    // 퍼즐 풀었을 때 호출 — graceMinutes만큼 재감지 안 되게 면제 타임스탬프 기록.
    Function("markPuzzleSolved") { graceMinutes: Double ->
      val exemptUntil = System.currentTimeMillis() + (graceMinutes * 60_000).toLong()
      prefs.edit().putLong(KEY_EXEMPT_UNTIL, exemptUntil).apply()
    }

    // 퍼즐 다 풀고 "돌아가기" 눌렀을 때 — 우리 앱을 백그라운드로 보내서
    // 뒤에 깔려있던 유튜브/인스타가 다시 보이게 함(앱을 끄는 게 아니라 숨기는 거).
    Function("moveToBack") {
      appContext.currentActivity?.moveTaskToBack(true)
    }

    Function("getGraceMinutesSetting") {
      prefs.getFloat(KEY_GRACE_MINUTES, DEFAULT_GRACE_MINUTES.toFloat()).toDouble()
    }

    Function("setGraceMinutesSetting") { minutes: Double ->
      prefs.edit().putFloat(KEY_GRACE_MINUTES, minutes.toFloat()).apply()
    }
  }
}
