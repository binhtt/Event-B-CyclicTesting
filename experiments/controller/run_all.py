"""One command: runtime checks, XML-derived generation, SUT tests, M1 replay."""
from pathlib import Path
import subprocess
import sys
import json

root=Path(__file__).resolve().parent
for script in ('check_runtime.py','run_experiment.py','validate_models.py'):
    subprocess.run([sys.executable,str(root/script)],check=True)
current=json.loads((root/'results.json').read_text())
baseline_path=root/'recorded_baseline.json'
if baseline_path.exists():
    baseline=json.loads(baseline_path.read_text())
    fields=('reachable_core_states','core_transition_targets','generated_tests',
            'suite_cycle_steps','reference_failures','killed_mutants',
            'stable_only_killed_mutants','mutant_results')
    matches={key:current[key]==baseline[key] for key in fields}
    (root/'baseline_comparison.json').write_text(json.dumps(matches,indent=2)+'\n')
    if not all(matches.values()): raise SystemExit('Results differ from recorded baseline; inspect before revising paper')
