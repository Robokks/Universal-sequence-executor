#!/usr/bin/env python3
"""Conservative offline checks and graph-level simulation of the generated AIXML.
NOT a replacement for lvai_check_aixml, lvai_validate_aixml or LabVIEW execution.
"""
from __future__ import annotations
import json,hashlib,math,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
MAN=json.loads((ROOT/'manifest.json').read_text())
KNOWN={
 'Add':({'x','y'},{'x+y'}), 'Subtract':({'x','y'},{'x-y'}),
 'Multiply':({'x','y'},{'x*y'}), 'Divide':({'x','y'},{'x/y'}),
 'Less?':({'x','y'},{'x < y?'}), 'Greater?':({'x','y'},{'x > y?'}),
 'Greater Or Equal?':({'x','y'},{'x >= y?'}), 'Equal?':({'x','y'},{'x = y?'}),
 'Or':({'x','y'},{'x .or. y?'}), 'Select':({'t','s','f'},{r's? t\3Af'}),
 'In Range and Coerce':({'upper limit','x','lower limit'},{'In Range?','coerced(x)'})}

def mappings(s):
    return {i.split(':',1)[0]:i.split(':',1)[1] for i in s.split(',') if i}

def typed(s,t):
    if t=='bool':return s=='true'
    if t=='int32':return int(s)
    if t=='double':return float(s)
    return s

def check(xml, pane):
    r=ET.fromstring(xml)
    assert r.tag=='VI' and r.attrib.get('description') and r.attrib.get('_name')
    assert '<!--' not in xml
    uids=set(); producers={}; inputs=[]; connectors=[]
    for item in r:
        assert item.tag in ('Control','Constant','Node','Indicator'),item.tag
        u=item.attrib['uid'];assert u not in uids,(u,r.attrib['_name']);uids.add(u)
        assert item.attrib.get('uid_parent')=='root'
        if item.tag in ('Control','Indicator'):
            assert 'value' in item.attrib
            connectors.append(int(item.attrib['conIdx']))
        if item.tag=='Node':
            n=item.attrib['_name'];assert n in KNOWN,n
            ins=mappings(item.attrib['inputs']);outs=mappings(item.attrib['outputs'])
            assert set(ins)==KNOWN[n][0],(n,ins)
            assert set(outs)==KNOWN[n][1],(n,outs)
            if n=='In Range and Coerce': assert item.attrib.get('includeLow')=='true' and item.attrib.get('includeHigh')=='true'
        if item.tag in ('Control','Constant','Node'):
            for t,w in mappings(item.attrib['outputs']).items():
                if w: assert w not in producers,(w,r.attrib['_name']);producers[w]=(u,t)
        if item.tag in ('Indicator','Node'):
            inputs.extend([(item.tag,term,wire) for term,wire in mappings(item.attrib['inputs']).items() if wire])
    assert len(connectors)==len(set(connectors))
    assert len(uids)==len(r)
    for _,t,w in inputs: assert w in producers, (r.attrib['_name'],t,w)
    if pane=='4815':assert all(c in [11,10,9,8,3,2,1,0] for c in connectors)
    if pane=='4833':assert all(c in [0,5,7,9,4,6,8,10,15] for c in connectors)
    return r

def simulate(r,args):
    wires={};outputs={}
    for it in r:
        tag=it.tag
        if tag in ('Control','Constant'):
            v=(args[it.attrib['_name']] if tag=='Control' else typed(it.attrib['value'],it.attrib['type']))
            wires[mappings(it.attrib['outputs'])['value']]=v
        elif tag=='Node':
            pin={k:wires[w] for k,w in mappings(it.attrib['inputs']).items()}
            n=it.attrib['_name']
            if n=='Add':v={'x+y':pin['x']+pin['y']}
            elif n=='Subtract':v={'x-y':pin['x']-pin['y']}
            elif n=='Multiply':v={'x*y':pin['x']*pin['y']}
            elif n=='Divide':v={'x/y':pin['x']/pin['y']}
            elif n=='Greater?':v={'x > y?':pin['x']>pin['y']}
            elif n=='Greater Or Equal?':v={'x >= y?':pin['x']>=pin['y']}
            elif n=='Less?':v={'x < y?':pin['x']<pin['y']}
            elif n=='Equal?':v={'x = y?':pin['x']==pin['y']}
            elif n=='Or':v={'x .or. y?':pin['x'] or pin['y']}
            elif n=='Select':v={r's? t\3Af':pin['t'] if pin['s'] else pin['f']}
            elif n=='In Range and Coerce':
                x,low,high=pin['x'],pin['lower limit'],pin['upper limit']
                v={'coerced(x)':min(max(x,low),high),'In Range?':low<=x<=high}
            else:raise AssertionError(n)
            for t,w in mappings(it.attrib['outputs']).items():wires[w]=v[t]
        elif tag=='Indicator': outputs[it.attrib['_name']]=wires[mappings(it.attrib['inputs'])['value']]
    return outputs

# Test vectors check the graph semantics, not NI execution semantics.
TESTS={
 'UE_Relative_Target':[((100,2), (102,)),((150,-20),(130,))],
 'UE_Measured_Displacement':[((302,300),(2,)),((289,300),(-11,))],
 'UE_Elapsed_Ms':[((1200,1000),(200,)),((600,600),(0,))],
 'UE_Ms_To_Seconds':[((1500,),(1.5,)),((0,),(0,))],
 'UE_Inclusive_Range':[((10,10,20),(True,)),((20,10,20),(True,)),((20.1,10,20),(False,))],
 'UE_Clamp_To_Limits':[((6,0,5),(5,False)),((0,0,5),(0,True)),((-1,0,5),(0,False))],
 'UE_Within_Tolerance':[((100,100,1),(True,)),((101,100,1),(True,)),((101.01,100,1),(False,))],
 'UE_Target_Error':[((100,96),(4,)),((10,12),(-2,))],
 'UE_Timeout_Reached':[((1000,1000),(True,)),((999,1000),(False,))],
 'UE_Stabilization_Reached':[((1000,1000),(True,)),((0,1000),(False,))],
 'UE_Dwell_Reached':[((400,500),(False,)),((500,500),(True,))],
 'UE_Retry_Allowed':[((1,3),(True,)),((3,3),(False,))],
 'UE_Cycles_Done':[((5,5),(True,)),((4,5),(False,))],
 'UE_Stop_Requested':[((False,False),(False,)),((True,False),(True,)),((False,True),(True,))],
 'UE_Select_Setpoint':[((True,150,100),(150,)),((False,150,100),(100,))],
 'UE_TriState_Condition':[((False,True),(-1,)),((True,False),(0,)),((True,True),(1,))],
 'UE_Command_Permitted':[((True,True,True,True),(True,)),((True,False,True,True),(False,)),((True,True,True,False),(False,))],
 'UE_Capture_Acceptable':[((True,True,True),(True,)),((True,False,True),(False,))],
 'UE_Relative_Target_Check':[((50,2,0,100),(52,True)),((95,10,0,100),(105,False)),((0,0,0,100),(0,True))],
 'UE_Sweep_Target':[((10,5,3),(25,)),((100,-10,2),(80,))],
 'UE_Hydraulic_Power_kW':[((100,60),(10,)),((200,0),(0,))],
 'UE_Percent_Drop':[((100,90),(10,True)),((0,5),(0,False)),((20,22),(-10,True))],
 'UE_Load_Fraction':[((1000,0.9),(900,)),((100,0),(0,))],
 'UE_Operating_Point_Ready':[((True,True,True),(True,)),((True,False,True),(False,))],
 'UE_Can_Advance_Step':[((True,True,True,True),(True,)),((False,True,True,True),(False,)),((True,True,False,True),(False,))],
 'UE_Run_Id_Matches':[((99,99),(True,)),((98,99),(False,))],
 'UE_Feedback_Freshness':[((1000,900,100),(100,True)),((1000,899,100),(101,False)),((1000,1001,100),(-1,False))],
 'UE_Cycle_Event_Duration':[((1050,1000),(50,)),((1000,1000),(0,))],
}

def eq(got,want):
    if isinstance(want,float): return math.isclose(got,want,rel_tol=1e-9,abs_tol=1e-9)
    return got==want

def run():
    files=0;cases=0;results=[]
    for entry in MAN['definitions']:
        path=ROOT/entry['path']; b=path.read_bytes()
        assert hashlib.sha256(b).hexdigest()==entry['sha256']
        r=check(b.decode('utf-8'),entry['pane']);files+=1
        name=entry['name'];assert name in TESTS,name
        for ins,expect in TESTS[name]:
            args={v['name']:arg for v,arg in zip(entry['inputs'],ins)}
            actual=simulate(r,args)
            assert len(expect)==len(entry['outputs'])
            for out,e in zip(entry['outputs'],expect):
                assert eq(actual[out['name']],e),(name,ins,actual,out,e)
            cases+=1
        results.append({'name':name,'pane':entry['pane'],'offline_structural':'PASS','graph_cases':len(TESTS[name]),'labview_converter':'NOT_RUN','labview_exec':'NOT_RUN'})
    report={'status':'OFFLINE_STATIC_AND_GRAPH_TESTS_PASS', 'aixml_files_checked':files,'simulation_cases_passed':cases, 'labview_converter':'NOT_RUN','labview_binary_execution':'NOT_RUN', 'details':results}
    (ROOT/'results'/'offline_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS: {files} AIXML static checks; {cases} graph-level tests. LABVIEW VALIDATION NOT RUN.')
    return report
if __name__=='__main__':run()
