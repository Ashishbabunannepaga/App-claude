import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/env.dart';

/// A user-presentable error. `code` mirrors the backend's stable error codes.
class ApiException implements Exception {
  ApiException(this.code, this.message, {this.statusCode, this.fields = const {}});

  final String code;
  final String message;
  final int? statusCode;
  final Map<String, String> fields;

  factory ApiException.fromDio(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['error'] is Map) {
      final err = data['error'] as Map;
      return ApiException(
        err['code']?.toString() ?? 'error',
        err['message']?.toString() ?? 'Something went wrong',
        statusCode: e.response?.statusCode,
        fields: (err['fields'] as Map?)?.map((k, v) => MapEntry(k.toString(), v.toString())) ?? const {},
      );
    }
    return switch (e.type) {
      DioExceptionType.connectionTimeout || DioExceptionType.sendTimeout || DioExceptionType.receiveTimeout =>
        ApiException('timeout', 'The connection timed out. Please try again.${kDebugMode ? _devHint : ''}'),
      DioExceptionType.connectionError => ApiException(
        'offline',
        // Debug builds also show the address being tried, which makes "wrong server address" obvious.
        'Can\'t reach the server. Check your internet connection.${kDebugMode ? _devHint : ''}',
      ),
      _ => ApiException('error', 'Something went wrong. Please try again.', statusCode: e.response?.statusCode),
    };
  }

  @override
  String toString() => message;
}

String errorMessage(Object error) => error is ApiException ? error.message : 'Something went wrong. Please try again.';

/// Debug builds only: which address failed and the usual fix for a phone.
String get _devHint =>
    '\nTrying: ${Env.apiBaseUrl}'
    '\nPhone? Start the backend, run "adb reverse tcp:8000 tcp:8000", then restart the app.';
