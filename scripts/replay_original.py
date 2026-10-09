"""Replay excluded-pair witnesses on hash-checked, uninstrumented transition code.
Replace only main with a bounded input loop; compile with UBSan.
"""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--source-directory', type=Path, default=ROOT/'experiments/external')
a = p.parse_args()
manifest = json.loads((ROOT/'experiments/external/sources.json').read_text())
reports = json.loads((ROOT/'results/external/results.json').read_text())
results = []
for model in reports:
    if model['reference_failed_tests'] == 0:
        continue
    name = model['benchmark']
    records = [f for f in manifest['files'] if f['model'] == name and f['file'].endswith('.c')]
    if len(records) != 1:
        raise ValueError('Expected one original C source for '+name)
    record = records[0]
    path = a.source_directory/record['file']
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('Source hash mismatch: '+str(path))
    # Use the witness through its first failing step, not the unused suffix.
    witness = model['reference_first_failure'][0]
    sequence = witness['inputs'][:witness['step']+1]
    symbols = witness['expected_symbols'][:witness['step']+1]
    import re
    versions = [f for f in manifest['files'] if f['model']==name and f['file'].endswith('version.txt')]
    vf = a.source_directory/versions[0]['file']
    vd = vf.read_bytes()
    if hashlib.sha256(vd).hexdigest() != versions[0]['sha256']:
        raise ValueError('Mapping hash mismatch: '+str(vf))
    mapping = {x:int(y) for x,y in re.findall(r'^(\S+)\s+(\d+)\s*$', vd.decode(), re.M)}
    codes = [mapping[x] for x in sequence]
    expected = [mapping[x] for x in symbols]
    source = data.decode().split('int main()',1)[0]
    source += '\nint main(void){int trace[]={' + ','.join(map(str,codes)) + '};'
    source += 'for(unsigned i=0;i<sizeof(trace)/sizeof(trace[0]);++i)calculate_output(trace[i]);return 0;}\n'
    with tempfile.TemporaryDirectory(prefix='rers-replay-') as tmp:
        c = Path(tmp)/'replay.c';exe = Path(tmp)/'replay';c.write_text(source)
        flags = ['-std=c99','-O0','-fwrapv','-fsanitize=undefined','-fno-sanitize-recover=undefined']
        subprocess.run(['gcc',*flags,str(c),'-o',str(exe)],check=True,capture_output=True,text=True)
        proc = subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
    results.append({'benchmark':name,'source_sha256':record['sha256'],'input_codes':codes,
                    'expected_codes':expected,'compiler_flags':flags,'exit_code':proc.returncode,
                    'stdout':proc.stdout,'stderr':proc.stderr})
    if 'Invalid input:' not in proc.stderr:
        raise RuntimeError('Expected invalid-input report not reproduced for '+name)
out=ROOT/'experiments/external/replay_results.json'
out.write_text(json.dumps(results,indent=2)+'\n')
print('PASS: invalid-input reports reproduced for all six excluded pairs; results at '+str(out))
