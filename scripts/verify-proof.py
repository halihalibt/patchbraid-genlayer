"""Offline exhaustive recomputation of finalized state, not new network consensus."""
import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tests.host import m
root=pathlib.Path(__file__).resolve().parents[1]
raw=json.loads((root/'evidence/verification.json').read_text())
assert raw['chain_id']==61999 and raw['state_variant']=='latest-final'
count=0
for item in raw['final_reads']:
    space=item['value'];dims=space['dimensions']
    assert m.sha({'id':space['id'],'owner':space['owner'],'dimensions':dims})==space['domain_hash']
    for change in space['changes'].values():
        data={'dimensions':dims,'instruction':change['instruction']}
        m.parse_program(change['decision'],data)
        assert m.sha(data)==change['input_hash']
        assert m.sha(m.program_signature(change['decision'],dims))==change['behavior_hash']
    for pair in space['pairs'].values():
        a,b=space['changes'][pair['first']],space['changes'][pair['second']]
        proof=m.analyze(a['decision']['program'],b['decision']['program'],dims)
        assert proof==pair['proof']
        assert m.sha({'space':space['id'],'domain':space['domain_hash'],'first':a,'second':b,'proof':proof})==pair['binding']
    state=space['initial'];used=[]
    for event in space['executions']:
        assert event['pair'] not in used;used.append(event['pair'])
        pair=space['pairs'][event['pair']];assert pair['consumed'] and pair['binding']==event['binding']
        assert pair['proof']['status'] in ['TOTAL_COMMUTE','PARTIAL_COMMUTE']
        assert event['actor']==space['owner'] and event['before']==state
        a=space['changes'][pair['first']]['decision']['program'];b=space['changes'][pair['second']]['decision']['program']
        after=m.compose(b,a,state,dims) if event['reverse'] else m.compose(a,b,state,dims)
        assert after is not None and after==event['after'];state=after
    assert state==space['current']
    assert all(p['consumed']==(ref in used) for ref,p in space['pairs'].items())
    count+=1
assert count>=1
print('Recomputed every behavior vector, pair proof, conflict witness and atomic execution from finalized evidence.')
