import 'package:flutter_test/flutter_test.dart';
import 'package:insureiq/core/utils/formatters.dart';

void main() {
  test('formats rupees in the Indian numbering system', () {
    expect(formatInr(1000000), '₹10,00,000');
    expect(formatInr(null), '—');
  });

  test('compact lakh / crore formatting', () {
    expect(formatInrCompact(1000000), '₹10 L');
    expect(formatInrCompact(15000000), '₹1.5 Cr');
    expect(formatInrCompact(24580), '₹24,580');
  });

  test('humanise snake_case keys', () {
    expect(humanise('room_rent_limit'), 'Room rent limit');
    expect(humanise('ncb_percentage'), 'NCB percentage');
    expect(humanise('idv'), 'IDV');
    expect(humanise('own_damage_premium'), 'Own damage premium');
  });

  test('detail values: rupees, percentages, lists, text', () {
    expect(formatDetailValue('own_damage_premium', '3237.78'), '₹3,237.78');
    expect(formatDetailValue('third_party_premium', 2094), '₹2,094');
    expect(formatDetailValue('compulsory_deductible', '1000'), '₹1,000');
    expect(formatDetailValue('ncb_percentage', '25'), '25%');
    expect(formatDetailValue('add_ons', ['Engine Secure', 'Key Replacement']), 'Engine Secure, Key Replacement');
    expect(formatDetailValue('room_rent_limit', '1% of sum insured'), '1% of sum insured');
    expect(formatDetailValue('waiting_period', '24'), '24'); // a number, but not an amount
    expect(formatDetailValue('roadside_assistance', null), '—');
  });
}
