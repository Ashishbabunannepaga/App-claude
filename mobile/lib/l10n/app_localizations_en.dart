// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get languageName => 'English';

  @override
  String get appLanguage => 'App language';

  @override
  String get appLanguageHelp => 'Buttons, menus and screens. AI answers have their own language setting.';

  @override
  String get skip => 'Skip';

  @override
  String get next => 'Next';

  @override
  String get getStarted => 'Get started';

  @override
  String get continueAction => 'Continue';

  @override
  String get cancel => 'Cancel';

  @override
  String get seeAll => 'See all';

  @override
  String get tryAgain => 'Try again';

  @override
  String get onb1Title => 'All your cover, one place';

  @override
  String get onb1Body => 'Health, life and motor policies for the whole family, kept safe and easy to find.';

  @override
  String get onb2Title => 'Ask in plain words';

  @override
  String get onb2Body => 'Every answer points to the page it came from, or tells you it isn\'t in your policy.';

  @override
  String get onb3Title => 'Renewals never sneak up';

  @override
  String get onb3Body => 'A gentle nudge well before your policy ends, so you are never left uncovered.';

  @override
  String get onb4Title => 'Family and nominees, sorted';

  @override
  String get onb4Body => 'See who is covered, who gets what, and what to do if something happens.';

  @override
  String get loginHeadline => 'All your insurance.\nOne place. Clearly explained.';

  @override
  String get loginSubhead => 'Add your policies, understand what you\'re covered for, and never miss a renewal.';

  @override
  String get mobileNumber => 'Mobile number';

  @override
  String get consentStart => 'I agree to the ';

  @override
  String get privacyPolicy => 'Privacy Policy';

  @override
  String get consentAnd => ' and ';

  @override
  String get terms => 'Terms';

  @override
  String get consentEnd => ', and consent to my policy documents being processed to provide this service.';

  @override
  String get getOtp => 'Get OTP';

  @override
  String get otpTitle => 'Enter the 6-digit code';

  @override
  String otpSentTo(String identifier) {
    return 'Sent to $identifier';
  }

  @override
  String get verify => 'Verify';

  @override
  String resendIn(int seconds) {
    return 'Resend code in ${seconds}s';
  }

  @override
  String get resendCode => 'Resend code';

  @override
  String get nameTitle => 'What should we call you?';

  @override
  String get fullName => 'Full name';

  @override
  String get dobOptional => 'Date of birth (optional)';

  @override
  String get navHome => 'Home';

  @override
  String get navPortfolio => 'Portfolio';

  @override
  String get navExplore => 'Explore';

  @override
  String get navProfile => 'Profile';

  @override
  String get addPolicy => 'Add policy';

  @override
  String hiName(String name) {
    return 'Hi $name';
  }

  @override
  String get helloThere => 'Hello there';

  @override
  String get homeSubtitle => 'Here\'s where your cover stands today.';

  @override
  String get whatToDo => 'What would you like to do?';

  @override
  String get comingUp => 'Coming up';

  @override
  String get coverageReport => 'Coverage report';

  @override
  String get askAi => 'Ask AI';

  @override
  String get claimHelp => 'Claim help';

  @override
  String get family => 'Family';

  @override
  String get nominees => 'Nominees';

  @override
  String get compare => 'Compare';

  @override
  String get emergencyCard => 'Emergency card';

  @override
  String get seeCoverageReport => 'See your coverage report';

  @override
  String get addAPolicy => 'Add a policy';

  @override
  String get seeSampleReport => 'See a sample report';

  @override
  String coinsEarned(int coins) {
    return '+$coins coins earned';
  }

  @override
  String get personalDetails => 'Personal details';

  @override
  String get dateOfBirth => 'Date of birth';

  @override
  String get city => 'City';

  @override
  String get state => 'State';

  @override
  String get save => 'Save';

  @override
  String get notifications => 'Notifications';

  @override
  String get renewalReminders => 'Renewal reminders';

  @override
  String get renewalRemindersHelp => '90, 60, 30, 15, 7 and 1 day before a policy expires';

  @override
  String get policyUpdates => 'Policy updates';

  @override
  String get policyUpdatesHelp => 'When a document has been read and is ready to review';

  @override
  String get notificationsPromise =>
      'We never send promotional notifications, and notifications never show your policy numbers, amounts or health details.';

  @override
  String get faqSafeQ => 'Is my data safe?';

  @override
  String get faqSafeA =>
      'Your documents are stored encrypted and are only accessible to you. We do not sell your data or share it with insurers or agents.';

  @override
  String get faqAiQ => 'How does the AI answer my questions?';

  @override
  String get faqAiA =>
      'It reads only your own policy document and shows the page its answer came from. If the answer is not in your document it will say so instead of guessing.';

  @override
  String get faqWrongQ => 'The details extracted from my policy are wrong. What do I do?';

  @override
  String get faqWrongA =>
      'Open the policy, tap the ⋮ menu and choose \"Edit details\". Anything you correct is saved as confirmed by you.';

  @override
  String get faqUploadQ => 'Which documents can I upload?';

  @override
  String get faqUploadA =>
      'PDF policy documents work best. You can also upload a clear photo (JPG/PNG) up to 20 MB. Password-protected PDFs must be unlocked first.';

  @override
  String get faqSellQ => 'Do you sell insurance?';

  @override
  String faqSellA(String app) {
    return 'No. $app helps you organise and understand the policies you already have. We do not sell or recommend insurance products.';
  }

  @override
  String get faqDeleteQ => 'How do I delete my account?';

  @override
  String get faqDeleteA => 'Profile → Privacy & data → Delete account. Your data is permanently deleted after 7 days.';

  @override
  String get supportThanks => 'Thanks — we\'ll get back to you within 2 working days.';

  @override
  String get helpSupport => 'Help & support';

  @override
  String get faqTitle => 'Frequently asked questions';

  @override
  String get contactUs => 'Contact us';

  @override
  String get topic => 'Topic';

  @override
  String get topicQuestion => 'A question';

  @override
  String get topicProblem => 'Something isn\'t working';

  @override
  String get topicFeedback => 'Feedback';

  @override
  String get topicPrivacy => 'Privacy / my data';

  @override
  String get topicGrievance => 'Complaint (grievance)';

  @override
  String get howCanWeHelp => 'How can we help?';

  @override
  String get send => 'Send';

  @override
  String get emailUsInstead => 'Email us instead';

  @override
  String get deleteAccountQ => 'Delete your account?';

  @override
  String get deleteAccountBody =>
      'Your account will be disabled now. All your policies, documents and data will be permanently deleted after 7 days. Logging in again within 7 days cancels the deletion.';

  @override
  String get deleteAccount => 'Delete account';

  @override
  String get privacyData => 'Privacy & data';

  @override
  String get privacyPromise =>
      'We use your policy documents only to show, explain and remind you about your own insurance. Documents are encrypted, never sold, and never shared with insurers or agents. AI processing uses providers contractually barred from training on your data.';

  @override
  String get downloadMyData => 'Download my data';

  @override
  String get downloadMyDataHelp => 'A copy of your profile, policies and questions';

  @override
  String get privacyPolicyItem => 'Privacy policy';

  @override
  String get grievanceOfficer => 'Grievance officer';

  @override
  String get deleteAccountHelp => 'Permanently delete all your data';

  @override
  String get appLock => 'App lock';

  @override
  String get appLockHelp => 'Use fingerprint, face or device PIN to open the app';

  @override
  String get setUpScreenLock => 'Set up a screen lock on your phone first.';

  @override
  String get aiAnswerLanguage => 'AI answer language';

  @override
  String get aiAnswerLanguageHelp =>
      'Summaries and answers about your policies will be written in this language. You can ask questions in it too.';
}
