// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

  @override
  String get languageName => 'हिन्दी';

  @override
  String get appLanguage => 'ऐप की भाषा';

  @override
  String get appLanguageHelp => 'बटन, मेन्यू और स्क्रीन। AI जवाबों की भाषा अलग से चुनी जाती है।';

  @override
  String get skip => 'छोड़ें';

  @override
  String get next => 'आगे';

  @override
  String get getStarted => 'शुरू करें';

  @override
  String get continueAction => 'आगे बढ़ें';

  @override
  String get cancel => 'रद्द करें';

  @override
  String get seeAll => 'सभी देखें';

  @override
  String get tryAgain => 'फिर कोशिश करें';

  @override
  String get onb1Title => 'आपका पूरा बीमा, एक जगह';

  @override
  String get onb1Body => 'पूरे परिवार की हेल्थ, लाइफ और मोटर पॉलिसी, सुरक्षित और ढूँढने में आसान।';

  @override
  String get onb2Title => 'सीधे शब्दों में पूछें';

  @override
  String get onb2Body => 'हर जवाब बताता है कि वह पॉलिसी के किस पेज से है, या कि यह आपकी पॉलिसी में नहीं है।';

  @override
  String get onb3Title => 'रिन्यूअल कभी नहीं छूटेगा';

  @override
  String get onb3Body => 'पॉलिसी खत्म होने से काफ़ी पहले याद दिलाएँगे, ताकि आप कभी बिना कवर के न रहें।';

  @override
  String get onb4Title => 'परिवार और नॉमिनी, सब तय';

  @override
  String get onb4Body => 'देखें कौन कवर है, किसे क्या मिलेगा, और कुछ होने पर क्या करना है।';

  @override
  String get loginHeadline => 'आपका पूरा बीमा।\nएक जगह। साफ़ समझ में।';

  @override
  String get loginSubhead => 'अपनी पॉलिसी जोड़ें, समझें कि आपको किस चीज़ का कवर है, और कोई रिन्यूअल न चूकें।';

  @override
  String get mobileNumber => 'मोबाइल नंबर';

  @override
  String get consentStart => 'मैं ';

  @override
  String get privacyPolicy => 'प्राइवेसी पॉलिसी';

  @override
  String get consentAnd => ' और ';

  @override
  String get terms => 'शर्तों';

  @override
  String get consentEnd =>
      ' से सहमत हूँ, और इस सेवा के लिए अपने पॉलिसी दस्तावेज़ों की प्रोसेसिंग की अनुमति देता/देती हूँ।';

  @override
  String get getOtp => 'OTP पाएँ';

  @override
  String get otpTitle => '6 अंकों का कोड डालें';

  @override
  String otpSentTo(String identifier) {
    return '$identifier पर भेजा गया';
  }

  @override
  String get verify => 'पुष्टि करें';

  @override
  String resendIn(int seconds) {
    return '$seconds सेकंड में दोबारा भेजें';
  }

  @override
  String get resendCode => 'कोड दोबारा भेजें';

  @override
  String get nameTitle => 'हम आपको किस नाम से बुलाएँ?';

  @override
  String get fullName => 'पूरा नाम';

  @override
  String get dobOptional => 'जन्म तिथि (वैकल्पिक)';

  @override
  String get navHome => 'होम';

  @override
  String get navPortfolio => 'पॉलिसी';

  @override
  String get navExplore => 'जानें';

  @override
  String get navProfile => 'प्रोफ़ाइल';

  @override
  String get addPolicy => 'पॉलिसी जोड़ें';

  @override
  String hiName(String name) {
    return 'नमस्ते $name';
  }

  @override
  String get helloThere => 'नमस्ते';

  @override
  String get homeSubtitle => 'आज आपके बीमा कवर की स्थिति।';

  @override
  String get whatToDo => 'आप क्या करना चाहेंगे?';

  @override
  String get comingUp => 'जल्द आने वाले';

  @override
  String get coverageReport => 'कवरेज रिपोर्ट';

  @override
  String get askAi => 'AI से पूछें';

  @override
  String get claimHelp => 'क्लेम में मदद';

  @override
  String get family => 'परिवार';

  @override
  String get nominees => 'नॉमिनी';

  @override
  String get compare => 'तुलना करें';

  @override
  String get emergencyCard => 'इमरजेंसी कार्ड';

  @override
  String get seeCoverageReport => 'अपनी कवरेज रिपोर्ट देखें';

  @override
  String get addAPolicy => 'पॉलिसी जोड़ें';

  @override
  String get seeSampleReport => 'नमूना रिपोर्ट देखें';

  @override
  String coinsEarned(int coins) {
    return '+$coins कॉइन मिले';
  }
}
