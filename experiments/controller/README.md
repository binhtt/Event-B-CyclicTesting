# Direct Event-B XML test-generation experiment

Run from the repository root:

```bash
python3 experiments/controller-native/run_all.py
```

For the standalone ZIP, run `python3 run_all.py` inside its extracted folder.

Requirements: Python 3.12 and GCC. Rodin and ProB are not required by this runner.

## Model input and execution

The input consists of the native Rodin context and both machines under `models/`.
The context's axioms supply finite carrier sets, constants, and function tables.
The interpreter parses M0's parameter domains, guards and assignment expressions,
enumerates enabled bindings, and evaluates all assignment right-hand sides against
the pre-state. The four response branches are **not** transcribed into Python.
INITIALISATION, Cycle, Environment, Sample, Decide and Emit are executed from XML.

The adapter declares the projection `(active,on,remaining)`, the C encodings of
MODE/POS, and the input/output interface. The generator retains the paper's BFS
access sequences, three schedule profiles and ten repeated continuation cycles.
These testing policies are configured; they are not inferred from the model.
The independent staged C controller is compiled and executed for every test and
each of its twelve deliberately injected faults.

`validate_models.py` executes both machines, compares abstract and staged responses
on 372 representative projected transitions, exercises all 144 valid pairs of
gap inputs for each target, and replays all generated tests through M1. It checks
all listed M1 invariants on distinct visited states. It does not explore every
possible event interleaving or independently validate the interpreter semantics.

## Supported subset

Explicit, non-extended events; finite typed parameters; deterministic single-variable
assignments; singleton partitions; explicit set/function tables; function application;
maplets, finite products/ranges, integer arithmetic, Boolean conversion, comparisons,
membership, conjunction/disjunction/implication and finite function typing.
Syntax outside this subset fails. Arbitrary Event-B models, quantifiers,
nondeterministic substitutions, extended-event inheritance, symbolic infinite domains,
and proof/refinement checking are not implemented. The evaluator is a research
prototype with no general semantic-correctness proof. ProB was unavailable for this
rerun; these results must not be described as a new ProB run.

## Recorded results

31 reachable core states; 372 targets; 1,116 tests; 18,216 reference cycles;
zero reference failures; all 12 fault variants detected; stable profile detects 10.
Fault-by-profile counts equal the previous manually encoded experiment.
M1 validation: 53,568 target/gap schedules; zero contract failures;
1,116 test replays / 18,216 cycles; zero replay failures.

`results.json`, `counterexamples.json`, `generated_tests.json`, `model_hashes.json`,
`model_validation.json` and `baseline_comparison.json` are regenerated.
The model hashes match the previously evaluated sources. The historical Rodin
status remains 67/89 (22 pending); this runner does not rerun or discharge proofs.
External Mealy benchmarks are unchanged and are not Event-B extraction evidence.

The new experiment is additive. Existing recorded results are retained separately.
