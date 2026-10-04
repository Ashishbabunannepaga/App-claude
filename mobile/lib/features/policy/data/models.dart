double? _num(Object? v) => v == null ? null : double.tryParse(v.toString());
DateTime? _date(Object? v) => v == null ? null : DateTime.parse(v as String);

class Policy {
  Policy({
    required this.id,
    required this.policyType,
    required this.verified,
    required this.source,
    required this.status,
    required this.fieldConfidence,
    required this.details,
    this.documentId,
    this.insurer,
    this.planName,
    this.policyNumber,
    this.startDate,
    this.endDate,
    this.premium,
    this.sumInsured,
    this.paymentFrequency,
    this.extractionConfidence,
    this.daysToExpiry,
  });

  final String id;
  final String? documentId;
  final String policyType;
  final String? insurer;
  final String? planName;
  final String? policyNumber;
  final DateTime? startDate;
  final DateTime? endDate;
  final double? premium;
  final double? sumInsured;
  final String? paymentFrequency;
  final bool verified;
  final String source;
  final double? extractionConfidence;
  final Map<String, double> fieldConfidence;
  final Map<String, dynamic> details;

  /// active | expiring_soon | expired | unknown
  final String status;
  final int? daysToExpiry;

  String get displayName => insurer ?? 'Untitled policy';

  factory Policy.fromJson(Map<String, dynamic> j) => Policy(
    id: j['id'] as String,
    documentId: j['document_id'] as String?,
    policyType: j['policy_type'] as String,
    insurer: j['insurer'] as String?,
    planName: j['plan_name'] as String?,
    policyNumber: j['policy_number'] as String?,
    startDate: _date(j['start_date']),
    endDate: _date(j['end_date']),
    premium: _num(j['premium']),
    sumInsured: _num(j['sum_insured']),
    paymentFrequency: j['payment_frequency'] as String?,
    verified: j['verified'] as bool,
    source: j['source'] as String,
    extractionConfidence: _num(j['extraction_confidence']),
    fieldConfidence: (j['field_confidence'] as Map? ?? {}).map((k, v) => MapEntry(k as String, _num(v) ?? 0)),
    details: Map<String, dynamic>.from(j['details'] as Map? ?? {}),
    status: j['status'] as String,
    daysToExpiry: j['days_to_expiry'] as int?,
  );
}

class PolicyDocument {
  PolicyDocument({required this.id, required this.status, this.errorCode, this.policyId});

  final String id;

  /// uploaded | processing | extracted | failed
  final String status;
  final String? errorCode;
  final String? policyId;

  bool get isDone => status == 'extracted' || status == 'failed';

  factory PolicyDocument.fromJson(Map<String, dynamic> j) => PolicyDocument(
    id: j['id'] as String,
    status: j['status'] as String,
    errorCode: j['error_code'] as String?,
    policyId: j['policy_id'] as String?,
  );

  String get errorText => switch (errorCode) {
    'pdf_password_protected' => 'This PDF is password-protected. Please upload an unlocked copy.',
    'pdf_too_many_pages' => 'This document has too many pages. Please upload only the policy schedule and wording.',
    'pdf_unreadable' => 'We couldn\'t open this file. It may be damaged.',
    'no_text_found' => 'We couldn\'t read any text. Try a clearer photo or the original PDF.',
    'ocr_unavailable' =>
      'Scanned documents can\'t be read right now. Please upload a digital PDF or enter details manually.',
    'ai_unavailable' => 'Our reading service is busy. Please retry in a minute.',
    _ => 'We couldn\'t process this document.',
  };
}

class Citation {
  Citation({this.page, this.section, required this.excerpt});
  final int? page;
  final String? section;
  final String excerpt;

  factory Citation.fromJson(Map<String, dynamic> j) =>
      Citation(page: j['page'] as int?, section: j['section'] as String?, excerpt: j['excerpt'] as String);

  String get label => [if (page != null) 'Page $page', if (section != null) section].join(' · ');
}

class Answer {
  Answer({
    required this.id,
    required this.question,
    required this.answer,
    required this.answerable,
    required this.confidence,
    required this.citations,
    required this.disclaimer,
  });

  final String id;
  final String question;
  final String answer;
  final bool answerable;
  final String confidence;
  final List<Citation> citations;
  final String disclaimer;

  factory Answer.fromJson(Map<String, dynamic> j) => Answer(
    id: j['id'] as String,
    question: j['question'] as String,
    answer: j['answer'] as String,
    answerable: j['answerable'] as bool,
    confidence: j['confidence'] as String,
    citations: (j['citations'] as List).map((c) => Citation.fromJson(c as Map<String, dynamic>)).toList(),
    disclaimer: j['disclaimer'] as String,
  );
}

class PolicySummary {
  PolicySummary({required this.headline, required this.keyPoints, required this.watchOuts, required this.disclaimer});
  final String headline;
  final List<String> keyPoints;
  final List<String> watchOuts;
  final String disclaimer;

  factory PolicySummary.fromJson(Map<String, dynamic> j) => PolicySummary(
    headline: j['headline'] as String,
    keyPoints: List<String>.from(j['key_points'] as List),
    watchOuts: List<String>.from(j['watch_outs'] as List),
    disclaimer: j['disclaimer'] as String,
  );
}

class RenewalItem {
  RenewalItem({
    required this.policyId,
    required this.policyType,
    this.insurer,
    required this.endDate,
    required this.daysToExpiry,
  });
  final String policyId;
  final String policyType;
  final String? insurer;
  final DateTime endDate;
  final int daysToExpiry;

  factory RenewalItem.fromJson(Map<String, dynamic> j) => RenewalItem(
    policyId: j['policy_id'] as String,
    policyType: j['policy_type'] as String,
    insurer: j['insurer'] as String?,
    endDate: DateTime.parse(j['end_date'] as String),
    daysToExpiry: j['days_to_expiry'] as int,
  );
}

class PortfolioSummary {
  PortfolioSummary({
    required this.totalPolicies,
    required this.activePolicies,
    required this.expiringSoon,
    required this.pendingVerification,
    required this.totalAnnualPremium,
    required this.healthCover,
    required this.lifeCover,
    required this.byType,
    required this.upcomingRenewals,
  });

  final int totalPolicies;
  final int activePolicies;
  final int expiringSoon;
  final int pendingVerification;
  final double totalAnnualPremium;
  final double healthCover;
  final double lifeCover;
  final Map<String, int> byType;
  final List<RenewalItem> upcomingRenewals;

  factory PortfolioSummary.fromJson(Map<String, dynamic> j) => PortfolioSummary(
    totalPolicies: j['total_policies'] as int,
    activePolicies: j['active_policies'] as int,
    expiringSoon: j['expiring_soon'] as int,
    pendingVerification: j['pending_verification'] as int,
    totalAnnualPremium: _num(j['total_annual_premium']) ?? 0,
    healthCover: _num(j['health_cover']) ?? 0,
    lifeCover: _num(j['life_cover']) ?? 0,
    byType: Map<String, int>.from(j['by_type'] as Map),
    upcomingRenewals: (j['upcoming_renewals'] as List)
        .map((r) => RenewalItem.fromJson(r as Map<String, dynamic>))
        .toList(),
  );
}
