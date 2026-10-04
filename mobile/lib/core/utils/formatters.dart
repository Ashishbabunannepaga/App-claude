import 'package:intl/intl.dart';

final _inr = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);
final _date = DateFormat('d MMM yyyy');

String formatInr(num? value) => value == null ? '—' : _inr.format(value);

/// ₹10,00,000 → "₹10 L", ₹1,50,00,000 → "₹1.5 Cr".
String formatInrCompact(num? value) {
  if (value == null) return '—';
  String trim(double v) => v.toStringAsFixed(v.truncateToDouble() == v ? 0 : 1);
  if (value >= 10000000) return '₹${trim(value / 10000000)} Cr';
  if (value >= 100000) return '₹${trim(value / 100000)} L';
  return formatInr(value);
}

String formatDate(DateTime? d) => d == null ? '—' : _date.format(d);

String policyTypeLabel(String type) => switch (type) {
  'health' => 'Health',
  'life' => 'Life',
  'motor' => 'Motor',
  _ => 'Other',
};

String humanise(String key) {
  final words = key.replaceAll('_', ' ');
  return words.isEmpty ? words : words[0].toUpperCase() + words.substring(1);
}
