import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/strings.dart';

/// Sends the SMS code and checks it through Firebase Authentication, so Google is the registered
/// SMS sender (no DLT registration of our own). The result is a Firebase ID token, which our
/// backend verifies before signing the user in with its own session.
abstract class PhoneGateway {
  /// Starts verification for an E.164 number; completes with Firebase's verification id once the
  /// SMS is sent.
  Future<String> sendCode(String phoneE164);

  /// Checks [code] against [verificationId]; returns a Firebase ID token proving the phone number.
  Future<String> confirmCode(String verificationId, String code);
}

class FirebasePhoneGateway implements PhoneGateway {
  FirebasePhoneGateway([FirebaseAuth? auth]) : _auth = auth ?? FirebaseAuth.instance;
  final FirebaseAuth _auth;

  @override
  Future<String> sendCode(String phoneE164) {
    final done = Completer<String>();
    _auth.verifyPhoneNumber(
      phoneNumber: phoneE164,
      timeout: const Duration(seconds: 60),
      codeSent: (verificationId, _) {
        if (!done.isCompleted) done.complete(verificationId);
      },
      verificationFailed: (e) {
        if (!done.isCompleted) done.completeError(firebaseError(e));
      },
      // Android may read the SMS by itself; the user still confirms on the code screen, which
      // keeps one path (and the consent choices) for every phone.
      verificationCompleted: (_) {},
      codeAutoRetrievalTimeout: (_) {},
    );
    return done.future;
  }

  @override
  Future<String> confirmCode(String verificationId, String code) async {
    try {
      final result = await _auth.signInWithCredential(
        PhoneAuthProvider.credential(verificationId: verificationId, smsCode: code),
      );
      final token = await result.user?.getIdToken(true);
      if (token == null) throw ApiException('firebase_no_token', strings.errProcessing);
      // Our backend keeps the session from here; Firebase's own sign-in isn't needed any more.
      await _auth.signOut();
      return token;
    } on FirebaseAuthException catch (e) {
      throw firebaseError(e);
    }
  }
}

/// Firebase's error codes as the app's own messages.
ApiException firebaseError(FirebaseAuthException e) => switch (e.code) {
  'invalid-verification-code' => ApiException(e.code, strings.otpWrongCode),
  'session-expired' || 'code-expired' => ApiException(e.code, strings.otpExpired),
  'invalid-phone-number' => ApiException(e.code, strings.invalidPhone),
  'too-many-requests' || 'quota-exceeded' => ApiException(e.code, strings.otpTooMany),
  'network-request-failed' => ApiException('offline', strings.timedOut),
  _ => ApiException(e.code, strings.otpSendFailed),
};

/// Firebase phone login is used when the app was built with a Firebase project
/// (FIREBASE_* dart-defines, see Env) and Firebase started; otherwise the backend's own OTP.
final phoneGatewayProvider = Provider<PhoneGateway?>((ref) {
  if (kIsWeb || Firebase.apps.isEmpty) return null;
  return FirebasePhoneGateway();
});
