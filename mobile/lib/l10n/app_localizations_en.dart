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
}
