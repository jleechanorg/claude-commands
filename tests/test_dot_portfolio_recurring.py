import importlib
import json
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.claude/skills/dot-portfolio-coordinator/scripts'))

class SharedRecurrenceTests(unittest.TestCase):
    def setUp(self):
        self.m=importlib.import_module('modules.recurring_ledger')
        self.tmp=tempfile.TemporaryDirectory(dir='/tmp');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.now=36000
        self.accounts=[]
        for i,name in enumerate(('first','second','third')):
            p=self.root/(name+'.json');p.write_text(json.dumps({'pending_delivery':{'event_id':'old-uncertain'} if i==2 else None}));p.chmod(0o600)
            self.accounts.append({'account':name,'historical_ledger':str(p),'historical_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        self.state=self.root/'shared';self.state.mkdir(mode=0o700)
        self.config={'schedule_id':'hourly-fixture','authority':'Check current work, no merge authority.', 'accounts':self.accounts,'shared_state_dir':str(self.state)}
        local=self.root/'default-worker';local.mkdir(mode=0o700)
        self.config['hosts']={'mac':{'state_dir':str(local)}}
        self.enterContext(mock.patch('time.time',side_effect=lambda:self.now))
        self.binding='1'*64
        self.enterContext(mock.patch.object(self.m,'authority_host_matches',return_value=True,create=True))
        self.ledger=self.m.SharedLedger(self.config,self.binding)
        self.ledger.initialize()

    def claim(self,role='mac',account='first',now=None):
        return self.ledger.apply({'action':'claim','role':role,'account':account},now=self.now if now is None else now)

    def finish(self,claim,outcome='delivered',verified=True):
        return self.ledger.apply({'action':'finish','role':claim['role'],'account':claim['account'],'token':claim['token'],'event_id':claim['event_id'],'result':{'outcome':outcome,'delivery_verified':verified}},now=self.now+10)

    def recovery_worker(self,rpc):
        from modules.recurring_worker import RecurringWorker
        root=self.root/'rpc-local'
        root.mkdir(mode=0o700,exist_ok=True)
        self.config['hosts']={'mac':{'state_dir':str(root)}}
        return RecurringWorker(self.config,self.binding,'mac',rpc=rpc)

    def test_lost_claim_and_finish_replies_recover_without_second_execution(self):
        for lost in ('claim','finish'):
            with self.subTest(lost=lost):
                account='first' if lost=='claim' else 'second'
                self.now=36000 if account=='first' else 37200
                calls=[];failed=[]
                def rpc(request):
                    result=self.ledger.apply(request,now=self.now)
                    if request['action']==lost and (lost=='finish' or not failed):
                        failed.append(True);raise OSError('synthetic lost reply')
                    return result
                worker=self.recovery_worker(rpc)
                worker.operation=lambda claim:calls.append(claim['event_id']) or {'outcome':'delivered','delivery_verified':True}
                with mock.patch('time.time',side_effect=lambda:self.now):
                    result=worker.run_account(account)
                self.assertEqual(result['status'],'recorded')
                self.assertEqual(len(calls),1)
                self.assertIsNone(json.loads((self.state/'ledger.json').read_text())['accounts'][account]['pending'])

    def test_durable_finish_survives_outage_and_worker_restart(self):
        sent=[]
        def broken(request):
            if request['action'] in ('finish','status'):raise OSError('synthetic outage')
            return self.ledger.apply(request,now=self.now)
        worker=self.recovery_worker(broken)
        worker.operation=lambda claim:sent.append(claim['event_id']) or {'outcome':'delivered','delivery_verified':True}
        with mock.patch('time.time',return_value=self.now):
            self.assertEqual(worker.run_account('first')['status'],'held')
            resumed=self.recovery_worker(lambda r:self.ledger.apply(r,now=self.now))
            resumed.operation=lambda c:self.fail('durable completion must not execute again')
            self.assertEqual(resumed.run_account('first')['status'],'recorded')
        self.assertEqual(len(sent),1)

    def test_transient_finish_lock_contention_is_retryable(self):
        failures=[]
        def rpc(request):
            if request['action']=='finish' and not failures:
                import fcntl
                failures.append(True)
                fd=self.ledger._lock()
                try:
                    reply=self.ledger.apply(request,now=self.now)
                    self.assertEqual(reply['reason'],'shared_lock_busy')
                    return reply
                finally:os.close(fd)
            return self.ledger.apply(request,now=self.now)
        worker=self.recovery_worker(rpc)
        worker.operation=lambda c:{'outcome':'no_action','delivery_verified':False}
        with mock.patch('time.time',return_value=self.now):
            self.assertEqual(worker.run_account('first')['status'],'recorded')

    def test_finish_is_idempotent_and_status_never_admits_execution(self):
        first=self.claim()
        self.assertEqual(self.finish(first)['status'],'recorded')
        self.assertEqual(self.finish(first)['status'],'recorded')
        status=self.ledger.apply(dict(first,action='status'),now=self.now+11)
        self.assertEqual(status['status'],'recorded')
        self.assertEqual(self.finish(first,'no_action',False)['status'],'held')

    def test_safe_terminal_receipt_can_settle_after_ledger_write_failure(self):
        first=self.claim()
        with mock.patch.object(self.ledger,'_write',side_effect=OSError('synthetic fsync failure')):
            self.assertEqual(self.finish(first)['status'],'held')
        self.assertEqual(self.finish(first)['status'],'recorded')
        self.assertEqual(self.claim('linux',now=37800)['status'],'admitted')

    def test_explicit_due_accepts_bounded_skew_without_changing_slot(self):
        for offset in (-60,60,180):
            with self.subTest(offset=offset):
                # Separate fixture account/hour for each grant.
                due=36000+(offset+60)*3600
                result=self.ledger.apply({'action':'claim','role':'mac','account':'first',
                    'request_id':('a' if offset==-60 else 'b' if offset==60 else 'c')*32,
                    'due_epoch':due},now=due+offset)
                self.assertEqual(result['status'],'admitted')
                self.assertEqual(result['due_epoch'],due)
                self.assertEqual(result['deadline_epoch'],due+1200)
                self.assertEqual(result['authority_epoch'],due+offset)
                self.ledger.apply(dict(result,action='finish',result={'outcome':'no_action','delivery_verified':False}),now=due+offset)

    def test_explicit_due_rejects_outside_skew_and_wrong_cadence(self):
        for due,now in ((36000,35939),(36000,36181),(36001,36001)):
            result=self.ledger.apply({'action':'claim','role':'mac','account':'first','due_epoch':due},now=now)
            self.assertEqual(result['status'],'held')
        self.assertIsNone(json.loads((self.state/'ledger.json').read_text())['accounts']['first']['pending'])

    def test_claim_retry_keeps_deadline_and_updates_authority_clock(self):
        request={'action':'claim','role':'mac','account':'first','due_epoch':36000,'request_id':'a'*32}
        first=self.ledger.apply(request,now=35940)
        second=self.ledger.apply(request,now=36020)
        self.assertEqual(first['event_id'],second['event_id'])
        self.assertEqual(first['deadline_epoch'],second['deadline_epoch'])
        self.assertEqual(second['authority_epoch'],36020)

    def test_authority_clock_and_full_rpc_elapsed_bound_local_budget(self):
        from modules.recurring_worker import authority_deadline
        with mock.patch('time.monotonic',return_value=200):
            self.assertEqual(authority_deadline({'deadline_epoch':37200,'authority_epoch':36060},190),1330)

    def test_lost_claim_recovers_after_expiry_without_dispatch(self):
        def outage(request):
            if request['action']=='claim':self.ledger.apply(request,now=self.now)
            raise OSError('synthetic reply outage')
        worker=self.recovery_worker(outage)
        worker.operation=lambda c:self.fail('lost claim must not dispatch')
        self.assertEqual(worker.run_account('first')['status'],'held')
        self.now+=3600
        resumed=self.recovery_worker(lambda r:self.ledger.apply(r,now=self.now))
        resumed.operation=lambda c:self.fail('expired unstarted claim must not dispatch')
        self.assertEqual(resumed.run_account('first',recover_only=True)['status'],'recorded')
        self.assertIsNone(json.loads((self.state/'ledger.json').read_text())['accounts']['first']['pending'])

    def test_recovery_command_never_creates_a_claim(self):
        worker=self.recovery_worker(lambda r:self.fail('recovery with no journal must not call authority'))
        self.assertEqual(worker.run_account('first',recover_only=True)['status'],'no_action')
        self.assertIsNone(json.loads((self.state/'ledger.json').read_text())['accounts']['first']['pending'])

    def test_local_execution_lock_excludes_second_worker(self):
        import fcntl
        worker=self.recovery_worker(lambda r:self.ledger.apply(r,now=self.now))
        lock=self.root/'rpc-local/rpc-first.lock'
        fd=os.open(lock,os.O_CREAT|os.O_RDWR,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            worker.operation=lambda c:self.fail('concurrent worker must not execute')
            self.assertEqual(worker.run_account('first')['reason'],'local_execution_busy')
        finally:os.close(fd)
        self.assertIsNone(json.loads((self.state/'ledger.json').read_text())['accounts']['first']['pending'])

    def test_request_identity_cannot_be_rebound_to_another_due(self):
        request={'action':'claim','role':'mac','account':'first','due_epoch':36000,'request_id':'d'*32}
        self.assertEqual(self.ledger.apply(request,now=36000)['status'],'admitted')
        for action in ('claim','status'):
            result=self.ledger.apply(dict(request,action=action,due_epoch=39600),now=36001)
            self.assertEqual(result['status'],'held')

    def test_terminal_history_is_durable_before_current_journal_completes(self):
        from modules import recurring_worker as w
        worker=self.recovery_worker(lambda r:self.ledger.apply(r,now=self.now))
        worker.operation=lambda c:{'outcome':'no_action','delivery_verified':False}
        real=w._atomic_write
        def write(path,*args):
            if '/rpc-history/' in path:raise OSError('synthetic archive failure')
            return real(path,*args)
        with mock.patch.object(w,'_atomic_write',side_effect=write):
            with self.assertRaises(OSError):worker.run_account('first')
        journal=json.loads((self.root/'rpc-local/rpc-first.json').read_text())
        self.assertEqual(journal['phase'],'finish')

    def test_service_environment_is_explicit_and_user_unit_is_labelled(self):
        from modules.recurring_worker import service_definitions
        import plistlib
        env={'HOME':'/fixture/home','PATH':'/fixture/bin:/usr/bin:/bin'}
        files=service_definitions('/usr/bin/python3','/fixture/worker.py','/fixture/schedule.json','a'*64,
                                 environments={'mac':env,'linux':env})
        self.assertEqual(plistlib.loads(files['mac_plist'].encode())['EnvironmentVariables'],env)
        self.assertIn('Environment="HOME=/fixture/home"',files['linux_service'])
        self.assertIn('user unit',files['linux_service'])

    def test_batch_reserves_settlement_margin(self):
        from modules.recurring_worker import bounded_operation_deadline
        self.assertEqual(bounded_operation_deadline(5000,3600),3480)
        self.assertEqual(bounded_operation_deadline(3000,3600),3000)

    def test_cli_render_uses_pinned_environment_and_rejects_wrong_uid(self):
        import subprocess,plistlib
        env={'HOME':str(self.root),'PATH':'/usr/bin:/bin'}
        config=dict(self.config,schema_version=1,hosts={role:{'uid':os.getuid(),'service_environment':env} for role in ('mac','linux')})
        path=self.root/'schedule-cli.json'
        for uid,expected in ((os.getuid(),0),(os.getuid()+1,2)):
            config['hosts']['mac']['uid']=uid
            path.write_text(json.dumps(config));path.chmod(0o600)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            result=subprocess.run([sys.executable,str(ROOT/'.claude/skills/dot-portfolio-coordinator/scripts/coordinator-recurring.py'),
                '--schedule',str(path),'--sha256',digest,'--role','mac','render'],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,expected)
            reply=json.loads(result.stdout)
            if expected==0:self.assertEqual(plistlib.loads(reply['mac_plist'].encode())['EnvironmentVariables'],env)
            else:self.assertEqual(reply['status'],'held')

    def test_remote_request_preserves_exact_broker_packet_without_local_fallback(self):
        from modules import recurring_worker as w
        self.config['authority_endpoint']={'python':'/fixture/python','script':'/fixture/broker.py',
            'schedule':'/fixture/private.json','ssh_host':'fixture-existing-alias'}
        worker=w.RecurringWorker(self.config,self.binding,'mac')
        request={'action':'claim','role':'mac','account':'first','request_id':'f'*32,'due_epoch':36000}
        def remote(argv,**kwargs):
            self.assertEqual(argv[:7],['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','--','fixture-existing-alias'])
            self.assertIn('/fixture/broker.py',argv[-1]);self.assertEqual(kwargs['timeout_secs'],20)
            return 0,json.dumps(self.ledger.apply(json.loads(kwargs['input_text']),now=self.now)),''
        with mock.patch.object(w,'run_bounded_command',side_effect=remote):
            reply=worker.remote_request(request)
        self.assertEqual(reply['request_id'],request['request_id'])
        with mock.patch.object(w,'run_bounded_command',return_value=(255,'','')):
            with self.assertRaises(ValueError):worker.remote_request(request)

    def test_normal_batch_waits_for_exact_account_offsets(self):
        from modules import recurring_worker as w
        worker=self.recovery_worker(lambda r:{})
        seen=[]
        worker.run_account=lambda a:seen.append((a,self.now)) or {'status':'recorded'}
        with mock.patch.object(w.time,'sleep',side_effect=lambda delay:setattr(self,'now',self.now+delay)):
            worker.run_batch()
        self.assertEqual(seen,[('first',36000),('second',37200),('third',38400)])
        self.assertIsNotNone(worker.batch_deadline)

    def test_utc_cadence_host_offset_and_no_catchup(self):
        self.assertEqual(self.m.due_slot(36000,'mac',0),36000)
        self.assertEqual(self.m.due_slot(37800,'linux',0),37800)
        self.assertEqual(self.m.due_slot(37200,'mac',1),37200)
        self.assertEqual(self.m.due_slot(39000,'linux',1),39000)
        self.assertEqual(self.claim(now=36121)['reason'],'missed_start_window')
        self.assertEqual(self.claim(now=36000)['status'],'admitted')

    def test_concurrent_hosts_cannot_admit_same_account(self):
        # Linux's next phase is inside an unresolved Mac claim; no lease expiry releases it.
        first=self.claim();self.assertEqual(first['status'],'admitted')
        peer=self.claim('linux',now=37800)
        self.assertEqual(peer['reason'],'account_pending_hold')
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.claim(now=36000),range(2)))
        self.assertTrue(all(r['status']!='admitted' for r in results))

    def test_simultaneous_claim_has_one_winner(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.claim(),range(2)))
        self.assertEqual(sum(r['status']=='admitted' for r in results),1)

    def test_orphan_and_uncertain_hold_survive_restart_next_hour(self):
        claim=self.claim()
        self.ledger=self.m.SharedLedger(self.config,self.binding)
        self.assertEqual(self.claim(now=39600)['reason'],'account_pending_hold')
        self.finish(claim,'uncertain',False)
        self.assertEqual(self.claim('linux',now=41400)['reason'],'account_pending_hold')

    def test_historical_hold_preserved_other_accounts_independent(self):
        before=Path(self.accounts[2]['historical_ledger']).read_bytes()
        self.assertEqual(self.claim(account='third',now=38400)['reason'],'historical_pending_hold')
        self.assertEqual(self.claim(account='second',now=37200)['status'],'admitted')
        self.assertEqual(Path(self.accounts[2]['historical_ledger']).read_bytes(),before)

    def test_verified_completion_deduplicates_hour_then_allows_next(self):
        first=self.claim();self.finish(first)
        self.assertEqual(self.claim(now=36020)['reason'],'slot_already_claimed')
        self.assertEqual(self.claim('linux',now=37800)['status'],'admitted')

    def test_no_send_completion_allows_next_phase_but_no_retry(self):
        first=self.claim();self.finish(first,'no_action',False)
        self.assertEqual(self.claim(now=36020)['reason'],'slot_already_claimed')
        self.assertEqual(self.claim(now=39600)['status'],'admitted')

    def test_unknown_outcome_or_bad_token_never_releases(self):
        first=self.claim();wrong=dict(first,token='bad')
        self.assertEqual(self.finish(wrong)['status'],'held')
        self.finish(first,'made_up_success',False)
        self.assertEqual(self.claim(now=39600)['reason'],'account_pending_hold')

    def test_stop_clock_rollback_missing_state_and_binding_fail_closed(self):
        (self.state/'STOP').touch()
        self.assertEqual(self.claim()['reason'],'operator_stop')
        (self.state/'STOP').unlink();first=self.claim();self.finish(first)
        self.assertEqual(self.claim(now=35999)['reason'],'clock_rollback_hold')
        other=self.m.SharedLedger(self.config,'2'*64)
        self.assertEqual(other.apply({'action':'claim','role':'linux','account':'first'},now=37800)['reason'],'schedule_binding_hold')
        (self.state/'ledger.json').unlink()
        self.assertEqual(self.claim(now=39600)['reason'],'ledger_unavailable_hold')
        with self.assertRaises(ValueError):self.ledger.initialize()

    def test_claim_receipt_and_grant_are_finite(self):
        first=self.claim()
        self.assertEqual(first['deadline_epoch']-first['due_epoch'],1200)
        self.assertEqual(self.ledger.apply(dict(first,action='check'),now=36010)['status'],'admitted')
        self.assertEqual(self.ledger.apply(dict(first,action='check'),now=37201)['status'],'held')
        self.assertEqual((self.state/'ledger.json').stat().st_mode&0o777,0o600)
        self.assertTrue((self.state/'receipts'/f"{first['event_id']}.json").exists())


    def test_uncertain_completion_cannot_be_relabelled_or_checked_as_live(self):
        first=self.claim();self.finish(first,'uncertain',False)
        self.assertEqual(self.finish(first)['status'],'held')
        self.assertEqual(self.ledger.apply(dict(first,action='check'),now=self.now+20)['status'],'held')

    def test_worker_restart_does_not_repeat_claimed_slot_and_independent_account_runs(self):
        from modules.recurring_worker import RecurringWorker
        calls=[]
        def rpc(request):return self.ledger.apply(request,now=self.now)
        worker=RecurringWorker(self.config,self.binding,'mac',rpc=rpc)
        worker.operation=lambda claim: calls.append(claim['account']) or {'outcome':'delivered','delivery_verified':True}
        self.assertEqual(worker.run_account('first')['status'],'recorded')
        self.assertEqual(worker.run_account('first')['reason'],'slot_already_claimed')
        self.now=39600
        self.assertEqual(worker.run_account('first')['status'],'recorded')
        self.now=40800
        self.assertEqual(worker.run_account('second')['status'],'recorded')
        self.now=42000
        self.assertEqual(worker.run_account('third')['reason'],'historical_pending_hold')
        self.assertEqual(calls,['first','first','second'])

    def test_worker_crash_and_authority_outage_never_release_or_fall_back_local(self):
        from modules.recurring_worker import RecurringWorker
        def rpc(request):return self.ledger.apply(request,now=self.now)
        worker=RecurringWorker(self.config,self.binding,'mac',rpc=rpc)
        def crash(claim):raise RuntimeError('synthetic failure')
        worker.operation=crash
        self.assertTrue(worker.run_account('first')['hold_preserved'])
        self.assertEqual(worker.run_account('first')['reason'],'account_pending_hold')
        def unavailable(request):raise OSError('authority unavailable')
        worker.rpc=unavailable
        self.assertEqual(worker.run_account('second')['reason'],'shared_authority_unavailable')

    def test_hourly_batch_start_is_utc_and_missed_wake_does_not_catch_up(self):
        from modules.recurring_worker import batch_start
        self.assertEqual(batch_start(36000,'mac'),36000)
        self.assertEqual(batch_start(37800,'linux'),37800)
        self.assertIsNone(batch_start(36600,'mac'))
        self.assertIsNone(batch_start(39600,'linux'))


    def test_real_worker_operation_uses_immutable_single_grant_and_existing_guarded_sender(self):
        from modules import recurring_worker as worker_module
        from modules.sender import validate_operator_grant
        local_root=self.root/'local';local_root.mkdir(mode=0o700)
        source=self.root/'sources.json';source.write_text('{}')
        dot_config=self.root/'dot.json';dot_config.write_text('{}')
        local={'state_dir':str(local_root),'hostname':'fixture-host','driver':'fixture-driver',
            'sources':str(source),'dot_config_file':str(dot_config),'transport_script':'/fixture/dot.sh',
            'execution_sha256':'e'*64}
        self.config['hosts']={'mac':local}
        profile={'executable':{'resolved_path':'/fixture/driver'}}
        deps={'node':{'selected_path':'/fixture/node'}}
        pinned={'source_digest':'source', 'sources':worker_module.file_fingerprint(source),
            'dot_config':worker_module.file_fingerprint(dot_config),'execution':deps}
        calls=[]
        def send(config,slot,state,snapshot,root,driver,transport,deadline,**kwargs):
            a=config['accounts'][slot['account_index']]
            valid,reason,grant=validate_operator_grant(a['grant_file'],a['grant_sha256'],a['account'])
            self.assertTrue(valid,reason);self.assertEqual(grant['max_messages'],1)
            self.assertEqual(grant['expiry_epoch']-grant['activated_at_epoch'],1200)
            self.assertEqual(Path(a['grant_file']).stat().st_mode&0o777,0o400)
            self.assertTrue(kwargs['execution_guard']())
            self.assertEqual(kwargs['node_path'],'/fixture/node')
            self.assertEqual(config['authority'],self.config['authority'])
            workspace=root/('driver-'+slot['event_id']);workspace.mkdir()
            (workspace/'.driver-diagnostic-fixture.json').write_text(json.dumps({'failure_stage':'process_exit','stdout':{'text':'[REDACTED]'}}))
            calls.append(slot['event_id'])
            return {'outcome':'delivered','delivery_verified':True}
        cli=SimpleNamespace(SourceRegistry=lambda _:object(),
            PortfolioCollector=lambda *a,**kw:SimpleNamespace(collect_all=lambda **kw:{}),
            model_snapshot_and_reader=lambda *a:({},lambda *a:None),run_pilot_slot=send)
        with mock.patch.object(worker_module,'probe_for_account',return_value={'status':'authenticated'},create=True), \
             mock.patch.object(worker_module,'controller',return_value=cli), \
             mock.patch.object(worker_module,'inspect_execution',return_value=(profile,pinned,'e'*64)), \
             mock.patch.object(worker_module,'source_digest',return_value='source'), \
             mock.patch.object(worker_module,'execution_dependencies',return_value=deps), \
             mock.patch.object(worker_module.socket,'gethostname',return_value='fixture-host'), \
             mock.patch.object(worker_module.platform,'system',return_value='Darwin'), \
             mock.patch('time.time',return_value=self.now):
            worker=worker_module.RecurringWorker(self.config,self.binding,'mac',rpc=lambda req:self.ledger.apply(req,now=self.now))
            result=worker.run_account('first')
        self.assertEqual(result['status'],'recorded');self.assertEqual(len(calls),1)
        self.assertTrue((local_root/calls[0]/'result.json').exists())
        self.assertEqual(len(list((local_root/calls[0]).glob('driver-diagnostic-*.json'))),1)

    def test_worker_reaches_real_prepared_sender_and_preserves_local_attempt(self):
        from modules import recurring_worker as w
        from test_dot_portfolio_coordinator_pilot import RecurringPilotTests, cli
        fixture=RecurringPilotTests()
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.now=self.now
        # The real environment scrub deliberately removes DOT_CAPTURE_FILE.
        fixture.transport.write_text(fixture.transport.read_text().replace('$DOT_CAPTURE_FILE',str(fixture.capture)))
        root=self.root/'real-worker';root.mkdir(mode=0o700)
        source=self.root/'sources.json';source.write_text('{}')
        dot=self.root/'dot.json';dot.write_text('{}')
        local={'state_dir':str(root),'hostname':'fixture-host','driver':'agy',
               'sources':str(source),'dot_config_file':str(dot),'transport_script':str(fixture.transport),
               'execution_sha256':'e'*64}
        self.config['hosts']={'mac':local}
        profile={'executable':{'resolved_path':'/fixture/agy'}}
        deps={'node':{'selected_path':'/fixture/node'}}
        pinned={'source_digest':'source','sources':w.file_fingerprint(source),
                'dot_config':w.file_fingerprint(dot),'execution':deps}
        with mock.patch.object(w,'controller',return_value=cli), \
             mock.patch.object(w,'probe_for_account',return_value={'status':'authenticated'}), \
             mock.patch.object(w,'inspect_execution',return_value=(profile,pinned,'e'*64)), \
             mock.patch.object(w,'source_digest',return_value='source'), \
             mock.patch.object(w,'execution_dependencies',return_value=deps), \
             mock.patch.object(w.socket,'gethostname',return_value='fixture-host'), \
             mock.patch.object(w.platform,'system',return_value='Darwin'), \
             mock.patch.object(cli,'SourceRegistry',return_value=object()), \
             mock.patch.object(cli,'PortfolioCollector',return_value=SimpleNamespace(collect_all=lambda **kw:{})), \
             mock.patch.object(cli,'model_snapshot_and_reader',return_value=(fixture.snapshot,fixture.source_reader)):
            worker=w.RecurringWorker(self.config,self.binding,'mac',rpc=lambda r:self.ledger.apply(r,now=self.now))
            result=worker.run_account('first')
            self.assertEqual(result['result']['outcome'],'delivered')
            event=result['event_id']
            self.assertEqual(fixture.capture.read_text().splitlines(),['first '+event])
            ledger=json.loads((root/event/'sender/account_first.json').read_text())
            self.assertEqual(ledger['attempted_count'],1)
            self.assertEqual(ledger['retained_event_ids'],[event])
            self.assertIsNone(ledger['pending_delivery'])
            # Existing local attempt evidence is unknown state, never proven no-send.
            receipt=json.loads((self.state/'receipts'/(event+'.json')).read_text())
            self.assertEqual(worker.operation(receipt)['outcome'],'uncertain')
            self.assertEqual(fixture.capture.read_text().splitlines(),['first '+event])
            # Real typed no-send proof passes through sender and shared settlement.
            fixture.transport.write_text('#!'+sys.executable+'\nimport sys,json,hashlib,os\n'
                "message=open(sys.argv[4],'rb').read()\n"
                "print('DOT_PRECOMMIT_NO_SEND '+json.dumps({'schema_version':2,'phase':'precommit','reason':'composer_not_empty','account':sys.argv[2],'event_id':os.environ['COORDINATOR_CHANGE_ID'],'message_sha256':hashlib.sha256(message).hexdigest()}),flush=True)\n")
            self.now=fixture.now=37200
            no_send=worker.run_account('second')
            self.assertEqual(no_send['result']['outcome'],'no_action')
            self.assertFalse(no_send['hold_preserved'])
            self.assertEqual(self.claim(account='second')['reason'],'slot_already_claimed')
            self.assertEqual(self.claim('linux','second',now=39000)['status'],'admitted')

    def test_known_preflight_failure_does_not_create_uncertain_account_hold(self):
        from modules import recurring_worker as worker_module
        worker=worker_module.RecurringWorker(self.config,self.binding,'mac',rpc=lambda req:self.ledger.apply(req,now=self.now))
        def blocked(claim):raise worker_module.PreflightNoSend('capability_blocked')
        worker.operation=blocked
        result=worker.run_account('first')
        self.assertFalse(result['hold_preserved'])
        self.assertEqual(self.claim('linux',now=37800)['status'],'admitted')

    def test_service_templates_are_calendar_triggered_without_catchup_or_keepalive(self):
        from modules.recurring_worker import service_definitions
        files=service_definitions('/usr/bin/python3','/fixture/coordinator-recurring.py','/fixture/schedule.json','a'*64)
        self.assertIn('OnCalendar=*-*-* *:30:00 UTC',files['linux_timer'])
        self.assertIn('Persistent=false',files['linux_timer'])
        self.assertIn('RuntimeMaxSec=3720',files['linux_service'])
        import plistlib
        data=plistlib.loads(files['mac_plist'].encode())
        self.assertFalse(data['RunAtLoad']);self.assertFalse(data['KeepAlive'])
        self.assertEqual(data['StartCalendarInterval'],{'Minute':0})
        self.assertIn('--role',data['ProgramArguments'])


    def test_wrong_authority_host_refuses_initialize_and_claim(self):
        with mock.patch.object(self.m,'authority_host_matches',return_value=False,create=True):
            self.assertEqual(self.claim()['reason'],'authority_host_mismatch')
            empty=self.root/'wrong-authority';empty.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError,'authority_host_mismatch'):
                self.m.SharedLedger(dict(self.config,shared_state_dir=str(empty)),self.binding).initialize()
            self.assertFalse((empty/'ledger.json').exists())

    def test_pin_is_checked_against_the_same_bytes_that_are_parsed(self):
        cfg=dict(self.config,schema_version=1)
        old=json.dumps(cfg).encode();new=json.dumps(dict(cfg,authority='changed authority')).encode()
        p=self.root/'schedule.json';p.write_bytes(old);p.chmod(0o600)
        with mock.patch.object(Path,'read_bytes',return_value=new):
            with self.assertRaises(ValueError):
                self.m.load_schedule(p,hashlib.sha256(new).hexdigest())

    def test_wall_clock_rollback_stops_batch_without_waiting(self):
        from modules import recurring_worker as w
        root=self.root/'worker';root.mkdir(mode=0o700)
        self.config['hosts']={'mac':{'state_dir':str(root)}}
        clock={'wall':36000}
        worker=w.RecurringWorker(self.config,self.binding,'mac',rpc=lambda r:{})
        def run(account):clock['wall']=35900;return {'status':'recorded'}
        worker.run_account=run
        with mock.patch.object(w.time,'time',side_effect=lambda:clock['wall']), \
             mock.patch.object(w.time,'sleep',side_effect=AssertionError('rollback must not wait')):
            results=worker.run_batch()
        self.assertEqual(results[-1]['reason'],'clock_rollback_hold')


    def test_completion_receipt_survives_crash_before_ledger_settlement(self):
        first=self.claim()
        with mock.patch.object(self.ledger,'_write',side_effect=OSError('synthetic fsync failure')):
            self.assertEqual(self.finish(first)['status'],'held')
        path=self.state/'receipts'/(first['event_id']+'.json')
        original=path.read_bytes()
        self.assertEqual(self.finish(first,'uncertain',False)['status'],'held')
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(self.claim(now=39600)['reason'],'account_pending_hold')

    def test_terminal_receipt_blocks_check_after_failed_ledger_settlement(self):
        first=self.claim()
        with mock.patch.object(self.ledger,'_write',side_effect=OSError('synthetic fsync failure')):
            self.assertEqual(self.finish(first,'uncertain',False)['status'],'held')
        result=self.ledger.apply(dict(first,action='check'),now=self.now+11)
        self.assertEqual(result['status'],'held')

    def test_dangling_stop_marker_still_stops_new_claim(self):
        (self.state/'STOP').symlink_to(self.root/'missing-stop-target')
        self.assertEqual(self.claim()['reason'],'operator_stop')


    def test_session_probe_requires_identity_composer_and_fresh_cleanup(self):
        from modules import recurring_worker as w
        from datetime import datetime,timezone
        config=self.root/'dot-probe.json';config.write_text(json.dumps({'accounts':{'first':{'profile_match':'fixture@example.invalid'}}}))
        local={'dot_config_file':str(config),'transport_script':'/fixture/dot.sh'}
        good={'schema_version':1,'status':'authenticated','identity_match':True,
              'composer_available':True,'endpoint_status':200,'cleanup_state':'context_closed',
              'timestamp':datetime.fromtimestamp(self.now,timezone.utc).isoformat()}
        def execute(argv,**kw):
            self.assertEqual(argv[1:4],['--account','first','probe'])
            self.assertEqual(len(argv[4]),64)
            return 0,'DOT_SESSION_PROBE '+json.dumps(good),' '
        with mock.patch.object(w,'run_bounded_command',side_effect=execute),mock.patch('time.time',return_value=self.now):
            self.assertEqual(w.probe_for_account(local,'first','/fixture/node')['status'],'authenticated')
            for key,value in [('identity_match',False),('composer_available',False),('cleanup_state','unresolved'),('status','logged_out')]:
                old=good[key];good[key]=value
                with self.assertRaises(w.PreflightNoSend):w.probe_for_account(local,'first','/fixture/node')
                good[key]=old
            good['timestamp']=datetime.fromtimestamp(self.now-61,timezone.utc).isoformat()
            with self.assertRaises(w.PreflightNoSend):w.probe_for_account(local,'first','/fixture/node')

    def test_changed_schedule_blocks_before_any_shared_claim(self):
        from modules.recurring_worker import RecurringWorker
        p=self.root/'worker-schedule.json';p.write_text(json.dumps(dict(self.config,schema_version=1)));p.chmod(0o600)
        pin=hashlib.sha256(p.read_bytes()).hexdigest()
        rpc=mock.Mock()
        worker=RecurringWorker(dict(self.config,schema_version=1),pin,'mac',rpc=rpc,schedule_path=p)
        p.write_text('{}')
        self.assertEqual(worker.run_account('first')['reason'],'schedule_changed_hold')
        rpc.assert_not_called()


    def test_historical_hold_survives_original_tmp_path_disappearing(self):
        original=Path(self.accounts[2]['historical_ledger'])
        before=original.read_bytes()
        backup=self.state/'historical'/'third.json'
        self.assertEqual(backup.read_bytes(),before)
        self.assertEqual(backup.stat().st_mode&0o777,0o400)
        original.unlink()
        self.assertEqual(self.claim(account='third',now=38400)['reason'],'historical_pending_hold')
        self.assertEqual(self.claim(account='second',now=37200)['status'],'admitted')

    def test_mac_calendar_accounts_for_non_whole_hour_timezone(self):
        from modules.recurring_worker import service_definitions
        import plistlib
        files=service_definitions('/usr/bin/python3','/fixture/worker.py','/fixture/schedule.json','a'*64,mac_utc_offset_minutes=345)
        self.assertEqual(plistlib.loads(files['mac_plist'].encode())['StartCalendarInterval'],{'Minute':45})

if __name__=='__main__':unittest.main()
