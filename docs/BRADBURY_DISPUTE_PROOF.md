# Bradbury dispute proof

This log records the live disputed-flow test on GenLayer's Bradbury testnet. It
distinguishes confirmed on-chain results from transactions that are still
pending; a pending transaction is not presented as a successful adjudication.

## Corrected deployment

- Contract: `0x6841fbaD4950Bf50CE55076e5b69b0BFE65DE8A4`
- Deployment: `0xfadbb4711984a484b63db3a7d94f9490f4be21caae376f15af619340086c6579`
- Funding (0.01 GEN): `0xa49903fa9608f88fc2ba248cd0e33a346426f850afee71840ab1567f18eddb57`
- Evidence submission: `0x97c61f45f77a21161add010404677a3d12846ebb612b056d744bf107df497b28`
- Dispute opening: `0xc35449b4ad32849edb9e86d8718515a861ba717c43f8895f7a2d4300a759080e`
- AI-jury invocation: `0x5a078990e478185c2eb46343aad1300d2a16abbfc8355881c558f38231a577a5`

Deployment, funding, evidence submission, and dispute opening each reached
`ACCEPTED` with validator agreement. At the end of the 2026-08-28 observation
window, the AI-jury invocation remained `PROPOSING`; its selected leader had
not published public execution data. The contract therefore correctly remained
`DISPUTED`, with `settled: false`, zero recorded payouts, and no resolution.
The transaction can be rechecked by hash without submitting a duplicate call.

The live rubric assesses Example Domain using three criteria: accurate source
characterization (4,000 bps), executive summary (3,000 bps), and limitations
(3,000 bps). The evidence consists of `https://example.com` plus a self-contained
text report.

## Regression discovered during the first attempt

An earlier immutable deployment at
`0xf840d37C15A4B1ad985F72EDF6e6c7B0CDD39073` exposed a real GenVM constraint.
Its resolution transaction
`0x04eb4a35b9e591882b6498f43588dadf7d94388417287bfd1820b8b0f41349f9`
ended `UNDETERMINED` / `FINISHED_WITH_ERROR`: the nondeterministic callbacks
captured `self.require_url_hashes`, causing a forbidden storage read in
nondeterministic mode before any web or LLM call.

The corrected contract copies that value into memory before constructing both
callbacks. A regression test now asserts that neither nondeterministic callback
captures `self`. The earlier contract remains safely disputed and can apply its
precommitted 50/50 fallback through `claim_dispute_timeout()` after its deadline.
