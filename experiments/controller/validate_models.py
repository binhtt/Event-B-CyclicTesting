"""Bounded execution checks, not refinement proofs or ProB model checking."""
import json
import hashlib
from itertools import product
from collections import deque
from pathlib import Path
import run_experiment as run

ROOT=Path(__file__).resolve().parent

def validate():
    m0,m1=run.M0,run.M1
    initial=m1.initial()
    assert not m0.check(run.INITIAL_NATIVE)
    assert not m1.check(initial)
    representatives={run.INITIAL:initial}; queue=deque([run.INITIAL]); edges=[]
    while queue:
        old=queue.popleft(); before=representatives[old]
        for inp in run.INPUTS:
            current=m1.execute(before,'Environment',run.native_input(inp))
            sampled=m1.execute(current,'Sample')
            decided=m1.execute(sampled,'Decide')
            emitted=m1.execute(decided,'Emit')
            abstract=m0.execute({k:before[k] for k in m0.variables},'Cycle',run.native_input(inp))
            assert all(emitted[k]==abstract[k] for k in m0.variables if not k.startswith('env'))
            assert run.published(sampled)==run.published(before)==run.published(decided)
            for state in (current,sampled,decided,emitted): assert not m1.check(state)
            new=run.encode(emitted); edges.append((old,inp,new))
            if new not in representatives: representatives[new]=emitted; queue.append(new)
    runs=0; checked=0
    # All valid input pairs at the two gaps, for every projected transition.
    checked_states=set()
    def check(state):
        nonlocal checked
        key=tuple(state[k] for k in m1.variables)
        if key not in checked_states:
            assert not m1.check(state)
            checked_states.add(key); checked+=1
    for old,inp,new in edges:
        before=representatives[old]
        sampled=m1.execute(m1.execute(before,'Environment',run.native_input(inp)),'Sample')
        expected=run.TRANSITIONS.get((old,inp))
        if expected is None: run.step(old,inp); expected=run.TRANSITIONS[old,inp]
        for a,b in product(run.INPUTS,repeat=2):
            updated=m1.execute(sampled,'Environment',run.native_input(a))
            decided=m1.execute(updated,'Decide')
            changed=m1.execute(decided,'Environment',run.native_input(b))
            emitted=m1.execute(changed,'Emit')
            for state in (sampled,updated,decided,changed,emitted): check(state)
            assert all(run.published(state)==run.published(before) for state in (sampled,updated,decided,changed))
            assert (run.encode(emitted),run.published(emitted))==expected
            runs+=1
    # Replay every generated test through M1, including continuation cycles.
    cases=json.loads((ROOT/'generated_tests.json').read_text()); cycles=0
    for case in cases:
        state=m1.initial()
        for k,(inp,y) in enumerate(zip(case['inputs'],case['expected_outputs'])):
            a,b=(case['noise_after_sample'],case['noise_after_decide']) if k==case['target_cycle'] else (inp,inp)
            previous=run.published(state)
            for event,args in [('Environment',run.native_input(inp)),('Sample',None),
                               ('Environment',run.native_input(a)),('Decide',None),
                               ('Environment',run.native_input(b)),('Emit',None)]:
                state=m1.execute(state,event,args); check(state)
                assert run.published(state)==(tuple(y) if event=='Emit' else previous)
            cycles+=1
    result={'method':'Direct XML subset interpreter; no manually coded Cycle branches',
            'reachable_projected_states':len(representatives),'transition_targets':len(edges),
            'abstract_refined_stable_agreement':len(edges),
            'all_gap_schedule_runs':runs,'schedule_contract_failures':0,
            'unique_refined_states_invariant_checked':checked,
            'test_replays':len(cases),'replay_cycles':cycles,'replay_failures':0,
            'model_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'models').glob('*.bu?'))},
            'limits':'Representative core states and designated schedules; not full event graph exploration, a refinement proof, or independent validation of interpreter semantics'}
    (ROOT/'model_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': validate()
