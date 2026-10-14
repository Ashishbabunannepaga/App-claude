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

  /// No description provided for @policy.
  ///
  /// In en, this message translates to:
  /// **'Policy'**
  String get policy;

  /// No description provided for @reviewExtracted.
  ///
  /// In en, this message translates to:
  /// **'Please review the extracted details'**
  String get reviewExtracted;

  /// No description provided for @coverageReportHelp.
  ///
  /// In en, this message translates to:
  /// **'What is covered, what has limits and what is not — item by item'**
  String get coverageReportHelp;

  /// No description provided for @noNomineeAddOne.
  ///
  /// In en, this message translates to:
  /// **'No nominee recorded — add one'**
  String get noNomineeAddOne;

  /// No description provided for @notRecorded.
  ///
  /// In en, this message translates to:
  /// **'Not recorded'**
  String get notRecorded;

  /// No description provided for @policyClauses.
  ///
  /// In en, this message translates to:
  /// **'Policy clauses'**
  String get policyClauses;

  /// No description provided for @policyClausesHelp.
  ///
  /// In en, this message translates to:
  /// **'Benefits, exclusions, waiting periods and limits — word for word'**
  String get policyClausesHelp;

  /// No description provided for @whoIsCovered.
  ///
  /// In en, this message translates to:
  /// **'Who is covered'**
  String get whoIsCovered;

  /// No description provided for @understandPolicy.
  ///
  /// In en, this message translates to:
  /// **'Understand your policy'**
  String get understandPolicy;

  /// No description provided for @keyDetails.
  ///
  /// In en, this message translates to:
  /// **'Key details'**
  String get keyDetails;

  /// No description provided for @coverageDetails.
  ///
  /// In en, this message translates to:
  /// **'Coverage details'**
  String get coverageDetails;

  /// No description provided for @typeInsurance.
  ///
  /// In en, this message translates to:
  /// **'{type} insurance'**
  String typeInsurance(String type);

  /// No description provided for @idv.
  ///
  /// In en, this message translates to:
  /// **'Insured declared value'**
  String get idv;

  /// No description provided for @cover.
  ///
  /// In en, this message translates to:
  /// **'Cover'**
  String get cover;

  /// No description provided for @validRange.
  ///
  /// In en, this message translates to:
  /// **'Valid {start} – {end}'**
  String validRange(String start, String end);

  /// No description provided for @premiumValue.
  ///
  /// In en, this message translates to:
  /// **'Premium {amount}'**
  String premiumValue(String amount);

  /// No description provided for @askAiShort.
  ///
  /// In en, this message translates to:
  /// **'Ask AI'**
  String get askAiShort;

  /// No description provided for @renewal.
  ///
  /// In en, this message translates to:
  /// **'Renewal'**
  String get renewal;

  /// No description provided for @claimHelpAction.
  ///
  /// In en, this message translates to:
  /// **'Claim help'**
  String get claimHelpAction;

  /// No description provided for @documentsRequired.
  ///
  /// In en, this message translates to:
  /// **'Documents usually required'**
  String get documentsRequired;

  /// No description provided for @followInsurerProcess.
  ///
  /// In en, this message translates to:
  /// **'Always follow the claim process stated in your policy and by your insurer.'**
  String get followInsurerProcess;

  /// No description provided for @readingPolicy.
  ///
  /// In en, this message translates to:
  /// **'Reading your policy…'**
  String get readingPolicy;

  /// No description provided for @watchOutFor.
  ///
  /// In en, this message translates to:
  /// **'Watch out for'**
  String get watchOutFor;

  /// No description provided for @policyNumber.
  ///
  /// In en, this message translates to:
  /// **'Policy number'**
  String get policyNumber;

  /// No description provided for @insurer.
  ///
  /// In en, this message translates to:
  /// **'Insurer'**
  String get insurer;

  /// No description provided for @plan.
  ///
  /// In en, this message translates to:
  /// **'Plan'**
  String get plan;

  /// No description provided for @startDate.
  ///
  /// In en, this message translates to:
  /// **'Start date'**
  String get startDate;

  /// No description provided for @endDate.
  ///
  /// In en, this message translates to:
  /// **'End date'**
  String get endDate;

  /// No description provided for @premium.
  ///
  /// In en, this message translates to:
  /// **'Premium'**
  String get premium;

  /// No description provided for @coverRow.
  ///
  /// In en, this message translates to:
  /// **'Cover'**
  String get coverRow;

  /// No description provided for @deletePolicyQ.
  ///
  /// In en, this message translates to:
  /// **'Delete this policy?'**
  String get deletePolicyQ;

  /// No description provided for @deletePolicyBody.
  ///
  /// In en, this message translates to:
  /// **'The policy, its document and your questions about it will be permanently deleted.'**
  String get deletePolicyBody;

  /// No description provided for @delete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// No description provided for @editDetails.
  ///
  /// In en, this message translates to:
  /// **'Edit details'**
  String get editDetails;

  /// No description provided for @viewDocument.
  ///
  /// In en, this message translates to:
  /// **'View document'**
  String get viewDocument;

  /// No description provided for @deletePolicy.
  ///
  /// In en, this message translates to:
  /// **'Delete policy'**
  String get deletePolicy;

  /// No description provided for @policyHealth.
  ///
  /// In en, this message translates to:
  /// **'Policy health'**
  String get policyHealth;

  /// No description provided for @noIssuesFound.
  ///
  /// In en, this message translates to:
  /// **'No issues found in the details we read'**
  String get noIssuesFound;

  /// No description provided for @thingsToKnow.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 thing to know about} other{{count} things to know about}}'**
  String thingsToKnow(int count);

  /// No description provided for @markedRenewed.
  ///
  /// In en, this message translates to:
  /// **'Marked as renewed. Add your new policy document to keep things up to date.'**
  String get markedRenewed;

  /// No description provided for @add.
  ///
  /// In en, this message translates to:
  /// **'Add'**
  String get add;

  /// No description provided for @renewalTitle.
  ///
  /// In en, this message translates to:
  /// **'Renewal'**
  String get renewalTitle;

  /// No description provided for @addEndDate.
  ///
  /// In en, this message translates to:
  /// **'Add the policy end date to track renewal.'**
  String get addEndDate;

  /// No description provided for @expiredOn.
  ///
  /// In en, this message translates to:
  /// **'This policy expired on {date}.'**
  String expiredOn(String date);

  /// No description provided for @renewsOn.
  ///
  /// In en, this message translates to:
  /// **'Renews on {date} — {days, plural, =1{1 day left} other{{days} days left}}.'**
  String renewsOn(String date, int days);

  /// No description provided for @lastPremium.
  ///
  /// In en, this message translates to:
  /// **'Last premium: {amount}'**
  String lastPremium(String amount);

  /// No description provided for @remindSchedule.
  ///
  /// In en, this message translates to:
  /// **'We\'ll remind you 90, 60, 30, 15, 7 and 1 day before expiry.'**
  String get remindSchedule;

  /// No description provided for @remindersOff.
  ///
  /// In en, this message translates to:
  /// **'Renewal reminders are turned off in settings.'**
  String get remindersOff;

  /// No description provided for @markedAsRenewed.
  ///
  /// In en, this message translates to:
  /// **'✓ Marked as renewed'**
  String get markedAsRenewed;

  /// No description provided for @markedNotRenewing.
  ///
  /// In en, this message translates to:
  /// **'Marked as not renewing'**
  String get markedNotRenewing;

  /// No description provided for @iRenewed.
  ///
  /// In en, this message translates to:
  /// **'I\'ve renewed this policy'**
  String get iRenewed;

  /// No description provided for @notRenewing.
  ///
  /// In en, this message translates to:
  /// **'I\'m not renewing'**
  String get notRenewing;

  /// No description provided for @undo.
  ///
  /// In en, this message translates to:
  /// **'Undo'**
  String get undo;

  /// No description provided for @claimHealthTitle.
  ///
  /// In en, this message translates to:
  /// **'Health insurance claim'**
  String get claimHealthTitle;

  /// No description provided for @claimHealthStep1.
  ///
  /// In en, this message translates to:
  /// **'Check that the hospital is in your insurer\'s network (for cashless treatment).'**
  String get claimHealthStep1;

  /// No description provided for @claimHealthStep2.
  ///
  /// In en, this message translates to:
  /// **'Planned admission: request cashless pre-authorisation at the hospital\'s insurance desk at least 48 hours before.'**
  String get claimHealthStep2;

  /// No description provided for @claimHealthStep3.
  ///
  /// In en, this message translates to:
  /// **'Emergency admission: inform your insurer or TPA within 24 hours.'**
  String get claimHealthStep3;

  /// No description provided for @claimHealthStep4.
  ///
  /// In en, this message translates to:
  /// **'Show your health card / policy number and photo ID at the hospital.'**
  String get claimHealthStep4;

  /// No description provided for @claimHealthStep5.
  ///
  /// In en, this message translates to:
  /// **'For reimbursement (non-network hospital), pay the bill and submit the claim within the time stated in your policy.'**
  String get claimHealthStep5;

  /// No description provided for @claimHealthStep6.
  ///
  /// In en, this message translates to:
  /// **'Track your claim with the claim reference number your insurer gives you.'**
  String get claimHealthStep6;

  /// No description provided for @claimHealthDoc1.
  ///
  /// In en, this message translates to:
  /// **'Claim form (signed)'**
  String get claimHealthDoc1;

  /// No description provided for @claimHealthDoc2.
  ///
  /// In en, this message translates to:
  /// **'Policy copy / health card'**
  String get claimHealthDoc2;

  /// No description provided for @claimHealthDoc3.
  ///
  /// In en, this message translates to:
  /// **'Photo ID and address proof'**
  String get claimHealthDoc3;

  /// No description provided for @claimHealthDoc4.
  ///
  /// In en, this message translates to:
  /// **'Discharge summary'**
  String get claimHealthDoc4;

  /// No description provided for @claimHealthDoc5.
  ///
  /// In en, this message translates to:
  /// **'Original hospital bills and payment receipts'**
  String get claimHealthDoc5;

  /// No description provided for @claimHealthDoc6.
  ///
  /// In en, this message translates to:
  /// **'Doctor\'s prescriptions and investigation reports'**
  String get claimHealthDoc6;

  /// No description provided for @claimHealthDoc7.
  ///
  /// In en, this message translates to:
  /// **'Cancelled cheque or bank details (for reimbursement)'**
  String get claimHealthDoc7;

  /// No description provided for @claimMotorTitle.
  ///
  /// In en, this message translates to:
  /// **'Motor insurance claim'**
  String get claimMotorTitle;

  /// No description provided for @claimMotorStep1.
  ///
  /// In en, this message translates to:
  /// **'Ensure everyone is safe. For theft or third-party injury, file an FIR with the police.'**
  String get claimMotorStep1;

  /// No description provided for @claimMotorStep2.
  ///
  /// In en, this message translates to:
  /// **'Inform your insurer as soon as possible and get a claim number.'**
  String get claimMotorStep2;

  /// No description provided for @claimMotorStep3.
  ///
  /// In en, this message translates to:
  /// **'Do not repair the vehicle before the insurer\'s surveyor inspects it (unless told otherwise).'**
  String get claimMotorStep3;

  /// No description provided for @claimMotorStep4.
  ///
  /// In en, this message translates to:
  /// **'Take the vehicle to a network garage for cashless repair, or any garage for reimbursement.'**
  String get claimMotorStep4;

  /// No description provided for @claimMotorStep5.
  ///
  /// In en, this message translates to:
  /// **'Pay any compulsory deductible and non-covered items; the insurer settles the rest.'**
  String get claimMotorStep5;

  /// No description provided for @claimMotorDoc1.
  ///
  /// In en, this message translates to:
  /// **'Claim form'**
  String get claimMotorDoc1;

  /// No description provided for @claimMotorDoc2.
  ///
  /// In en, this message translates to:
  /// **'Policy copy'**
  String get claimMotorDoc2;

  /// No description provided for @claimMotorDoc3.
  ///
  /// In en, this message translates to:
  /// **'Registration certificate (RC)'**
  String get claimMotorDoc3;

  /// No description provided for @claimMotorDoc4.
  ///
  /// In en, this message translates to:
  /// **'Driving licence of the driver'**
  String get claimMotorDoc4;

  /// No description provided for @claimMotorDoc5.
  ///
  /// In en, this message translates to:
  /// **'FIR (for theft, major accident or third-party claims)'**
  String get claimMotorDoc5;

  /// No description provided for @claimMotorDoc6.
  ///
  /// In en, this message translates to:
  /// **'Repair estimate and final invoice'**
  String get claimMotorDoc6;

  /// No description provided for @claimLifeTitle.
  ///
  /// In en, this message translates to:
  /// **'Life insurance claim'**
  String get claimLifeTitle;

  /// No description provided for @claimLifeStep1.
  ///
  /// In en, this message translates to:
  /// **'The nominee should inform the insurer as soon as possible.'**
  String get claimLifeStep1;

  /// No description provided for @claimLifeStep2.
  ///
  /// In en, this message translates to:
  /// **'Collect the claim form from the insurer\'s branch or website.'**
  String get claimLifeStep2;

  /// No description provided for @claimLifeStep3.
  ///
  /// In en, this message translates to:
  /// **'Submit the form with the required documents.'**
  String get claimLifeStep3;

  /// No description provided for @claimLifeStep4.
  ///
  /// In en, this message translates to:
  /// **'The insurer may investigate claims made within the first few policy years.'**
  String get claimLifeStep4;

  /// No description provided for @claimLifeStep5.
  ///
  /// In en, this message translates to:
  /// **'Track the claim status with the insurer.'**
  String get claimLifeStep5;

  /// No description provided for @claimLifeDoc1.
  ///
  /// In en, this message translates to:
  /// **'Claim form'**
  String get claimLifeDoc1;

  /// No description provided for @claimLifeDoc2.
  ///
  /// In en, this message translates to:
  /// **'Original policy document'**
  String get claimLifeDoc2;

  /// No description provided for @claimLifeDoc3.
  ///
  /// In en, this message translates to:
  /// **'Death certificate'**
  String get claimLifeDoc3;

  /// No description provided for @claimLifeDoc4.
  ///
  /// In en, this message translates to:
  /// **'Nominee\'s photo ID, address proof and bank details'**
  String get claimLifeDoc4;

  /// No description provided for @claimLifeDoc5.
  ///
  /// In en, this message translates to:
  /// **'Medical records / FIR and post-mortem report (if applicable)'**
  String get claimLifeDoc5;

  /// No description provided for @claimOtherTitle.
  ///
  /// In en, this message translates to:
  /// **'Making a claim'**
  String get claimOtherTitle;

  /// No description provided for @claimOtherStep1.
  ///
  /// In en, this message translates to:
  /// **'Read your policy to confirm the event is covered.'**
  String get claimOtherStep1;

  /// No description provided for @claimOtherStep2.
  ///
  /// In en, this message translates to:
  /// **'Inform your insurer as soon as possible and get a claim number.'**
  String get claimOtherStep2;

  /// No description provided for @claimOtherStep3.
  ///
  /// In en, this message translates to:
  /// **'Submit the claim form and supporting documents.'**
  String get claimOtherStep3;

  /// No description provided for @claimOtherStep4.
  ///
  /// In en, this message translates to:
  /// **'Track your claim with the insurer.'**
  String get claimOtherStep4;

  /// No description provided for @claimOtherDoc1.
  ///
  /// In en, this message translates to:
  /// **'Claim form'**
  String get claimOtherDoc1;

  /// No description provided for @claimOtherDoc2.
  ///
  /// In en, this message translates to:
  /// **'Policy copy'**
  String get claimOtherDoc2;

  /// No description provided for @claimOtherDoc3.
  ///
  /// In en, this message translates to:
  /// **'Photo ID'**
  String get claimOtherDoc3;

  /// No description provided for @claimOtherDoc4.
  ///
  /// In en, this message translates to:
  /// **'Proof of loss / bills'**
  String get claimOtherDoc4;

  /// No description provided for @explore.
  ///
  /// In en, this message translates to:
  /// **'Explore'**
  String get explore;

  /// No description provided for @claimGuides.
  ///
  /// In en, this message translates to:
  /// **'Claim guides'**
  String get claimGuides;

  /// No description provided for @comingSoon.
  ///
  /// In en, this message translates to:
  /// **'Coming soon'**
  String get comingSoon;

  /// No description provided for @gmailImport.
  ///
  /// In en, this message translates to:
  /// **'Gmail import'**
  String get gmailImport;

  /// No description provided for @digiLocker.
  ///
  /// In en, this message translates to:
  /// **'DigiLocker'**
  String get digiLocker;

  /// No description provided for @claimTracking.
  ///
  /// In en, this message translates to:
  /// **'Claim tracking'**
  String get claimTracking;

  /// No description provided for @wellness.
  ///
  /// In en, this message translates to:
  /// **'Wellness'**
  String get wellness;

  /// No description provided for @deathLife1.
  ///
  /// In en, this message translates to:
  /// **'Inform the insurer as soon as possible (call centre, branch or website) and note the claim number.'**
  String get deathLife1;

  /// No description provided for @deathLife2.
  ///
  /// In en, this message translates to:
  /// **'The nominee fills the death claim form and attaches the documents below.'**
  String get deathLife2;

  /// No description provided for @deathLife3.
  ///
  /// In en, this message translates to:
  /// **'For deaths within the first 3 policy years the insurer may investigate before paying — this is normal.'**
  String get deathLife3;

  /// No description provided for @deathLife4.
  ///
  /// In en, this message translates to:
  /// **'The claim amount is paid to the nominee\'s bank account. If the nominee is a minor, the appointee receives it.'**
  String get deathLife4;

  /// No description provided for @deathHealth1.
  ///
  /// In en, this message translates to:
  /// **'A health policy ends for the person who died. If it is a family floater, the other members stay covered until renewal.'**
  String get deathHealth1;

  /// No description provided for @deathHealth2.
  ///
  /// In en, this message translates to:
  /// **'Any pending hospital bills can still be claimed by the nominee — submit them within the claim time limit.'**
  String get deathHealth2;

  /// No description provided for @deathHealth3.
  ///
  /// In en, this message translates to:
  /// **'Inform the insurer to remove the member and update the policy at renewal.'**
  String get deathHealth3;

  /// No description provided for @deathMotor1.
  ///
  /// In en, this message translates to:
  /// **'The vehicle and its insurance must be transferred to the legal heir within the time the insurer specifies.'**
  String get deathMotor1;

  /// No description provided for @deathMotor2.
  ///
  /// In en, this message translates to:
  /// **'Inform the insurer with the death certificate and the new owner\'s documents.'**
  String get deathMotor2;

  /// No description provided for @deathMotor3.
  ///
  /// In en, this message translates to:
  /// **'Until transfer, avoid using the vehicle — claims may be refused if the registered owner has died.'**
  String get deathMotor3;

  /// No description provided for @deathOther1.
  ///
  /// In en, this message translates to:
  /// **'Inform the insurer with the death certificate and ask for their claim or transfer process.'**
  String get deathOther1;

  /// No description provided for @deathDoc1.
  ///
  /// In en, this message translates to:
  /// **'Death certificate (original or attested copy)'**
  String get deathDoc1;

  /// No description provided for @deathDoc2.
  ///
  /// In en, this message translates to:
  /// **'Policy document or policy number'**
  String get deathDoc2;

  /// No description provided for @deathDoc3.
  ///
  /// In en, this message translates to:
  /// **'Nominee\'s photo ID and address proof (Aadhaar / PAN)'**
  String get deathDoc3;

  /// No description provided for @deathDoc4.
  ///
  /// In en, this message translates to:
  /// **'Nominee\'s bank details (cancelled cheque)'**
  String get deathDoc4;

  /// No description provided for @deathDoc5.
  ///
  /// In en, this message translates to:
  /// **'Medical records or hospital discharge summary (if applicable)'**
  String get deathDoc5;

  /// No description provided for @deathDoc6.
  ///
  /// In en, this message translates to:
  /// **'FIR and post-mortem report (for accidental death)'**
  String get deathDoc6;

  /// No description provided for @shareSubject.
  ///
  /// In en, this message translates to:
  /// **'My {type} insurance details'**
  String shareSubject(String type);

  /// No description provided for @shareBody.
  ///
  /// In en, this message translates to:
  /// **'Keep this safe.\n\n{name} — {type} insurance\nPolicy number: {number}\nCover: {cover}\nNominees: {nominees}\n\nIf something happens to me:\n{steps}'**
  String shareBody(String name, String type, String number, String cover, String nominees, String steps);

  /// No description provided for @seePolicyDocument.
  ///
  /// In en, this message translates to:
  /// **'see policy document'**
  String get seePolicyDocument;

  /// No description provided for @addNominee.
  ///
  /// In en, this message translates to:
  /// **'Add nominee'**
  String get addNominee;

  /// No description provided for @fullyAssigned.
  ///
  /// In en, this message translates to:
  /// **'100% of the claim amount is assigned'**
  String get fullyAssigned;

  /// No description provided for @noNomineeYet.
  ///
  /// In en, this message translates to:
  /// **'No nominee recorded yet'**
  String get noNomineeYet;

  /// No description provided for @assignedLeft.
  ///
  /// In en, this message translates to:
  /// **'{assigned}% assigned · {left}% left'**
  String assignedLeft(int assigned, int left);

  /// No description provided for @nomineeLegalNote.
  ///
  /// In en, this message translates to:
  /// **'This is your own record. The nominee that counts legally is the one registered with your insurer — keep them the same.'**
  String get nomineeLegalNote;

  /// No description provided for @minorAppointee.
  ///
  /// In en, this message translates to:
  /// **'Minor · appointee: {name}'**
  String minorAppointee(String name);

  /// No description provided for @notSet.
  ///
  /// In en, this message translates to:
  /// **'not set'**
  String get notSet;

  /// No description provided for @ifSomethingHappens.
  ///
  /// In en, this message translates to:
  /// **'If something happens to you'**
  String get ifSomethingHappens;

  /// No description provided for @docsFamilyNeeds.
  ///
  /// In en, this message translates to:
  /// **'Documents your family will need'**
  String get docsFamilyNeeds;

  /// No description provided for @shareWithFamily.
  ///
  /// In en, this message translates to:
  /// **'Share these details with family'**
  String get shareWithFamily;

  /// No description provided for @needAppointee.
  ///
  /// In en, this message translates to:
  /// **'Add an appointee — an adult who receives the money for a minor.'**
  String get needAppointee;

  /// No description provided for @editNominee.
  ///
  /// In en, this message translates to:
  /// **'Edit nominee'**
  String get editNominee;

  /// No description provided for @pickFromFamily.
  ///
  /// In en, this message translates to:
  /// **'Pick from family'**
  String get pickFromFamily;

  /// No description provided for @fullNameAsPolicy.
  ///
  /// In en, this message translates to:
  /// **'Full name (as in the policy)'**
  String get fullNameAsPolicy;

  /// No description provided for @relationship.
  ///
  /// In en, this message translates to:
  /// **'Relationship'**
  String get relationship;

  /// No description provided for @shareOfClaim.
  ///
  /// In en, this message translates to:
  /// **'Share of claim: {percent}%'**
  String shareOfClaim(int percent);

  /// No description provided for @appointeeLabel.
  ///
  /// In en, this message translates to:
  /// **'Appointee (adult who receives money for the minor)'**
  String get appointeeLabel;

  /// No description provided for @phoneOptional.
  ///
  /// In en, this message translates to:
  /// **'Phone (optional)'**
  String get phoneOptional;

  /// No description provided for @removeNominee.
  ///
  /// In en, this message translates to:
  /// **'Remove nominee'**
  String get removeNominee;

  /// No description provided for @notFoundFillIn.
  ///
  /// In en, this message translates to:
  /// **'Not found in document — please fill in'**
  String get notFoundFillIn;

  /// No description provided for @doubleCheck.
  ///
  /// In en, this message translates to:
  /// **'Please double-check this'**
  String get doubleCheck;

  /// No description provided for @startBeforeEnd.
  ///
  /// In en, this message translates to:
  /// **'Start date must be before end date.'**
  String get startBeforeEnd;

  /// No description provided for @checkPolicyDetails.
  ///
  /// In en, this message translates to:
  /// **'Check your policy details'**
  String get checkPolicyDetails;

  /// No description provided for @enterPolicyDetails.
  ///
  /// In en, this message translates to:
  /// **'Enter policy details'**
  String get enterPolicyDetails;

  /// No description provided for @editPolicyDetails.
  ///
  /// In en, this message translates to:
  /// **'Edit policy details'**
  String get editPolicyDetails;

  /// No description provided for @weReadDetails.
  ///
  /// In en, this message translates to:
  /// **'We read these details from your document. Please check them carefully — fields marked in amber need your attention.'**
  String get weReadDetails;

  /// No description provided for @insuranceType.
  ///
  /// In en, this message translates to:
  /// **'Insurance type'**
  String get insuranceType;

  /// No description provided for @insurerRequired.
  ///
  /// In en, this message translates to:
  /// **'Insurer is required'**
  String get insurerRequired;

  /// No description provided for @planName.
  ///
  /// In en, this message translates to:
  /// **'Plan name'**
  String get planName;

  /// No description provided for @idvRupees.
  ///
  /// In en, this message translates to:
  /// **'IDV (₹)'**
  String get idvRupees;

  /// No description provided for @sumAssuredRupees.
  ///
  /// In en, this message translates to:
  /// **'Sum assured (₹)'**
  String get sumAssuredRupees;

  /// No description provided for @sumInsuredRupees.
  ///
  /// In en, this message translates to:
  /// **'Sum insured (₹)'**
  String get sumInsuredRupees;

  /// No description provided for @premiumRupees.
  ///
  /// In en, this message translates to:
  /// **'Premium (₹)'**
  String get premiumRupees;

  /// No description provided for @premiumFrequency.
  ///
  /// In en, this message translates to:
  /// **'Premium frequency'**
  String get premiumFrequency;

  /// No description provided for @notSure.
  ///
  /// In en, this message translates to:
  /// **'Not sure'**
  String get notSure;

  /// No description provided for @confirmAddPolicy.
  ///
  /// In en, this message translates to:
  /// **'Confirm & add policy'**
  String get confirmAddPolicy;

  /// No description provided for @select.
  ///
  /// In en, this message translates to:
  /// **'Select'**
  String get select;

  /// No description provided for @whoIsCoveredQ.
  ///
  /// In en, this message translates to:
  /// **'Who is covered?'**
  String get whoIsCoveredQ;

  /// No description provided for @addFamilyMembers.
  ///
  /// In en, this message translates to:
  /// **'Add family members'**
  String get addFamilyMembers;
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
