package expo.modules.shortsdetector

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.content.SharedPreferences
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/**
 * 유튜브 Shorts / 인스타그램 Reels 탭 진입을 감지해서 MainActivity를
 * 포커스 가진 풀스크린으로 띄우는 서비스 (CLAUDE.md 핵심 기능 설계 2번).
 *
 * 감지 방식: 화면 뷰 트리에서 resource-id에 "shorts"/"reel" 문자열이 들어간
 * 뷰가 있는지 찾는 휴리스틱. 정확한 리소스 id를 모르는 상태라 가장 안정적으로
 * 추측 가능한 방식 — 두 앱이 업데이트되면 깨질 수 있음(CLAUDE.md 참고/리스크 참고).
 */
class ShortsDetectorAccessibilityService : AccessibilityService() {

  companion object {
    private val TARGET_KEYWORD_BY_PACKAGE = mapOf(
      "com.google.android.youtube" to "shorts",
      "com.instagram.android" to "reel"
    )
    private const val MIN_RETRIGGER_INTERVAL_MS = 3_000L
    private const val MAX_TREE_DEPTH = 40
  }

  private var lastTriggerAtMillis = 0L

  override fun onAccessibilityEvent(event: AccessibilityEvent) {
    val packageName = event.packageName?.toString() ?: return
    val keyword = TARGET_KEYWORD_BY_PACKAGE[packageName] ?: return

    if (!treeContainsKeyword(rootInActiveWindow, keyword)) return
    if (isWithinGracePeriod()) return

    val now = System.currentTimeMillis()
    if (now - lastTriggerAtMillis < MIN_RETRIGGER_INTERVAL_MS) return
    lastTriggerAtMillis = now

    launchPuzzleActivity()
  }

  private fun treeContainsKeyword(node: AccessibilityNodeInfo?, keyword: String, depth: Int = 0): Boolean {
    if (node == null || depth > MAX_TREE_DEPTH) return false
    val id = node.viewIdResourceName
    if (id != null && id.lowercase().contains(keyword)) return true
    for (i in 0 until node.childCount) {
      if (treeContainsKeyword(node.getChild(i), keyword, depth + 1)) return true
    }
    return false
  }

  private fun isWithinGracePeriod(): Boolean {
    val prefs: SharedPreferences = getSharedPreferences(PREFS_NAME, 0)
    val exemptUntil = prefs.getLong(KEY_EXEMPT_UNTIL, 0L)
    return System.currentTimeMillis() < exemptUntil
  }

  private fun launchPuzzleActivity() {
    val intent = Intent().apply {
      setClassName(packageName, "com.gomokushield.app.MainActivity")
      addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
      putExtra(EXTRA_TRIGGER, TRIGGER_PUZZLE)
    }
    startActivity(intent)
  }

  override fun onInterrupt() {}
}
