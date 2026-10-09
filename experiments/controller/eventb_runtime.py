"""Finite interpreter for the explicit Rodin XML subset used by this pilot.

No controller transition branches are encoded here. Unsupported syntax fails
closed. This is not Rodin, ProB, or a general Event-B semantic implementation.
"""
import re
import itertools
import xml.etree.ElementTree as ET
from pathlib import Path

P = 'org.eventb.core.'

class UnsupportedModel(ValueError):
    pass

def attr(e, name):
    return e.get(P + name)

def children(e, name):
    return e.findall(P + name)

class Parser:
    precedence = {'⇒':1, '∨':2, '∧':3, '=':4, '≠':4, '∈':4,
                  '>':4, '<':4, '≥':4, '≤':4, '→':5, '×':6,
                  '↦':7, '‥':8, '+':9, '−':9, '∗':10}
    def __init__(self, text):
        self.tokens = re.findall(r'[A-Za-z_][A-Za-z_0-9]*|ℕ1|ℕ|\d+|[(){} ,⇒∨∧=≠∈><≥≤→×↦‥+−∗]', text)
        self.tokens = [x for x in self.tokens if not x.isspace()]
        if ''.join(self.tokens) != re.sub(r'\s+', '', text):
            raise UnsupportedModel('Unsupported tokens: ' + text)
        self.i = 0
    def take(self):
        if self.i >= len(self.tokens): raise UnsupportedModel('Unexpected end')
        t = self.tokens[self.i]; self.i += 1; return t
    def expect(self, token):
        if self.take() != token: raise UnsupportedModel('Expected ' + token)
    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None
    def expression(self, minimum=0):
        t = self.take()
        if t == '(':
            left = self.expression(); self.expect(')')
        elif t == '{':
            items = []
            if self.peek() != '}':
                while True:
                    items.append(self.expression())
                    if self.peek() != ',': break
                    self.take()
            self.expect('}'); left = ('set', tuple(items))
        elif t.isdigit(): left = ('int', int(t))
        elif re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*|ℕ1|ℕ', t):
            left = ('id', t)
        else: raise UnsupportedModel('Unsupported expression: ' + t)
        while True:
            op = self.peek()
            if op == '(':
                self.take(); args=[]
                if self.peek() != ')':
                    while True:
                        args.append(self.expression())
                        if self.peek() != ',': break
                        self.take()
                self.expect(')'); left = ('call', left, tuple(args)); continue
            prec = self.precedence.get(op, -1)
            if prec < minimum: break
            self.take()
            right = self.expression(prec if op == '⇒' else prec + 1)
            left = ('op', op, left, right)
        return left

def parse(text):
    p=Parser(text); node=p.expression()
    if p.peek() is not None: raise UnsupportedModel('Trailing syntax: '+text)
    return node

def evaluate(n, env):
    kind=n[0]
    if kind == 'id': return env[n[1]]
    if kind == 'int': return n[1]
    if kind == 'set': return frozenset(evaluate(v,env) for v in n[1])
    if kind == 'call':
        name=n[1][1] if n[1][0]=='id' else None
        args=[evaluate(a,env) for a in n[2]]
        if name=='bool': return bool(args[0])
        if name=='partition':
            whole,*parts=args
            return frozenset().union(*parts)==whole and sum(map(len,parts))==len(whole)
        relation=evaluate(n[1],env)
        found=[v for k,v in relation if k==args[0]]
        if len(found)!=1: raise UnsupportedModel('Not a total single-valued function')
        return found[0]
    op=n[1]; a=evaluate(n[2],env)
    if op=='∧': return bool(a) and bool(evaluate(n[3],env))
    if op=='∨': return bool(a) or bool(evaluate(n[3],env))
    if op=='⇒': return not bool(a) or bool(evaluate(n[3],env))
    b=evaluate(n[3],env)
    if op=='=': return a==b
    if op=='≠': return a!=b
    if op=='∈':
        if isinstance(b,tuple) and b[0]=='function_type':
            dom,codom=b[1:]
            return (isinstance(a,frozenset) and all(k in dom and v in codom for k,v in a)
                    and {k for k,v in a}==set(dom) and len(a)==len(dom))
        if b=='NAT': return type(a)==int and a>=0
        if b=='NAT1': return type(a)==int and a>=1
        return a in b
    if op=='>': return a>b
    if op=='<': return a<b
    if op=='≥': return a>=b
    if op=='≤': return a<=b
    if op=='↦': return (a,b)
    if op=='×': return frozenset(itertools.product(a,b))
    if op=='→': return ('function_type',a,b)
    if op=='‥': return frozenset(range(a,b+1))
    if op=='+': return a+b
    if op=='−': return a-b
    if op=='∗': return a*b
    raise UnsupportedModel(op)

def identifiers(n):
    if n[0]=='id': return {n[1]}
    if n[0]=='int': return set()
    if n[0]=='set': return set().union(*(identifiers(x) for x in n[1]))
    if n[0]=='call': return identifiers(n[1]) | set().union(*(identifiers(x) for x in n[2]))
    return identifiers(n[2]) | identifiers(n[3])

class Context:
    def __init__(self, path):
        root=ET.parse(path).getroot()
        self.env={'FALSE':False,'TRUE':True,'BOOL':frozenset((False,True)),
                  'ℕ':'NAT','ℕ1':'NAT1'}
        self.axioms=[(attr(a,'label'),parse(attr(a,'predicate'))) for a in children(root,'axiom')]
        # Enumerated carrier sets must have explicit singleton partitions.
        for label,n in self.axioms:
            if n[0]=='call' and n[1]==('id','partition'):
                domain=n[2][0][1]; values=[]
                for singleton in n[2][1:]:
                    if singleton[0]!='set' or len(singleton[1])!=1 or singleton[1][0][0]!='id':
                        raise UnsupportedModel('Only singleton carrier partitions supported')
                    name=singleton[1][0][1]; self.env[name]=name; values.append(name)
                self.env[domain]=frozenset(values)
        pending={attr(e,'identifier') for e in children(root,'constant')}-self.env.keys()
        while pending:
            progress=False
            for label,n in self.axioms:
                # Numeric equalities may be one conjunct of a typing axiom.
                stack=[n]
                while stack:
                    a=stack.pop()
                    if a[:2]==('op','∧'): stack.extend(a[2:])
                    elif a[:2]==('op','=') and a[2][0]=='id' and a[2][1] in pending:
                        try: value=evaluate(a[3],self.env)
                        except KeyError: continue
                        name=a[2][1]; self.env[name]=value; pending.remove(name); progress=True
            if not progress: raise UnsupportedModel('Cannot resolve constants: '+str(pending))
        for label,n in self.axioms:
            if not evaluate(n,self.env): raise UnsupportedModel('False context axiom: '+label)

class Machine:
    def __init__(self, path, context):
        root=ET.parse(path).getroot(); self.context=context; self.events={}; self.cache={}
        self.variables=[attr(e,'identifier') for e in children(root,'variable')]
        self.invariants=[(attr(e,'label'),parse(attr(e,'predicate'))) for e in children(root,'invariant')]
        for e in children(root,'event'):
            if attr(e,'extended')=='true': raise UnsupportedModel('Extended events not supported')
            name=attr(e,'label'); guards=[parse(attr(g,'predicate')) for g in children(e,'guard')]
            actions=[]
            for a in children(e,'action'):
                text=attr(a,'assignment')
                if text.count('≔')!=1: raise UnsupportedModel('Only deterministic assignments supported')
                lhs,rhs=text.split('≔'); lhs=lhs.strip()
                if lhs not in self.variables: raise UnsupportedModel('Invalid assignment target')
                actions.append((lhs,parse(rhs)))
            if len({v for v,n in actions})!=len(actions): raise UnsupportedModel('Duplicate assignment')
            params=[attr(p,'identifier') for p in children(e,'parameter')]
            domains={g[2][1]:g[3] for g in guards if g[:2]==('op','∈') and g[2][0]=='id' and g[2][1] in params}
            if set(domains)!=set(params): raise UnsupportedModel('Every parameter requires a finite domain guard')
            refs=set().union(*(identifiers(n) for n in guards),*(identifiers(n) for v,n in actions))
            self.events[name]=(guards,actions,params,domains,sorted(refs & set(self.variables)))
    def successors(self, state, name, supplied=None):
        guards,actions,params,domains,refs=self.events[name]; supplied=supplied or {}
        if set(supplied)-set(params): raise UnsupportedModel('Unknown supplied parameter')
        key=(name,tuple((v,state[v]) for v in refs),tuple(sorted(supplied.items())))
        if key not in self.cache:
            env=self.context.env | state; free=[p for p in params if p not in supplied]
            choices=[sorted(evaluate(domains[p],env),key=str) for p in free]
            rows=[]
            for values in itertools.product(*choices):
                bindings=supplied | dict(zip(free,values)); pre=env | bindings
                if all(evaluate(g,pre) for g in guards):
                    # All RHS expressions use the pre-state: Event-B simultaneous assignment.
                    changes={v:evaluate(n,pre) for v,n in actions}
                    rows.append((changes,bindings))
            self.cache[key]=rows
        return [(state | changes,dict(bindings)) for changes,bindings in self.cache[key]]
    def execute(self, state, name, supplied=None):
        rows=self.successors(state,name,supplied)
        if len(rows)!=1: raise UnsupportedModel(f'{name}: expected exactly one successor, got {len(rows)}')
        return rows[0][0]
    def initial(self): return self.execute({},'INITIALISATION')
    def check(self,state):
        env=self.context.env | state
        return [label for label,n in self.invariants if not evaluate(n,env)]
