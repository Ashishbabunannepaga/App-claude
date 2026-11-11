import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:insureiq/core/network/api_exception.dart';
import 'package:insureiq/core/storage/token_storage.dart';
import 'package:insureiq/features/auth/data/auth_repository.dart';
import 'package:insureiq/features/auth/data/phone_gateway.dart';

/// Phone login through Firebase: Firebase sends and checks the SMS code, our backend verifies
/// Firebase's ID token and signs the user in. Without Firebase, the backend's own OTP is used.
class _Gateway implements PhoneGateway {
  final sent = <String>[];
  final confirmed = <(String, String)>[];
  Object? confirmError;

  @override
  Future<String> sendCode(String phoneE164) async {
    sent.add(phoneE164);
    return 'verification-1';
  }

  @override
  Future<String> confirmCode(String verificationId, String code) async {
    confirmed.add((verificationId, code));
    if (confirmError != null) throw confirmError!;
    return 'firebase-id-token';
  }
}

class _Tokens extends TokenStorage {
  String? access;
  @override
  Future<void> save({required String access, required String refresh}) async => this.access = access;
}

/// A Dio that records requests and answers like the backend.
(Dio, List<RequestOptions>) _backend() {
  final dio = Dio(BaseOptions(baseUrl: 'http://api.test/api/v1'));
  final seen = <RequestOptions>[];
  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (o, h) {
        seen.add(o);
        final data = switch (o.path) {
          '/auth/otp/request' => {'identifier': '+919876543210', 'expires_in': 300, 'resend_after': 30},
          _ => {
            'access_token': 'our-access',
            'refresh_token': 'our-refresh',
            'user': {'id': 'u1', 'phone': '+919876543210'},
          },
        };
        h.resolve(Response(requestOptions: o, statusCode: 200, data: data));
      },
    ),
  );
  return (dio, seen);
}

void main() {
  test('phone numbers are sent to Firebase in +91 form', () {
    expect(AuthRepository.e164('98765 43210'), '+919876543210');
    expect(AuthRepository.e164('919876543210'), '+919876543210');
    expect(AuthRepository.e164('+447700900123'), '+447700900123');
  });

  test('with Firebase: Firebase sends the SMS, and the backend gets Firebase\'s proof', () async {
    final gateway = _Gateway();
    final tokens = _Tokens();
    final (dio, seen) = _backend();
    final repo = AuthRepository(dio, tokens, gateway);

    final challenge = await repo.requestOtp('9876543210');
    expect(gateway.sent, ['+919876543210']);
    expect(challenge.identifier, '+919876543210');
    expect(seen, isEmpty, reason: 'no backend OTP request when Firebase sends the SMS');

    final user = await repo.verifyOtp(challenge.identifier, '246810', consent: true, contactConsent: true);
    expect(gateway.confirmed, [('verification-1', '246810')]);
    expect(seen.single.path, '/auth/firebase');
    expect(seen.single.data, {'id_token': 'firebase-id-token', 'consent': true, 'contact_consent': true});
    expect(user.id, 'u1');
    expect(tokens.access, 'our-access', reason: 'the session is ours, not Firebase\'s');
  });

  test('with Firebase: a wrong code shows our message and nothing reaches the backend', () async {
    final gateway = _Gateway()..confirmError = firebaseError(FirebaseAuthException(code: 'invalid-verification-code'));
    final (dio, seen) = _backend();
    final repo = AuthRepository(dio, _Tokens(), gateway);
    final challenge = await repo.requestOtp('9876543210');
    await expectLater(
      repo.verifyOtp(challenge.identifier, '000000', consent: true),
      throwsA(isA<ApiException>().having((e) => e.code, 'code', 'invalid-verification-code')),
    );
    expect(seen, isEmpty);
  });

  test('Firebase errors become clear messages', () {
    expect(firebaseError(FirebaseAuthException(code: 'too-many-requests')).message, contains('Too many'));
    expect(firebaseError(FirebaseAuthException(code: 'session-expired')).message, contains('expired'));
    expect(firebaseError(FirebaseAuthException(code: 'network-request-failed')).code, 'offline');
    expect(firebaseError(FirebaseAuthException(code: 'something-new')).message, contains("couldn't send"));
  });

  test('without Firebase: the backend\'s own OTP, as before', () async {
    final (dio, seen) = _backend();
    final repo = AuthRepository(dio, _Tokens());
    final challenge = await repo.requestOtp('9876543210');
    await repo.verifyOtp(challenge.identifier, '246810', consent: true);
    expect(seen.map((o) => o.path), ['/auth/otp/request', '/auth/otp/verify']);
  });

  test('email sign-in never goes through Firebase', () async {
    final gateway = _Gateway();
    final (dio, seen) = _backend();
    await AuthRepository(dio, _Tokens(), gateway).requestOtp('asha@example.com');
    expect(gateway.sent, isEmpty);
    expect(seen.single.path, '/auth/otp/request');
  });
}
