# Reproducibility

## Controller

Run `python3 experiments/controller/run_all.py` from the repository root. It runs interpreter checks, test generation/C execution and M1 validation. Inputs are [engine,hazard,direction] with Boolean 0/1 and neutral/left/right = 0/1/2; outputs are [left,right] with 0/100 levels. Core is [mode,on,remaining], modes none/left/right/both = 0/1/2/3. Tests use three profiles and ten continuation cycles. Compare numerical counts rather than elapsed time.

Native Rodin XML is the behavioral source. eventb_runtime.py evaluates the supported finite subset, using pre-state RHS evaluation for simultaneous assignment. Model-to-C identifiers/encodings and stage-scheduling policies remain explicit configuration.

## Rodin

See RODIN_REVIEW.md. Import the complete AutomotivePilot project folder or its ZIP into Rodin 3.9. Saved proof evidence is 67/89, not a fully proved development. Exact pending obligations are in results/formal/proof_obligations.csv. Model hashes match all runner copies. Rodin GUI import/proof replay was not rerun in packaging.

## External

Run `python3 experiments/external/experiment.py`. First execution downloads and verifies pinned archives. Seed is 20261002 plus zero-based model position in the eight-pair list. Original C is instrumented for reset/output capture. Tests stop on first error; mutant evaluation stops at first killing test. Potentially equivalent mutants are not excluded. C99 uses -O0 -fwrapv.

## Provenance

New direct-XML evidence: results/controller-directxml. Earlier controller evidence: results/controller. External and formal results are separately recorded; no new Rodin/ProB/external run is claimed here. ProB scripts remain optional historical tooling. Linux/Python 3.12.14/GCC 13.3.0 are the recorded testing environment. Verify SHA256SUMS.json before rerunning commands that regenerate files.
