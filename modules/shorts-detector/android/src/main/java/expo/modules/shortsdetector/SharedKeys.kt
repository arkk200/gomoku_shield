package expo.modules.shortsdetector

// AccessibilityService와 ShortsDetectorModule이 공유하는 SharedPreferences 키/상수.
// 둘이 따로 선언하면 오타로 어긋날 위험이 있어서 한 곳에 모음.

const val PREFS_NAME = "shorts_detector_prefs"
const val KEY_EXEMPT_UNTIL = "exempt_until_millis"
const val KEY_GRACE_MINUTES = "grace_minutes"
const val DEFAULT_GRACE_MINUTES = 10.0

const val EXTRA_TRIGGER = "trigger"
const val TRIGGER_PUZZLE = "puzzle"

const val ACCESSIBILITY_SERVICE_CLASS = "expo.modules.shortsdetector.ShortsDetectorAccessibilityService"
