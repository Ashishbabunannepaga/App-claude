/// Static, reviewed claim guidance (V1 is content, not AI).
/// TODO(Week 8): have this content reviewed by an insurance domain expert before launch.
class ClaimGuide {
  const ClaimGuide(this.title, this.steps, this.documents);
  final String title;
  final List<String> steps;
  final List<String> documents;
}

const claimGuides = <String, ClaimGuide>{
  'health': ClaimGuide(
    'Health insurance claim',
    [
      'Check that the hospital is in your insurer\'s network (for cashless treatment).',
      'Planned admission: request cashless pre-authorisation at the hospital\'s insurance desk at least 48 hours before.',
      'Emergency admission: inform your insurer or TPA within 24 hours.',
      'Show your health card / policy number and photo ID at the hospital.',
      'For reimbursement (non-network hospital), pay the bill and submit the claim within the time stated in your policy.',
      'Track your claim with the claim reference number your insurer gives you.',
    ],
    [
      'Claim form (signed)',
      'Policy copy / health card',
      'Photo ID and address proof',
      'Discharge summary',
      'Original hospital bills and payment receipts',
      'Doctor\'s prescriptions and investigation reports',
      'Cancelled cheque or bank details (for reimbursement)',
    ],
  ),
  'motor': ClaimGuide(
    'Motor insurance claim',
    [
      'Ensure everyone is safe. For theft or third-party injury, file an FIR with the police.',
      'Inform your insurer as soon as possible and get a claim number.',
      'Do not repair the vehicle before the insurer\'s surveyor inspects it (unless told otherwise).',
      'Take the vehicle to a network garage for cashless repair, or any garage for reimbursement.',
      'Pay any compulsory deductible and non-covered items; the insurer settles the rest.',
    ],
    [
      'Claim form',
      'Policy copy',
      'Registration certificate (RC)',
      'Driving licence of the driver',
      'FIR (for theft, major accident or third-party claims)',
      'Repair estimate and final invoice',
    ],
  ),
  'life': ClaimGuide(
    'Life insurance claim',
    [
      'The nominee should inform the insurer as soon as possible.',
      'Collect the claim form from the insurer\'s branch or website.',
      'Submit the form with the required documents.',
      'The insurer may investigate claims made within the first few policy years.',
      'Track the claim status with the insurer.',
    ],
    [
      'Claim form',
      'Original policy document',
      'Death certificate',
      'Nominee\'s photo ID, address proof and bank details',
      'Medical records / FIR and post-mortem report (if applicable)',
    ],
  ),
  'other': ClaimGuide(
    'Making a claim',
    [
      'Read your policy to confirm the event is covered.',
      'Inform your insurer as soon as possible and get a claim number.',
      'Submit the claim form and supporting documents.',
      'Track your claim with the insurer.',
    ],
    ['Claim form', 'Policy copy', 'Photo ID', 'Proof of loss / bills'],
  ),
};
