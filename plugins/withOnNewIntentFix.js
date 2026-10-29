const { withMainActivity } = require('@expo/config-plugins');
const { mergeContents } = require('@expo/config-plugins').CodeGenerator;

// MainActivity는 launchMode="singleTask"라 ShortsDetectorAccessibilityService가
// 재실행시키면 onCreate가 아니라 onNewIntent로 옴. RN 기본 onNewIntent는 JS Linking
// 쪼으로만 전달하고 setIntent()는 안 불러서, 안 고치면 getIntent()가 계속 옛 인텐트를
// 돌려줘서 ShortsDetectorModule.consumeLaunchTrigger()가 새 트리거를 영영 못 읽음.
//
// expo prebuild가 MainActivity.kt를 다시 생성할 때마다 이 수정이 날아가지 않게
// config plugin으로 박아둠(수동 편집이었으면 재생성 때 조용히 사라짐).
function withOnNewIntentFix(config) {
  return withMainActivity(config, (config) => {
    if (config.modResults.language !== 'kt') {
      throw new Error('withOnNewIntentFix: MainActivity가 Kotlin이 아님');
    }

    let contents = config.modResults.contents;

    contents = mergeContents({
      src: contents,
      newSrc: 'import android.content.Intent',
      tag: 'gomoku-shield-onnewintent-import',
      anchor: /^import android\.os\.Bundle/m,
      offset: 0,
      comment: '//',
    }).contents;

    const method = [
      '',
      '  override fun onNewIntent(intent: Intent) {',
      '    setIntent(intent)',
      '    super.onNewIntent(intent)',
      '  }',
    ].join('\n');

    contents = mergeContents({
      src: contents,
      newSrc: method,
      tag: 'gomoku-shield-onnewintent-method',
      anchor: /override fun getMainComponentName\(\): String = "main"/,
      offset: 1,
      comment: '//',
    }).contents;

    config.modResults.contents = contents;
    return config;
  });
}

module.exports = withOnNewIntentFix;
