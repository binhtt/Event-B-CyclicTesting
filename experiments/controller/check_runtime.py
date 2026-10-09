"""Focused checks of interpreter behavior and model-driven changes."""
import json
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from eventb_runtime import Context, Machine, UnsupportedModel, parse

ROOT=Path(__file__).resolve().parent

class RuntimeChecks(unittest.TestCase):
    def setUp(self):
        self.context=Context(ROOT/'models/C_AutomotivePilot.buc')
    def test_simultaneous_assignments(self):
        xml='''<org.eventb.core.machineFile>
        <org.eventb.core.variable org.eventb.core.identifier="x"/>
        <org.eventb.core.variable org.eventb.core.identifier="y"/>
        <org.eventb.core.event org.eventb.core.label="Swap">
        <org.eventb.core.action org.eventb.core.assignment="x ≔ y"/>
        <org.eventb.core.action org.eventb.core.assignment="y ≔ x"/>
        </org.eventb.core.event></org.eventb.core.machineFile>'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'Swap.bum';p.write_text(xml)
            self.assertEqual(Machine(p,self.context).execute({'x':1,'y':2},'Swap'),{'x':2,'y':1})
    def test_unsupported_syntax_rejected(self):
        with self.assertRaises(UnsupportedModel): parse('∀x·x ∈ BOOL')
    def test_machine_guard_changes_behavior_without_python_edit(self):
        original=Machine(ROOT/'models/M0_AtomicCycle.bum',self.context)
        tree=ET.parse(ROOT/'models/M0_AtomicCycle.bum')
        for event in tree.getroot().findall('org.eventb.core.event'):
            if event.get('org.eventb.core.label')=='Cycle':
                for guard in event.findall('org.eventb.core.guard'):
                    text=guard.get('org.eventb.core.predicate')
                    guard.set('org.eventb.core.predicate',text.replace('r = ticks − 1','r = ticks − 2'))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'Changed.bum';tree.write(p,encoding='utf-8')
            changed=Machine(p,self.context)
            args={'e':True,'h':False,'p':'pLeft'}
            self.assertEqual(original.execute(original.initial(),'Cycle',args)['remaining'],4)
            self.assertEqual(changed.execute(changed.initial(),'Cycle',args)['remaining'],3)
    def test_disabled_stage_rejected(self):
        m=Machine(ROOT/'models/M1_SampledCycle.bum',self.context)
        with self.assertRaises(UnsupportedModel): m.execute(m.initial(),'Emit')
    def test_invalid_parameter_rejected(self):
        m=Machine(ROOT/'models/M0_AtomicCycle.bum',self.context)
        with self.assertRaises(UnsupportedModel):
            m.execute(m.initial(),'Cycle',{'e':False,'h':False,'p':'unsupported'})

if __name__=='__main__': unittest.main()
