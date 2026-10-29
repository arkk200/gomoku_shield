package expo.modules.shortsdetector

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.content.SharedPreferences
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/**
 * 유튜브 Shorts / 인스타그램 Reels 탭 진입을 감지해서 MainActivity를
 * 포커스 가진 풀스크린으로 띄우는 서비스 (CLAUDE.md 핵심 기능 설계 2번).
 *
 * 감지 방식: 화면에 떠있는 모든 윈도우(windows — rootInActiveWindow 하나만 보면
 * reel 플레이어가 다른 윈도우에 있어서 놓치는 경우가 실제로 있었음)의 뷰 트리에서
 * resource-id에 "shorts"/"reel" 문자열이 들어간 뷰가 있는지 찾는 휴리스틱. 정확한
 * 리소스 id를 모르는 상태라 가장 안정적으로 추측 가능한 방식 — 두 앱이 업데이트되면
 * 깨질 수 있음(CLAUDE.md 참고/리스크 참고).
 *
 * accessibility_service_config.xml에 flagReportViewIds(이게 없으면 resource-id가
 * 전부 null로 옴), flagIncludeNotImportantViews(이게 없으면 레이아웃 래퍼 노드
 * 밑으로 전혀 못 내려가서 실제 콘텐츠를 못 찾음)가 둘 다 필수 — 실기기 테스트로
 * 찾아낸 것들이라 빠뜨리면 조용히(에러 없이) 그냥 감지가 안 됨.
 *
 * 체크는 두 경로로 돌아감: (1) onAccessibilityEvent — 화면이 바뀔 때마다 바로 반응.
 * (2) POLL_INTERVAL_MS마다 도는 타이머 — 유저가 영상 하나를 가만히 보기만 하고
 * 스크롤을 안 하면 화면 변화 이벤트 자체가 안 생겨서 (1)만으로는 면제시간이
 * 지나도 영원히 재감지가 안 되는 문제가 실제로 있었음(실기기 QA로 찾음). 타이머가
 * 그 경우를 커버함.
 */
class ShortsDetectorAccessibilityService : AccessibilityService() {

  companion object {
    private const val TAG = "ShortsDetector"
    private val TARGET_KEYWORD_BY_PACKAGE = mapOf(
      "com.google.android.youtube" to "shorts",
      "com.instagram.android" to "reel"
    )
    private const val MIN_RETRIGGER_INTERVAL_MS = 3_000L
    private const val MAX_TREE_DEPTH = 40
    private const val POLL_INTERVAL_MS = 3_000L
  }

  private var lastTriggerAtMillis = 0L
  private val handler = Handler(Looper.getMainLooper())
  private val pollRunnable = object : Runnable {
    override fun run() {
      checkAndMaybeTrigger()
      handler.postDelayed(this, POLL_INTERVAL_MS)
    }
  }

  override fun onServiceConnected() {
    super.onServiceConnected()
    Log.d(TAG, "connected")
    handler.post(pollRunnable)
  }

  override fun onDestroy() {
    handler.removeCallbacks(pollRunnable)
    super.onDestroy()
  }

  override fun onAccessibilityEvent(event: AccessibilityEvent) {
    checkAndMaybeTrigger()
  }

  // 타이머든 이벤트든 똑같은 로직을 씀 — windows를 직접 보니까 이벤트 없이도 호출 가능함.
  private fun checkAndMaybeTrigger() {
    for ((pkg, keyword) in TARGET_KEYWORD_BY_PACKAGE) {
      val pkgWindows = windows.filter { it.root?.packageName?.toString() == pkg }
      if (pkgWindows.isEmpty()) continue
      if (!pkgWindows.any { treeContainsKeyword(it.root, keyword) }) continue
      if (isWithinGracePeriod()) continue

      val now = System.currentTimeMillis()
      if (now - lastTriggerAtMillis < MIN_RETRIGGER_INTERVAL_MS) continue
      lastTriggerAtMillis = now

      Log.d(TAG, "detected $keyword in $pkg, launching puzzle")
      launchPuzzleActivity()
      return
    }
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
