# Inspecting the saved Rodin project

Use Rodin 3.9. Create a fresh workspace to avoid an existing AutomotivePilot name collision.

1. File > Import > General > Existing Projects into Workspace.
2. Select the repository's `models` directory as root; select `AutomotivePilot`.
3. Enable Copy projects into workspace, then Finish.
4. Open C_AutomotivePilot, M0_AtomicCycle and M1_SampledCycle.
5. Open the Event-B proving perspective; select individual proof obligations to inspect saved proofs or attempt interactive proving.

Alternatively import `models/AutomotivePilot-Rodin.zip` using Select archive file in the same import wizard.

The project contains its descriptor/settings, native context/machines (.buc/.bum), checked components (.bcc/.bcm), obligations (.bpo), saved proof trees (.bpr), and proof status (.bps). It is not merely a collection of source files.

Saved status: M0 25/32; M1 42/57; total 67/89, with 22 pending. See `results/formal/proof_obligations.csv` and `saved_proof_status.json` for exact names. The saved_manual_flag is Rodin metadata, not evidence of new interactive proof work in this packaging run. Rebuilding/replaying may change status with installed prover versions. No pending obligation is claimed proved.

`docs/EVENTB_MODEL.md` is a human-readable rendering of source XML, not an alternate executable model. Native model hashes match the test runner's model copies.

GUI import and proof replay have not been rerun during packaging. The project metadata and XML have been checked; the saved formal evidence is historical.
