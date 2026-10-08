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
        self.binding='1'*64
        self.enterContext(mock.patch.object(self.m,'authority_host_matches',return_value=True,create=True))
        self.ledger=self.m.SharedLedger(self.config,self.binding)
        self.ledger.initialize()

    def claim(self,role='mac',account='first',now=None):
        return self.ledger.apply({'action':'claim','role':role,'account':account},now=self.now if now is None else now)

    def finish(self,claim,outcome='delivered',verified=True):
        return self.ledger.apply({'action':'finish','role':claim['role'],'account':claim['account'],'token':claim['token'],'event_id':claim['event_id'],'result':{'outcome':outcome,'delivery_verified':verified}},now=self.now+10)

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
        self.now=37200
        self.assertEqual(worker.run_account('second')['status'],'recorded')
        self.now=38400
        self.assertEqual(worker.run_account('third')['reason'],'historical_pending_hold')
        self.assertEqual(calls,['first','second'])

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
