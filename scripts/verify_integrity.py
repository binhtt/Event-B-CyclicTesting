"""Verify every file listed in the packaged SHA-256 manifest."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'SHA256SUMS.json').read_text())
errors=[]
for name,expected in manifest.items():
    p=root/name
    if not p.is_file():errors.append(name+': missing')
    elif hashlib.sha256(p.read_bytes()).hexdigest()!=expected:errors.append(name+': changed')
if errors:raise SystemExit('\n'.join(errors))
print('PASS: all '+str(len(manifest))+' packaged file hashes match.')
