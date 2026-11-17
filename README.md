# PatchBraid

A standalone GenLayer primitive for **certifying whether two natural-language configuration changes can safely change order**.

“Set the retry limit to one” and “increase it by one” look harmless independently, yet their order changes the result. Even edits with the same final value at the current configuration may differ on another legal starting state or near a numeric boundary. PatchBraid does not ask a model whether two changes “seem compatible.” GenLayer independently compiles each instruction into a bounded executable program; deterministic code then checks both orders on **every declared state**, retaining a concrete conflict witness and a hash of the complete behavior table.

A version-bound execution gate applies only certified commuting pairs to the contract's own configuration state, atomically and once per pair ticket. It does not mutate a server, deploy software or transfer assets.

## Workflow

1. Create a configuration space: 1–4 named integer variables, inclusive bounds, at most 256 combined states, and an initial value vector.
2. Register immutable change instructions. Each accepting validator independently compiles the instruction and requires equivalent success/failure and final values over the **entire finite domain**, then separately audits the candidate against the original text. Ambiguous or unsupported instructions remain UNKNOWN.
3. Analyze two KNOWN changes. The exact analyzer checks `A;B` versus `B;A` for all starting states and returns TOTAL_COMMUTE, PARTIAL_COMMUTE, CONFLICT or NO_COMMON_SUCCESS. It compares success domains as well as successful values; a boundary failure cannot be waved away.
4. Execute a safe pair under the exact certificate binding and current space revision. Even a PARTIAL_COMMUTE pair must succeed at the actual current state. Any rejection leaves the configuration and consumption ticket untouched. Successful execution records before/after state, authenticated actor, order and next revision.

## Why this needs GenLayer

Natural-language variables and step order require independently validated interpretation. Ordinary contracts can execute a supplied program but cannot establish that it implements an unstructured instruction. PatchBraid adds substantive semantic consensus, then uses finite function composition to make the safety result exact relative to the accepted programs and declared bounds. The AI never supplies the commutativity verdict, counterexample or resulting configuration.

Only SET, ADD and COPY are supported, with up to four ordered operations per change. There is no arbitrary Python, JavaScript, shell execution, hidden IO, clamping, rounding or guessed parameter. Complete-domain behavioral equivalence permits genuinely equivalent program syntax without tolerating a mismatch on a single legal state. Independent text auditing supplements equivalence, because two equal wrong programs would still be wrong interpretations.

## Deployment

- Network: **Stable Studionet 61999**. RPC `https://studio.genlayer.com/api`.
- Contract: [`0x7F5DdCEaFE6b3983fefD6160f68b95D430dbDb58`](https://explorer-studio.genlayer.com/address/0x7F5DdCEaFE6b3983fefD6160f68b95D430dbDb58).
- Deployment transaction: [`0x69cd834feaa602b18f4c339259f96f88f2a1323dc9da9b580c234f5ed3f51848`](https://explorer-studio.genlayer.com/tx/0x69cd834feaa602b18f4c339259f96f88f2a1323dc9da9b580c234f5ed3f51848).
- Source SHA-256: `514692ab30645017c18a17c59571e28ac0aaedb3a2eece5f36c8ce874f3e3a51`.

## Run

```sh
npm ci
npm test
npm run verify
node scripts/call.mjs read get_protocol '[]'
```

Node.js 22+ and Python 3.12+ are recommended. JavaScript dependencies are pinned `genlayer-js` and `viem`; no paid model API key, database or frontend is needed. GenLayer supplies the actual consensus boundary.

- [Readable contract](contracts/contract.py)
- [Real GenVM schema](schema.json) · [Deployment metadata](deployment.json)
- [Example domain and instructions](examples/changes.json)
- [Semantics, API and guarantees](PROTOCOL.md)
- [Deployment and actual calls](DEPLOYMENT.md)
- [Real transaction journal](evidence/live.json)

## Recorded transaction evidence

11 local mocked-host unit tests passed. The stored real Studionet journal contains 11 FINALIZED/SUCCESS transactions and 2 FINALIZED expected contract rejections, with 1 submitted transaction still awaiting a terminal observation. The deployment was observed FINALIZED/SUCCESS and deployed source bytes matched the recorded SHA-256. **The full live acceptance run is not complete; this evidence is not a completed acceptance claim.**

- Pending observation: `reject-dead-pair`, transaction `0x4b2296186f3758458f5f630093ebee6ef150221c08a039f06ae4622801ef2e16`.

`node scripts/check-journal.mjs` validates the integrity and identity of stored receipts offline; it is not a fresh chain read. `npm run live` resumes the original journal and signers without re-submitting recorded hashes. `npm run verify` deliberately refuses an incomplete journal; after completion it independently re-fetches receipts and final state and writes `evidence/verification.json`. Local CI validates source tests and stored-record integrity; neither substitutes for completed live acceptance.

## Scope and limits

This certifies finite state transformations, not arbitrary production deployments. A client can consume the committed configuration as an input to its own controlled deployment pipeline; PatchBraid never executes that external action. Any external consumer must separately ensure its actual semantics and bounds match the contract. Cross-space changes, external side effects, concurrent server state and noninteger values are outside the certificate.

Instructions and domains are signed public declarations, not statements about an independently observed live server. No external current-fact feed is relevant to the calculation. Do not enter secrets or confidential configuration values. A wallet represents an authorized space owner, not an authenticated organization.

Each deployment stores at most 128 spaces. Each space has up to 16 immutable changes, 32 pair tickets and at most 256 legal states. A pair ticket is single-use, but the owner can deliberately analyze the same changes under a new reference to authorize another application. Replay protection does not forbid such an explicit new authorization. There is no administrator override for UNKNOWN or conflicting programs. Semantic consensus can fail, disagree or be mistaken; finite proofs do not convert unverified prose into real-world truth.

MIT. GenLayer identifies its respective project; this contract is independent.
