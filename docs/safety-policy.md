# Operational safety policy

Version: safety-1.4. English, fictional student scenarios only. These states are application routes, not clinical assessments. Templates and labels were author-reviewed; independent student and clinical review have not occurred.

## Route a message

1. Normalize Unicode and a small documented set of spelling variants; screen the complete input for explicit danger before rejecting length. Never silently truncate danger. Reject empty, nontext or overlong input with a fixed safety-check fallback. UI limit: 2,000 characters.
2. A latched escalation or explicit danger rule immediately displays the fixed escalation template without an LLM call. Messages receive this screen on every turn.
3. For remaining valid input, give the constrained LLM classifier the latest eight history messages plus the current message. Validate an exact single-field JSON safety label. The model wire values NO_SAFETY_SIGNAL, UNCERTAIN_SAFETY and CURRENT_DANGER map to ROUTINE, CLARIFY and ESCALATE; ordinary requests for clarification are distinct from uncertainty about personal safety. Current credible danger may be promoted to ESCALATE. The classifier cannot downgrade a rule's CLARIFY result.
4. Ambiguity produces a fixed direct safety question. Boundary requests receive a refusal plus the safety question. A positive short reply to a safety clarification escalates. Negative replies are screened in context.
5. Only ROUTINE may call the supportive generator. A deterministic output check rejects prohibited patterns, medical/diagnostic language, harm language, secrecy/guarantees, invented contacts/URLs, contact-like numeric strings, numeric medication doses, clinical scores and malformed/long text. Ordinary short times, durations and counts are permitted. Replace rejected output with a fixed safety check; never show the rejected text.
6. Invalid classifier output, timeout, incomplete model output, runtime exception or failed generation returns SAFE_FALLBACK. Do not expose exception details. Explicit-rule crisis routing remains independent of model availability.

## Follow-up and reset

After any escalation, all later messages in that session receive the same crisis referral. “I am fine,” a joke request, an instruction override or elapsed time never clears the latch. Only the visible **Clear session / start fresh** control clears both history and latch and returns to the opening notice. This conservative choice can over-refer after danger has passed; the prototype does not verify real-world safety. Each evaluation dialogue starts a fresh Session. Context/display histories are bounded in memory; ordinary chat is not persisted.

## Referrals

The default region is unknown. No regional contacts have been independently verified, so `config/resources.json` intentionally has no contacts. The fixed template gives general local emergency, emergency department, trusted nearby person and campus staff guidance without numbers, links, or a location assumption. No person or service is automatically contacted.

The resource loader rejects missing, expired, unapproved or malformed entries; source URLs must use HTTPS. Metadata cannot itself prove the source is official: a maintainer must actually verify it and record dates. Adding regional contacts requires connecting a user-selected region and revalidating display behavior. The current UI intentionally offers only general guidance and does not use inferred location.

The templates follow the principles of asking directly, listening without judgment, connecting to people, and reducing immediate exposure to danger described by [NIMH](https://www.nimh.nih.gov/health/publications/5-action-steps-to-help-someone-having-thoughts-of-suicide) (consulted 2026-11-12). No source telephone number is copied into this project.

## Known limits

Regexes and a small general-purpose model cannot recognize every expression, language, euphemism, context, encoding or prompt injection. Output filtering can miss unsafe paraphrases and can also reject benign wording. Latency limits are local read timeouts, not an end-to-end service guarantee. The engine runs sequentially; a congested runtime can time out. This is an assessed synthetic prototype, not a deployed health service. Passing planted cases cannot establish clinical safety or effectiveness.
