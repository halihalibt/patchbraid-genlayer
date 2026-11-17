# PatchBraid semantics and API

## Domain and program language

Dimensions are ordered `{key,description,min,max}` records. There are 1–4 distinct keys, each width at most eight, with at most 256 combined states. Bounds range between -100 and 107 under the width rule. State vectors follow dimension order.

A compiled operation has exactly `{op,target,value,source}`:

| op | Meaning | Fields |
|---|---|---|
| SET | Assign a literal integer | target key, value, source="" |
| ADD | Add a signed integer to current target | target key, value, source="" |
| COPY | Copy current source into target | target key, source key, value=0 |

A program has 1–4 sequential operations. Integer literals are bounded to ±1,000,000. After each step the target must remain in its declared inclusive bounds; otherwise the entire program rejects with no partial update. Intermediate out-of-domain values are not allowed even if a later step would restore them. COPY observes changes made by preceding steps. All rejection causes are one observable REJECT outcome for equivalence; failed intermediate state is not observable.

`UNKNOWN` carries an empty program. Conditions, loops, multiplication, unspecified amounts/order and unresolved variable references are unsupported rather than guessed. Explicit out-of-range assignments can be KNOWN programs that reject on all inputs.

## Independent consensus

The leader uses `gl.nondet.exec_prompt` inside `gl.vm.run_nondet_unsafe` and returns status, program and a contiguous instruction quote. Each validator independently derives another program without the leader's answer. It compares `program_signature`: UNKNOWN status, or the output/REJECT result on **every** legal state. Then it independently audits the candidate program and quote against the complete original instruction and fixed language rules. Invalid schema, forged quotes, unsupported operations or any behavioral mismatch reject validation. Input commands cannot instruct validators to manufacture agreement.

Equivalent syntax is allowed; equal behavior at only the current state is insufficient. This proof remains bounded to the declared domain and trusted accepted interpretation. It is not a global theorem about unbounded arithmetic or external systems.

## Pair proof

For every state, `analyze` computes atomic `A;B` and `B;A`:

- TOTAL_COMMUTE: both succeed with identical outputs everywhere.
- PARTIAL_COMMUTE: the success domains coincide, outputs match wherever successful, and at least one state succeeds while some reject.
- CONFLICT: at least one starting state differs in definedness or final value. `witness` gives the first such input and both outcomes (`null` is atomic REJECT).
- NO_COMMON_SUCCESS: both orders reject everywhere. Equal rejection alone is not permission to execute.

`states_checked`, `common_successes`, `witness` and `table_hash` are deterministic outputs. `table_hash` covers the complete ordered input/ab/ba table. A pair binding covers the space ID, domain hash, immutable first/second change records and full proof. The domain hash covers space ID, owner and dimensions. Change input hashes bind dimensions and exact instruction; behavior hashes bind normalized full-domain output vectors.

Execution is owner-only, bound to the current **space revision** and exact pair binding. Only TOTAL/PARTIAL pairs qualify; the chosen order must still succeed at the current configuration. Success marks that pair consumed and appends one before/after event. Rejected calls change neither current state, revision nor consumption. The owner can explicitly create a different pair reference for another application; tickets prevent accidental replay, not deliberate reauthorization.

## API

| Write | Positional arguments |
|---|---|
| create_space | reference, domain, initial |
| register_change | sid, expected_revision, reference, instruction |
| analyze_pair | sid, expected_revision, reference, first, second |
| execute_pair | sid, expected_revision, reference, binding, reverse |

All post-creation writes require the actual owner signature. Domain and initial are JSON strings. Domain is an array of dimension records; initial is an integer array in dimension order. Instruction is 5–1000 characters. References and variable keys use lowercase `[a-z0-9-]{3,40}`. `first` and `second` are distinct change references already in that space; `reverse` is a boolean selecting B;A instead of A;B. Duplicate JSON keys, numeric booleans, floats, reused references and stale revisions are rejected.

Views: `get_protocol()`, `list_spaces()`, `get_space(sid)`, all JSON strings. The space contains dimensions, initial/current state, immutable changes, pair proofs, consumption flags and executions. It is not an EVM storage ABI; use the supplied GenLayer method schema and SDK.

```sh
node scripts/call.mjs read get_space '["SPACE_ID"]'
```

For actual writes use `scripts/call.mjs write` with the exact array from `schema.json`, your securely provisioned authorized `CONTRACT_PRIVATE_KEY` and zero attached value. Require FINALIZED + SUCCESS and inspect latest-final state, not only the transaction return.

## Validation coverage

Local tests check concrete total/partial/conflict/dead pairs, COPY observation order, atomic failure, syntactically distinct equivalent programs, all 400 pairs of selected literal/add single-operation programs against an independently implemented transformer, real state-boundary refusal, replay/owner/binding/revision checks and substantive validator disagreement/auditing. These are mock-host tests. Actual deployment, semantic compilations, pair analyses, authorized executions and expected failures are separately recorded and independently re-fetched on Stable Studionet.

## GenLayer references

- [Equivalence Principle and substantive independent validators](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle)
- [Stable network configuration](https://docs.genlayer.com/developers/intelligent-contracts/deploying/network-configuration)
