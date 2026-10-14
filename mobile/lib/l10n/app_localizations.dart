import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale) : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates = <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[Locale('en'), Locale('hi')];

  /// No description provided for @languageName.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get languageName;

  /// No description provided for @appLanguage.
  ///
  /// In en, this message translates to:
  /// **'App language'**
  String get appLanguage;

  /// No description provided for @appLanguageHelp.
  ///
  /// In en, this message translates to:
  /// **'Buttons, menus and screens. AI answers have their own language setting.'**
  String get appLanguageHelp;

  /// No description provided for @skip.
  ///
  /// In en, this message translates to:
  /// **'Skip'**
  String get skip;

  /// No description provided for @next.
  ///
  /// In en, this message translates to:
  /// **'Next'**
  String get next;

  /// No description provided for @getStarted.
  ///
  /// In en, this message translates to:
  /// **'Get started'**
  String get getStarted;

  /// No description provided for @continueAction.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get continueAction;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @seeAll.
  ///
  /// In en, this message translates to:
  /// **'See all'**
  String get seeAll;

  /// No description provided for @tryAgain.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get tryAgain;

  /// No description provided for @onb1Title.
  ///
  /// In en, this message translates to:
  /// **'All your cover, one place'**
  String get onb1Title;

  /// No description provided for @onb1Body.
  ///
  /// In en, this message translates to:
  /// **'Health, life and motor policies for the whole family, kept safe and easy to find.'**
  String get onb1Body;

  /// No description provided for @onb2Title.
  ///
  /// In en, this message translates to:
  /// **'Ask in plain words'**
  String get onb2Title;

  /// No description provided for @onb2Body.
  ///
  /// In en, this message translates to:
  /// **'Every answer points to the page it came from, or tells you it isn\'t in your policy.'**
  String get onb2Body;

  /// No description provided for @onb3Title.
  ///
  /// In en, this message translates to:
  /// **'Renewals never sneak up'**
  String get onb3Title;

  /// No description provided for @onb3Body.
  ///
  /// In en, this message translates to:
  /// **'A gentle nudge well before your policy ends, so you are never left uncovered.'**
  String get onb3Body;

  /// No description provided for @onb4Title.
  ///
  /// In en, this message translates to:
  /// **'Family and nominees, sorted'**
  String get onb4Title;

  /// No description provided for @onb4Body.
  ///
  /// In en, this message translates to:
  /// **'See who is covered, who gets what, and what to do if something happens.'**
  String get onb4Body;

  /// No description provided for @loginHeadline.
  ///
  /// In en, this message translates to:
  /// **'All your insurance.\nOne place. Clearly explained.'**
  String get loginHeadline;

  /// No description provided for @loginSubhead.
  ///
  /// In en, this message translates to:
  /// **'Add your policies, understand what you\'re covered for, and never miss a renewal.'**
  String get loginSubhead;

  /// No description provided for @mobileNumber.
  ///
  /// In en, this message translates to:
  /// **'Mobile number'**
  String get mobileNumber;

  /// No description provided for @consentStart.
  ///
  /// In en, this message translates to:
  /// **'I agree to the '**
  String get consentStart;

  /// No description provided for @privacyPolicy.
  ///
  /// In en, this message translates to:
  /// **'Privacy Policy'**
  String get privacyPolicy;

  /// No description provided for @consentAnd.
  ///
  /// In en, this message translates to:
  /// **' and '**
  String get consentAnd;

  /// No description provided for @terms.
  ///
  /// In en, this message translates to:
  /// **'Terms'**
  String get terms;

  /// No description provided for @consentEnd.
  ///
  /// In en, this message translates to:
  /// **', and consent to my policy documents being processed to provide this service.'**
  String get consentEnd;

  /// No description provided for @getOtp.
  ///
  /// In en, this message translates to:
  /// **'Get OTP'**
  String get getOtp;

  /// No description provided for @otpTitle.
  ///
  /// In en, this message translates to:
  /// **'Enter the 6-digit code'**
  String get otpTitle;

  /// No description provided for @otpSentTo.
  ///
  /// In en, this message translates to:
  /// **'Sent to {identifier}'**
  String otpSentTo(String identifier);

  /// No description provided for @verify.
  ///
  /// In en, this message translates to:
  /// **'Verify'**
  String get verify;

  /// No description provided for @resendIn.
  ///
  /// In en, this message translates to:
  /// **'Resend code in {seconds}s'**
  String resendIn(int seconds);

  /// No description provided for @resendCode.
  ///
  /// In en, this message translates to:
  /// **'Resend code'**
  String get resendCode;

  /// No description provided for @nameTitle.
  ///
  /// In en, this message translates to:
  /// **'What should we call you?'**
  String get nameTitle;

  /// No description provided for @fullName.
  ///
  /// In en, this message translates to:
  /// **'Full name'**
  String get fullName;

  /// No description provided for @dobOptional.
  ///
  /// In en, this message translates to:
  /// **'Date of birth (optional)'**
  String get dobOptional;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navPortfolio.
  ///
  /// In en, this message translates to:
  /// **'Portfolio'**
  String get navPortfolio;

  /// No description provided for @navExplore.
  ///
  /// In en, this message translates to:
  /// **'Explore'**
  String get navExplore;

  /// No description provided for @navProfile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get navProfile;

  /// No description provided for @addPolicy.
  ///
  /// In en, this message translates to:
  /// **'Add policy'**
  String get addPolicy;

  /// No description provided for @hiName.
  ///
  /// In en, this message translates to:
  /// **'Hi {name}'**
  String hiName(String name);

  /// No description provided for @helloThere.
  ///
  /// In en, this message translates to:
  /// **'Hello there'**
  String get helloThere;

  /// No description provided for @homeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Here\'s where your cover stands today.'**
  String get homeSubtitle;

  /// No description provided for @whatToDo.
  ///
  /// In en, this message translates to:
  /// **'What would you like to do?'**
  String get whatToDo;

  /// No description provided for @comingUp.
  ///
  /// In en, this message translates to:
  /// **'Coming up'**
  String get comingUp;

  /// No description provided for @coverageReport.
  ///
  /// In en, this message translates to:
  /// **'Coverage report'**
  String get coverageReport;

  /// No description provided for @askAi.
  ///
  /// In en, this message translates to:
  /// **'Ask AI'**
  String get askAi;

  /// No description provided for @claimHelp.
  ///
  /// In en, this message translates to:
  /// **'Claim help'**
  String get claimHelp;

  /// No description provided for @family.
  ///
  /// In en, this message translates to:
  /// **'Family'**
  String get family;

  /// No description provided for @nominees.
  ///
  /// In en, this message translates to:
  /// **'Nominees'**
  String get nominees;

  /// No description provided for @compare.
  ///
  /// In en, this message translates to:
  /// **'Compare'**
  String get compare;

  /// No description provided for @emergencyCard.
  ///
  /// In en, this message translates to:
  /// **'Emergency card'**
  String get emergencyCard;

  /// No description provided for @seeCoverageReport.
  ///
  /// In en, this message translates to:
  /// **'See your coverage report'**
  String get seeCoverageReport;

  /// No description provided for @addAPolicy.
  ///
  /// In en, this message translates to:
  /// **'Add a policy'**
  String get addAPolicy;

  /// No description provided for @seeSampleReport.
  ///
  /// In en, this message translates to:
  /// **'See a sample report'**
  String get seeSampleReport;

  /// No description provided for @coinsEarned.
  ///
  /// In en, this message translates to:
  /// **'+{coins} coins earned'**
  String coinsEarned(int coins);

  /// No description provided for @personalDetails.
  ///
  /// In en, this message translates to:
  /// **'Personal details'**
  String get personalDetails;

  /// No description provided for @dateOfBirth.
  ///
  /// In en, this message translates to:
  /// **'Date of birth'**
  String get dateOfBirth;

  /// No description provided for @city.
  ///
  /// In en, this message translates to:
  /// **'City'**
  String get city;

  /// No description provided for @state.
  ///
  /// In en, this message translates to:
  /// **'State'**
  String get state;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @notifications.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get notifications;

  /// No description provided for @renewalReminders.
  ///
  /// In en, this message translates to:
  /// **'Renewal reminders'**
  String get renewalReminders;

  /// No description provided for @renewalRemindersHelp.
  ///
  /// In en, this message translates to:
  /// **'90, 60, 30, 15, 7 and 1 day before a policy expires'**
  String get renewalRemindersHelp;

  /// No description provided for @policyUpdates.
  ///
  /// In en, this message translates to:
  /// **'Policy updates'**
  String get policyUpdates;

  /// No description provided for @policyUpdatesHelp.
  ///
  /// In en, this message translates to:
  /// **'When a document has been read and is ready to review'**
  String get policyUpdatesHelp;

  /// No description provided for @notificationsPromise.
  ///
  /// In en, this message translates to:
  /// **'We never send promotional notifications, and notifications never show your policy numbers, amounts or health details.'**
  String get notificationsPromise;

  /// No description provided for @faqSafeQ.
  ///
  /// In en, this message translates to:
  /// **'Is my data safe?'**
  String get faqSafeQ;

  /// No description provided for @faqSafeA.
  ///
  /// In en, this message translates to:
  /// **'Your documents are stored encrypted and are only accessible to you. We do not sell your data or share it with insurers or agents.'**
  String get faqSafeA;

  /// No description provided for @faqAiQ.
  ///
  /// In en, this message translates to:
  /// **'How does the AI answer my questions?'**
  String get faqAiQ;

  /// No description provided for @faqAiA.
  ///
  /// In en, this message translates to:
  /// **'It reads only your own policy document and shows the page its answer came from. If the answer is not in your document it will say so instead of guessing.'**
  String get faqAiA;

  /// No description provided for @faqWrongQ.
  ///
  /// In en, this message translates to:
  /// **'The details extracted from my policy are wrong. What do I do?'**
  String get faqWrongQ;

  /// No description provided for @faqWrongA.
  ///
  /// In en, this message translates to:
  /// **'Open the policy, tap the ⋮ menu and choose \"Edit details\". Anything you correct is saved as confirmed by you.'**
  String get faqWrongA;

  /// No description provided for @faqUploadQ.
  ///
  /// In en, this message translates to:
  /// **'Which documents can I upload?'**
  String get faqUploadQ;

  /// No description provided for @faqUploadA.
  ///
  /// In en, this message translates to:
  /// **'PDF policy documents work best. You can also upload a clear photo (JPG/PNG) up to 20 MB. Password-protected PDFs must be unlocked first.'**
  String get faqUploadA;

  /// No description provided for @faqSellQ.
  ///
  /// In en, this message translates to:
  /// **'Do you sell insurance?'**
  String get faqSellQ;

  /// No description provided for @faqSellA.
  ///
  /// In en, this message translates to:
  /// **'No. {app} helps you organise and understand the policies you already have. We do not sell or recommend insurance products.'**
  String faqSellA(String app);

  /// No description provided for @faqDeleteQ.
  ///
  /// In en, this message translates to:
  /// **'How do I delete my account?'**
  String get faqDeleteQ;

  /// No description provided for @faqDeleteA.
  ///
  /// In en, this message translates to:
  /// **'Profile → Privacy & data → Delete account. Your data is permanently deleted after 7 days.'**
  String get faqDeleteA;

  /// No description provided for @supportThanks.
  ///
  /// In en, this message translates to:
  /// **'Thanks — we\'ll get back to you within 2 working days.'**
  String get supportThanks;

  /// No description provided for @helpSupport.
  ///
  /// In en, this message translates to:
  /// **'Help & support'**
  String get helpSupport;

  /// No description provided for @faqTitle.
  ///
  /// In en, this message translates to:
  /// **'Frequently asked questions'**
  String get faqTitle;

  /// No description provided for @contactUs.
  ///
  /// In en, this message translates to:
  /// **'Contact us'**
  String get contactUs;

  /// No description provided for @topic.
  ///
  /// In en, this message translates to:
  /// **'Topic'**
  String get topic;

  /// No description provided for @topicQuestion.
  ///
  /// In en, this message translates to:
  /// **'A question'**
  String get topicQuestion;

  /// No description provided for @topicProblem.
  ///
  /// In en, this message translates to:
  /// **'Something isn\'t working'**
  String get topicProblem;

  /// No description provided for @topicFeedback.
  ///
  /// In en, this message translates to:
  /// **'Feedback'**
  String get topicFeedback;

  /// No description provided for @topicPrivacy.
  ///
  /// In en, this message translates to:
  /// **'Privacy / my data'**
  String get topicPrivacy;

  /// No description provided for @topicGrievance.
  ///
  /// In en, this message translates to:
  /// **'Complaint (grievance)'**
  String get topicGrievance;

  /// No description provided for @howCanWeHelp.
  ///
  /// In en, this message translates to:
  /// **'How can we help?'**
  String get howCanWeHelp;

  /// No description provided for @send.
  ///
  /// In en, this message translates to:
  /// **'Send'**
  String get send;

  /// No description provided for @emailUsInstead.
  ///
  /// In en, this message translates to:
  /// **'Email us instead'**
  String get emailUsInstead;

  /// No description provided for @deleteAccountQ.
  ///
  /// In en, this message translates to:
  /// **'Delete your account?'**
  String get deleteAccountQ;

  /// No description provided for @deleteAccountBody.
  ///
  /// In en, this message translates to:
  /// **'Your account will be disabled now. All your policies, documents and data will be permanently deleted after 7 days. Logging in again within 7 days cancels the deletion.'**
  String get deleteAccountBody;

  /// No description provided for @deleteAccount.
  ///
  /// In en, this message translates to:
  /// **'Delete account'**
  String get deleteAccount;

  /// No description provided for @privacyData.
  ///
  /// In en, this message translates to:
  /// **'Privacy & data'**
  String get privacyData;

  /// No description provided for @privacyPromise.
  ///
  /// In en, this message translates to:
  /// **'We use your policy documents only to show, explain and remind you about your own insurance. Documents are encrypted, never sold, and never shared with insurers or agents. AI processing uses providers contractually barred from training on your data.'**
  String get privacyPromise;

  /// No description provided for @downloadMyData.
  ///
  /// In en, this message translates to:
  /// **'Download my data'**
  String get downloadMyData;

  /// No description provided for @downloadMyDataHelp.
  ///
  /// In en, this message translates to:
  /// **'A copy of your profile, policies and questions'**
  String get downloadMyDataHelp;

  /// No description provided for @privacyPolicyItem.
  ///
  /// In en, this message translates to:
  /// **'Privacy policy'**
  String get privacyPolicyItem;

  /// No description provided for @grievanceOfficer.
  ///
  /// In en, this message translates to:
  /// **'Grievance officer'**
  String get grievanceOfficer;

  /// No description provided for @deleteAccountHelp.
  ///
  /// In en, this message translates to:
  /// **'Permanently delete all your data'**
  String get deleteAccountHelp;

  /// No description provided for @appLock.
  ///
  /// In en, this message translates to:
  /// **'App lock'**
  String get appLock;

  /// No description provided for @appLockHelp.
  ///
  /// In en, this message translates to:
  /// **'Use fingerprint, face or device PIN to open the app'**
  String get appLockHelp;

  /// No description provided for @setUpScreenLock.
  ///
  /// In en, this message translates to:
  /// **'Set up a screen lock on your phone first.'**
  String get setUpScreenLock;

  /// No description provided for @aiAnswerLanguage.
  ///
  /// In en, this message translates to:
  /// **'AI answer language'**
  String get aiAnswerLanguage;

  /// No description provided for @aiAnswerLanguageHelp.
  ///
  /// In en, this message translates to:
  /// **'Summaries and answers about your policies will be written in this language. You can ask questions in it too.'**
  String get aiAnswerLanguageHelp;
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>['en', 'hi'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
