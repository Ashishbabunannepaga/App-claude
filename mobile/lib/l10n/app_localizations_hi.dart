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

  @override
  String get personalDetails => 'निजी जानकारी';

  @override
  String get dateOfBirth => 'जन्म तिथि';

  @override
  String get city => 'शहर';

  @override
  String get state => 'राज्य';

  @override
  String get save => 'सेव करें';

  @override
  String get notifications => 'सूचनाएँ';

  @override
  String get renewalReminders => 'रिन्यूअल रिमाइंडर';

  @override
  String get renewalRemindersHelp => 'पॉलिसी खत्म होने से 90, 60, 30, 15, 7 और 1 दिन पहले';

  @override
  String get policyUpdates => 'पॉलिसी अपडेट';

  @override
  String get policyUpdatesHelp => 'जब कोई दस्तावेज़ पढ़ लिया गया हो और जाँचने के लिए तैयार हो';

  @override
  String get notificationsPromise =>
      'हम कभी प्रचार वाली सूचनाएँ नहीं भेजते, और सूचनाओं में कभी आपका पॉलिसी नंबर, रकम या सेहत की जानकारी नहीं दिखती।';

  @override
  String get faqSafeQ => 'क्या मेरा डेटा सुरक्षित है?';

  @override
  String get faqSafeA =>
      'आपके दस्तावेज़ एन्क्रिप्ट करके रखे जाते हैं और सिर्फ़ आप उन्हें देख सकते हैं। हम आपका डेटा न बेचते हैं, न बीमा कंपनियों या एजेंटों से साझा करते हैं।';

  @override
  String get faqAiQ => 'AI मेरे सवालों के जवाब कैसे देता है?';

  @override
  String get faqAiA =>
      'यह सिर्फ़ आपका अपना पॉलिसी दस्तावेज़ पढ़ता है और बताता है कि जवाब किस पेज से आया। अगर जवाब आपके दस्तावेज़ में नहीं है, तो अंदाज़ा लगाने की बजाय साफ़ बता देता है।';

  @override
  String get faqWrongQ => 'मेरी पॉलिसी से निकाली गई जानकारी गलत है। मैं क्या करूँ?';

  @override
  String get faqWrongA =>
      'पॉलिसी खोलें, ⋮ मेन्यू दबाएँ और \"जानकारी बदलें\" चुनें। आप जो भी ठीक करेंगे, वह आपके द्वारा पुष्टि किया हुआ माना जाएगा।';

  @override
  String get faqUploadQ => 'मैं कौन-से दस्तावेज़ अपलोड कर सकता/सकती हूँ?';

  @override
  String get faqUploadA =>
      'PDF पॉलिसी दस्तावेज़ सबसे अच्छे रहते हैं। आप 20 MB तक की साफ़ फ़ोटो (JPG/PNG) भी अपलोड कर सकते हैं। पासवर्ड वाली PDF पहले अनलॉक करें।';

  @override
  String get faqSellQ => 'क्या आप बीमा बेचते हैं?';

  @override
  String faqSellA(String app) {
    return 'नहीं। $app आपकी मौजूदा पॉलिसियों को व्यवस्थित करने और समझने में मदद करता है। हम बीमा प्रोडक्ट न बेचते हैं, न उनकी सलाह देते हैं।';
  }

  @override
  String get faqDeleteQ => 'मैं अपना अकाउंट कैसे डिलीट करूँ?';

  @override
  String get faqDeleteA =>
      'प्रोफ़ाइल → प्राइवेसी और डेटा → अकाउंट डिलीट करें। आपका डेटा 7 दिन बाद हमेशा के लिए मिटा दिया जाता है।';

  @override
  String get supportThanks => 'धन्यवाद — हम 2 कामकाजी दिनों में आपसे संपर्क करेंगे।';

  @override
  String get helpSupport => 'मदद और सहायता';

  @override
  String get faqTitle => 'अक्सर पूछे जाने वाले सवाल';

  @override
  String get contactUs => 'हमसे संपर्क करें';

  @override
  String get topic => 'विषय';

  @override
  String get topicQuestion => 'एक सवाल';

  @override
  String get topicProblem => 'कुछ काम नहीं कर रहा';

  @override
  String get topicFeedback => 'सुझाव';

  @override
  String get topicPrivacy => 'प्राइवेसी / मेरा डेटा';

  @override
  String get topicGrievance => 'शिकायत';

  @override
  String get howCanWeHelp => 'हम कैसे मदद करें?';

  @override
  String get send => 'भेजें';

  @override
  String get emailUsInstead => 'इसकी बजाय ईमेल करें';

  @override
  String get deleteAccountQ => 'अपना अकाउंट डिलीट करें?';

  @override
  String get deleteAccountBody =>
      'आपका अकाउंट अभी बंद कर दिया जाएगा। आपकी सभी पॉलिसियाँ, दस्तावेज़ और डेटा 7 दिन बाद हमेशा के लिए मिटा दिए जाएँगे। 7 दिन के अंदर फिर से लॉग इन करने पर डिलीट रद्द हो जाएगा।';

  @override
  String get deleteAccount => 'अकाउंट डिलीट करें';

  @override
  String get privacyData => 'प्राइवेसी और डेटा';

  @override
  String get privacyPromise =>
      'हम आपके पॉलिसी दस्तावेज़ों का इस्तेमाल सिर्फ़ आपका अपना बीमा दिखाने, समझाने और याद दिलाने के लिए करते हैं। दस्तावेज़ एन्क्रिप्टेड रहते हैं, कभी बेचे नहीं जाते, और कभी बीमा कंपनियों या एजेंटों से साझा नहीं होते। AI प्रोसेसिंग ऐसे प्रदाताओं से होती है जिन्हें अनुबंध के तहत आपके डेटा पर ट्रेनिंग की अनुमति नहीं है।';

  @override
  String get downloadMyData => 'मेरा डेटा डाउनलोड करें';

  @override
  String get downloadMyDataHelp => 'आपकी प्रोफ़ाइल, पॉलिसियों और सवालों की एक कॉपी';

  @override
  String get privacyPolicyItem => 'प्राइवेसी पॉलिसी';

  @override
  String get grievanceOfficer => 'शिकायत अधिकारी';

  @override
  String get deleteAccountHelp => 'अपना सारा डेटा हमेशा के लिए मिटाएँ';

  @override
  String get appLock => 'ऐप लॉक';

  @override
  String get appLockHelp => 'ऐप खोलने के लिए फ़िंगरप्रिंट, चेहरा या फ़ोन का PIN इस्तेमाल करें';

  @override
  String get setUpScreenLock => 'पहले अपने फ़ोन पर स्क्रीन लॉक लगाएँ।';

  @override
  String get aiAnswerLanguage => 'AI जवाबों की भाषा';

  @override
  String get aiAnswerLanguageHelp =>
      'आपकी पॉलिसियों के सारांश और जवाब इसी भाषा में लिखे जाएँगे। आप इसमें सवाल भी पूछ सकते हैं।';
}
