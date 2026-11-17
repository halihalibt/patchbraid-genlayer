import unittest,json,itertools
from tests.host import m,gl,A,Return,tx
D=[{'key':'retry','description':'Retry limit','min':0,'max':2},{'key':'debug','description':'Debug flag','min':0,'max':1}]
def op(kind='SET',target='retry',value=1,source=''):return {'op':kind,'target':target,'value':value,'source':source}
def decision(program,status='KNOWN',quote='Set retry to one.'):return {'status':status,'program':program,'quote':quote}
class AlgebraTests(unittest.TestCase):
    def test_commutativity_and_domain_conflict(self):
        self.assertEqual(m.analyze([op()],[op(target='debug')],D)['status'],'TOTAL_COMMUTE')
        self.assertEqual(m.analyze([op('ADD')],[op(target='debug')],D)['status'],'PARTIAL_COMMUTE')
        r=m.analyze([op(value=0)],[op('ADD')],D);self.assertEqual(r['status'],'CONFLICT');self.assertNotEqual(r['witness']['ab'],r['witness']['ba'])
    def test_nonempty_success_domain_required(self):
        r=m.analyze([op(value=9)],[op(target='debug')],D);self.assertEqual(r['status'],'NO_COMMON_SUCCESS')
    def test_operation_order_and_atomic_failure(self):
        self.assertEqual(m.run_program([op(),op('COPY','debug',0,'retry')],[0,0],D),[1,1])
        state=[2,0];self.assertIsNone(m.run_program([op(target='debug'),op('ADD')],state,D));self.assertEqual(state,[2,0])
    def test_equivalence_is_behavior_not_syntax(self):
        a=decision([op('ADD',value=0)]);b=decision([op('COPY',value=0,source='retry')]);self.assertEqual(m.program_signature(a,D),m.program_signature(b,D))
        self.assertNotEqual(m.program_signature(a,D),m.program_signature(decision([op()]),D))
    def test_exhaustive_single_ops_against_distinct_transformers(self):
        programs=[[op('SET',key,val)] for key in ['retry','debug'] for val in range(-1,4)]+[[op('ADD',key,val)] for key in ['retry','debug'] for val in range(-2,3)]
        def independently(program,state):
            s=dict(zip(['retry','debug'],state));step=program[0];k=step['target'];s[k]=step['value'] if step['op']=='SET' else s[k]+step['value'];return [s['retry'],s['debug']] if 0<=s['retry']<=2 and 0<=s['debug']<=1 else None
        for a,b in itertools.product(programs,repeat=2):
            statuses=[]
            for state in itertools.product(range(3),range(2)):
                x=independently(a,state);ab=None if x is None else independently(b,x);y=independently(b,state);ba=None if y is None else independently(a,y);statuses.append((ab,ba))
            expected='CONFLICT' if any(x!=y for x,y in statuses) else 'NO_COMMON_SUCCESS' if all(x is None for x,y in statuses) else 'TOTAL_COMMUTE' if all(x is not None for x,y in statuses) else 'PARTIAL_COMMUTE'
            self.assertEqual(m.analyze(a,b,D)['status'],expected)

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        gl.message.sender_address=A[0];self.c=m.PatchBraid();self.c.spaces={};self.c.ids=[];self.sid=self.c.create_space('config-lab',m.pack(D),'[0,0]');self.original=m.compile_program
        m.compile_program=lambda data:decision([op()])
    def tearDown(self):m.compile_program=self.original
    def space(self):return json.loads(self.c.get_space(self.sid))
    def call(self,method,*args,actor=0):return tx(self.c,actor,method,self.sid,self.space()['revision'],*args)
    def register(self,ref,program):
        m.compile_program=lambda data:decision(program);self.call('register_change',ref,'Set retry to one.')
    def pair(self):
        self.register('change-one',[op()]);self.register('change-two',[op(target='debug')]);self.call('analyze_pair','pair-one','change-one','change-two');return self.space()['pairs']['pair-one']
    def test_binding_owner_and_replay(self):
        pair=self.pair()
        with self.assertRaisesRegex(Exception,'OWNER_ONLY'):self.call('execute_pair','pair-one',pair['binding'],False,actor=1)
        with self.assertRaisesRegex(Exception,'PAIR_BINDING'):self.call('execute_pair','pair-one','wrong',False)
        self.call('execute_pair','pair-one',pair['binding'],True);self.assertEqual(self.space()['current'],[1,1])
        with self.assertRaisesRegex(Exception,'PAIR_CONSUMED'):self.call('execute_pair','pair-one',pair['binding'],False)
        self.assertEqual(len(self.space()['executions']),1)
    def test_conflict_cannot_execute(self):
        self.register('change-one',[op(value=0)]);self.register('change-two',[op('ADD')]);self.call('analyze_pair','pair-one','change-one','change-two');pair=self.space()['pairs']['pair-one']
        with self.assertRaisesRegex(Exception,'UNSAFE_REORDER'):self.call('execute_pair','pair-one',pair['binding'],False)
        self.assertEqual(self.space()['current'],[0,0])
    def test_partial_pair_can_reject_current_state_without_consumption(self):
        pair=self.pair();self.call('execute_pair','pair-one',pair['binding'],False)
        self.register('raise-once',[op('ADD')]);self.call('analyze_pair','raise-first','raise-once','change-two');p=self.space()['pairs']['raise-first'];self.call('execute_pair','raise-first',p['binding'],False)
        self.call('analyze_pair','raise-again','raise-once','change-two');p=self.space()['pairs']['raise-again']
        with self.assertRaisesRegex(Exception,'CURRENT_STATE_REJECTED'):self.call('execute_pair','raise-again',p['binding'],False)
        self.assertFalse(self.space()['pairs']['raise-again']['consumed']);self.assertEqual(self.space()['current'],[2,1])
    def test_unknown_duplicate_and_stale(self):
        m.compile_program=lambda data:decision([],status='UNKNOWN');self.call('register_change','unknown-edit','Make it better.')
        self.register('known-edit',[op()])
        with self.assertRaisesRegex(Exception,'UNCOMPILED_CHANGE'):self.call('analyze_pair','bad-pair','unknown-edit','known-edit')
        with self.assertRaisesRegex(Exception,'CHANGE_EXISTS'):self.call('register_change','known-edit','Set retry to one.')
        with self.assertRaisesRegex(Exception,'STALE_REVISION'):tx(self.c,0,'register_change',self.sid,0,'other-edit','Set retry to one.')
    def test_model_rejects_forged_quote_unsupported_ops_and_numbers(self):
        data={'dimensions':D,'instruction':'Set retry to one.'}
        for answer in [decision([op()],quote='invented'),decision([op('MULTIPLY')]),decision([op(value=True)]),decision([op(target='absent')])]:
            with self.assertRaises(Exception):m.parse_program(answer,data)
    def test_validator_extensional_equivalence_and_semantic_audit(self):
        data={'dimensions':D,'instruction':'Leave the retry variable unchanged.'};good=decision([op('ADD',value=0)],quote=data['instruction']);equivalent=decision([op('COPY',value=0,source='retry')],quote=data['instruction']);wrong=decision([op()],quote=data['instruction'])
        gl.nondet.exec_prompt=lambda prompt,**kw:{'valid':True} if prompt.startswith('Audit the candidate') else good
        def run(leader,validate):
            self.assertTrue(validate(Return(equivalent)));self.assertFalse(validate(Return(wrong)));return leader()
        gl.vm.run_nondet_unsafe=run;self.original(data)
        gl.nondet.exec_prompt=lambda prompt,**kw:{'valid':False} if prompt.startswith('Audit the candidate') else good
        gl.vm.run_nondet_unsafe=lambda leader,validate:self.assertFalse(validate(Return(good))) or good
        self.original(data)
if __name__=='__main__':unittest.main()
