"""Automatic native XML execution using a restricted Event-B interpreter.
Model-to-C encoding and scheduling policy are explicitly configured.
"""
from pathlib import Path
from itertools import product
from collections import deque
import ctypes as ct
import xml.etree.ElementTree as ET
import json, re, subprocess, time, hashlib

ROOT=Path(__file__).resolve().parent
from eventb_runtime import Context, Machine
CONTEXT=Context(ROOT/'models/C_AutomotivePilot.buc')
M0=Machine(ROOT/'models/M0_AtomicCycle.bum',CONTEXT)
M1=Machine(ROOT/'models/M1_SampledCycle.bum',CONTEXT)
# This declaration is the model-to-C adapter, not controller behavior.
MODE_NAMES=('noMode','leftMode','rightMode','bothMode')
POS_NAMES=('pNeutral','pLeft','pRight')
INPUTS=list(product((0,1),(0,1),range(len(POS_NAMES))))
CORE_VARS=('active','on','remaining')
INITIAL_NATIVE=M0.initial()
def encode(state):
    return (MODE_NAMES.index(state['active']),int(state['on']),state['remaining'])
def native_core(core):
    return {'active':MODE_NAMES[core[0]],'on':bool(core[1]),'remaining':core[2]}
def native_input(inp):
    return {'e':bool(inp[0]),'h':bool(inp[1]),'p':POS_NAMES[inp[2]]}
def published(state): return (state['blinkLeft'],state['blinkRight'])
INITIAL=encode(INITIAL_NATIVE)
NATIVE_STATES={INITIAL:INITIAL_NATIVE}
TRANSITIONS={}
def step(old,inp):
    key=(tuple(old),tuple(inp))
    if key not in TRANSITIONS:
        before=NATIVE_STATES[tuple(old)]
        new=M0.execute(before,'Cycle',native_input(inp))
        failures=M0.check(new)
        if failures: raise ValueError(('M0 invariant failures',failures))
        core=encode(new); NATIVE_STATES.setdefault(core,new)
        TRANSITIONS[key]=(core,published(new))
    return TRANSITIONS[key][0]
def lamps(state): return published(NATIVE_STATES[tuple(state)])

class Controller(ct.Structure):
    _fields_=[(x,ct.c_int) for x in ('mode','on','count','left','right','engine','hazard','direction',
        'sampled_engine','sampled_hazard','sampled_direction',
        'next_mode','next_on','next_count','next_left','next_right','stage')]

def schedules(inp):
    e,h,p=inp
    return [('stable',inp,inp),
            ('after_sample',(1-e,1-h,(p+1)%3),inp),
            ('both_gaps',(1-e,1-h,(p+1)%3),(1-e,1-h,(p+2)%3))]

def main():
    t=time.perf_counter()
    subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
                    str(ROOT/'controller.c'),'-o',str(ROOT/'controller.so')],check=True)
    lib=ct.CDLL(str(ROOT/'controller.so'))
    lib.reset.argtypes=[ct.POINTER(Controller)]
    lib.reset.restype=None
    lib.assign_inputs.argtypes=[ct.POINTER(Controller)]+[ct.c_int]*3
    lib.assign_inputs.restype=None
    lib.sample.argtypes=[ct.POINTER(Controller)]
    lib.sample.restype=None
    for name in ('decide','emit'):
        fn=getattr(lib,name)
        fn.argtypes=[ct.POINTER(Controller),ct.c_int]
        fn.restype=None
    paths={INITIAL:[]};queue=deque([INITIAL]);edges=[]
    while queue:
        old=queue.popleft()
        for inp in INPUTS:
            new=step(old,inp);edges.append((old,inp,new))
            if new not in paths:paths[new]=paths[old]+[inp];queue.append(new)
    cases=[]
    for index,(old,inp,new) in enumerate(edges):
        for profile,noise1,noise2 in schedules(inp):
            # Ten suffix cycles expose hidden countdown faults at lamp outputs.
            sequence=paths[old]+[inp]+[inp]*10
            oracle=[];state=INITIAL
            for sample in sequence:state=step(state,sample);oracle.append(lamps(state))
            cases.append({'id':f'T{index:03}_{profile}','target_source':old,
                          'target_input':inp,'target_destination':new,
                          'target_cycle':len(paths[old]),'inputs':sequence,
                          'noise_after_sample':noise1,'noise_after_decide':noise2,
                          'expected_outputs':oracle})
    (ROOT/'generated_tests.json').write_text(json.dumps(cases,separators=(',',':')))
    bug_names=['reference','short_phase_4','long_phase_6','direction_over_hazard',
               'engine_blocks_hazard','reset_on_mode_change','read_live_at_decide',
               'read_live_at_emit','publish_at_decide','swap_lamps',
               'use_previous_mode_for_output','ignore_hazard','hazard_right_dark']
    def check(sut,expected,k,stage,inp=None,a=None,b=None):
        actual=(sut.left,sut.right)
        if actual!=tuple(expected):
            return {'cycle':k,'observation_stage':stage,'sample':inp,
                    'after_sample':a,'after_decide':b,'expected':expected,
                    'actual':actual,'early_output':stage not in ('after_emit','after_reset')}
        return None
    def run_cycle(sut,inp,a,b,previous,expected,bug,k):
        operations=(
            ('after_input_before_sample',lambda:lib.assign_inputs(ct.byref(sut),*inp),previous),
            ('after_sample',lambda:lib.sample(ct.byref(sut)),previous),
            ('after_input_before_decide',lambda:lib.assign_inputs(ct.byref(sut),*a),previous),
            ('after_decide',lambda:lib.decide(ct.byref(sut),bug),previous),
            ('after_input_before_emit',lambda:lib.assign_inputs(ct.byref(sut),*b),previous),
            ('after_emit',lambda:lib.emit(ct.byref(sut),bug),expected))
        for stage,operation,wanted in operations:
            operation()
            mismatch=check(sut,wanted,k,stage,inp,a,b)
            if mismatch:return mismatch
        return None
    def execute(case,bug):
        sut=Controller();lib.reset(ct.byref(sut))
        previous=lamps(INITIAL)
        mismatch=check(sut,previous,-1,'after_reset')
        if mismatch:return mismatch
        for k,(inp,expected) in enumerate(zip(case['inputs'],case['expected_outputs'])):
            a,b=(case['noise_after_sample'],case['noise_after_decide']) if k==case['target_cycle'] else (inp,inp)
            mismatch=run_cycle(sut,inp,a,b,previous,expected,bug,k)
            if mismatch:return mismatch
            previous=expected
        return None
    outcomes=[];witnesses=[]
    for bug,name in enumerate(bug_names):
        fails=0;first=None;profiles={p:0 for p in ('stable','after_sample','both_gaps')}
        for case in cases:
            mismatch=execute(case,bug)
            if mismatch:
                fails+=1
                profile=case['id'].split('_',1)[1];profiles[profile]+=1
                if first is None:first={'mutant':name,'test_id':case['id'],
                                       'test':case,'mismatch':mismatch}
        outcomes.append({'mutant':name,'failed_tests':fails,'total_tests':len(cases),
                         'failed_tests_by_profile':profiles})
        if first:witnesses.append(first)
    assert outcomes[0]['failed_tests']==0,outcomes[0]
    # Baseline only: all 12 x 12 noise pairs for every reachable core edge.
    exhaustive_count=0;exhaustive_fail=0
    for old,inp,new in edges:
        for a,b in product(INPUTS,repeat=2):
            sut=Controller();lib.reset(ct.byref(sut))
            state=INITIAL;previous=lamps(state)
            mismatch=check(sut,previous,-1,'after_reset')
            for k,access in enumerate(paths[old]):
                state=step(state,access);expected=lamps(state)
                mismatch=mismatch or run_cycle(sut,access,access,access,previous,expected,0,k)
                previous=expected
            mismatch=mismatch or run_cycle(sut,inp,a,b,previous,lamps(new),0,len(paths[old]))
            exhaustive_count+=1
            exhaustive_fail+=bool(mismatch)
    assert exhaustive_fail==0
    killed=sum(x['failed_tests']>0 for x in outcomes[1:])
    result={'oracle':'Context axioms and M0 guards/actions interpreted directly from native Rodin XML',
            'sut':'Independent procedural C research pilot, compiled with gcc',
            'observable_oracle':'Initial output and outputs after every input assignment, Sample, Decide, and Emit',
            'reachable_core_states':len(paths),'core_transition_targets':len(edges),
            'core_transition_target_coverage':len({(tuple(c['target_source']),tuple(c['target_input'])) for c in cases})/len(edges),'schedule_profiles':3,
            'generated_tests':len(cases),'suite_cycle_steps':sum(len(c['inputs']) for c in cases),
            'reference_failures':outcomes[0]['failed_tests'],
            'exhaustive_target_schedule_runs':exhaustive_count,'exhaustive_reference_failures':exhaustive_fail,
            'mutants':len(outcomes)-1,'killed_mutants':killed,'mutation_score':killed/(len(outcomes)-1),
            'stable_only_killed_mutants':sum(x['failed_tests_by_profile']['stable']>0 for x in outcomes[1:]),
            'mutant_results':outcomes[1:],'elapsed_seconds':round(time.perf_counter()-t,3),
            'scope':'Restricted direct XML interpreter; finite projection; configured model-to-C mapping; no general interpreter correctness proof',
            'rodin_proof_status':{'closed':67,'total':89,'pending':22},
            'rodin_proof_status_source':'Previously recorded Rodin analysis; not rerun by this script'}
    (ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'counterexamples.json').write_text(json.dumps(witnesses,indent=2)+'\n')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'models').iterdir()}
    (ROOT/'model_hashes.json').write_text(json.dumps(hashes,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
