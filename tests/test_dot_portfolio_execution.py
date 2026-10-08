import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.claude/skills/dot-portfolio-coordinator/scripts'))


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT/'.claude/skills/dot-portfolio-coordinator/scripts/modules/decision_execution.py').is_file(), 'decision-only execution profile is absent')
        self.module = importlib.import_module('modules.decision_execution')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.native = self.root/'claude'
        self.native.write_bytes(b'\x7fELFsynthetic native fixture')
        self.native.chmod(0o700)
        self.dot = self.root/'dot.sh'
        self.dot.write_text('# synthetic transport\n')
        self.chrome = self.root/'dot_chrome.mjs'
        self.chrome.write_text('// synthetic browser transport\n')
        self.calls = []
        self.enterContext(mock.patch.dict(os.environ, {'DOT_NODE': str(self.native)}))

    def resolve(self, auth=None, help_text=None):
        def run(argv, **kwargs):
            self.calls.append((argv, kwargs))
            if '--help' in argv:
                return 0, help_text if help_text is not None else ' '.join(self.module.REQUIRED_FLAGS), ''
            return 0, json.dumps(auth or {'loggedIn': True, 'authMethod': 'claude.ai',
                'apiProvider': 'firstParty', 'subscriptionType': 'max'}), ''
        with mock.patch.object(self.module, 'run_bounded_command', side_effect=run):
            return self.module.resolve_decision_profile('claude', str(self.native))

    def test_supported_native_subscription_profile_has_no_tools(self):
        profile = self.resolve()
        args = profile['args']
        self.assertEqual(args[args.index('--tools')+1], '')
        self.assertEqual(args[args.index('--permission-mode')+1], 'dontAsk')
        self.assertEqual(args[args.index('--permission-prompts')+1], 'none')
        self.assertEqual(json.loads(args[args.index('--mcp-config')+1]), {'mcpServers': {}})
        self.assertIn('--restricted', args)
        self.assertIn('--safe-mode', args)
        self.assertNotIn('--dangerously-skip-permissions', args)
        self.assertNotIn('--yolo', args)
        self.assertTrue(self.module.profile_unchanged(profile))
        self.assertEqual(len(self.calls), 2)

    def test_unsupported_driver_never_runs_even_help(self):
        with mock.patch.object(self.module, 'run_bounded_command') as run:
            for driver in ('agy', 'codex'):
                with self.assertRaisesRegex(ValueError, 'capability_blocked'):
                    self.module.resolve_decision_profile(driver, str(self.native))
            run.assert_not_called()

    def test_script_launcher_missing_flags_and_paid_auth_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'capability_blocked'):
            self.resolve(help_text='--tools --output-format')
        for auth in ({'loggedIn':False}, {'loggedIn':True,'authMethod':'api_key'},
                     {'loggedIn':True,'authMethod':'claude.ai','apiProvider':'bedrock','subscriptionType':'max'}):
            with self.subTest(auth=auth), self.assertRaisesRegex(ValueError, 'subscription_auth_required'):
                self.resolve(auth=auth)
        self.native.write_text('#!/bin/sh\nexit 0\n')
        with self.assertRaisesRegex(ValueError, 'native_executable_required'):
            self.resolve()

    def test_model_environment_excludes_injected_tools_and_paid_routes(self):
        env = self.module.decision_environment({'HOME':'/fixture/home','PATH':'/bin',
            'CLAUDE_CODE_OAUTH_TOKEN':'existing-token','ANTHROPIC_API_KEY':'not-allowed',
            'ANTHROPIC_BASE_URL':'https://invalid.example','NODE_OPTIONS':'--require injected',
            'CLAUDE_CODE_PLUGIN_PATH':'injected','DOT_URL':'private','SECRET':'private'})
        self.assertEqual(env, {'HOME':'/fixture/home','PATH':'/bin','CLAUDE_CODE_OAUTH_TOKEN':'existing-token'})

    def test_dependency_binding_changes_for_transport_bytes_path_and_driver(self):
        profile = self.resolve()
        first = self.module.execution_dependencies(profile, str(self.dot))
        self.assertEqual(first, self.module.execution_dependencies(profile, str(self.dot)))
        self.chrome.write_text('// changed\n')
        self.assertNotEqual(first, self.module.execution_dependencies(profile, str(self.dot)))
        self.chrome.write_text('// synthetic browser transport\n')
        alternate = self.root/'other.sh'
        alternate.write_bytes(self.dot.read_bytes())
        self.assertNotEqual(first, self.module.execution_dependencies(profile, str(alternate)))
        self.native.write_bytes(b'\x7fELFchanged native fixture')
        self.assertFalse(self.module.profile_unchanged(profile))
        with self.assertRaisesRegex(ValueError, 'execution_dependency_changed'):
            self.module.execution_dependencies(profile, str(self.dot))

    def test_missing_dependency_is_not_silently_omitted(self):
        profile = self.resolve()
        self.chrome.unlink()
        with self.assertRaises(ValueError):
            self.module.execution_dependencies(profile, str(self.dot))

    def test_adapter_blocks_unsupported_driver_before_child_invocation(self):
        from modules.driver_adapter import DriverAdapter
        from test_dot_portfolio_coordinator_driver_adapter import TestDriverAdapter
        packet = TestDriverAdapter()._schema_v1_packet()
        with mock.patch('modules.driver_adapter.shutil.which', return_value=str(self.native)), mock.patch('modules.driver_adapter.run_bounded_command') as run:
            result = DriverAdapter('agy').decide(packet, self.root)
        self.assertEqual(result, {'status':'driver_failed','reason':'capability_blocked'})
        run.assert_not_called()

    def test_adapter_uses_private_separate_cwd_stdin_and_no_tools(self):
        from modules.driver_adapter import DriverAdapter
        from test_dot_portfolio_coordinator_driver_adapter import TestDriverAdapter
        fixture = TestDriverAdapter()
        packet = fixture._schema_v1_packet()
        decision = fixture._schema_v1_decision(packet)
        profile = self.resolve()
        workspace = self.root/'ledgers'
        workspace.mkdir()
        (workspace/'hold.json').write_text('private sentinel')
        def run(argv, **kwargs):
            self.assertIn('--tools',argv)
            self.assertEqual(argv[argv.index('--tools')+1],'')
            self.assertNotIn('--dangerously-skip-permissions',argv)
            self.assertFalse(any(arg.startswith('@') for arg in argv))
            self.assertNotEqual(Path(kwargs['cwd']),workspace)
            self.assertNotIn(workspace,Path(kwargs['cwd']).parents)
            self.assertEqual(Path(kwargs['cwd']).stat().st_mode&0o777,0o700)
            self.assertIn('Packet JSON:',kwargs['input_text'])
            return 0,json.dumps({'type':'result','subtype':'success','is_error':False,'result':json.dumps(decision)}),''
        with mock.patch('modules.driver_adapter.shutil.which',return_value=str(self.native)), mock.patch('modules.model_admission.ModelAdmissionChecker.admit_decision_driver',return_value=profile,create=True), mock.patch('modules.driver_adapter.run_bounded_command',side_effect=run):
            result=DriverAdapter('claude').decide(packet,workspace)
        self.assertEqual(result,{'status':'ok','decision':decision})

    def test_driver_symlink_retarget_detected_even_with_identical_bytes(self):
        target = self.native
        link = self.root/'alias'
        link.symlink_to(target)
        self.native = link
        profile = self.resolve()
        other = self.root/'other-native'
        other.write_bytes(target.read_bytes()); other.chmod(0o700)
        link.unlink(); link.symlink_to(other)
        self.assertFalse(self.module.profile_unchanged(profile))

    def test_restart_binding_covers_execution_and_preserves_deadline(self):
        from test_dot_portfolio_coordinator_observe import coordinator_portfolio as cli
        first = cli.run_binding({'a':'b'}, 'registry', 'pilot', 'claude', {'transport':'old'})
        self.assertNotEqual(first, cli.run_binding({'a':'b'}, 'registry', 'pilot', 'claude', {'transport':'new'}))
        state = cli.load_run_state(self.root, first, 1200, 1000)
        self.assertEqual(cli.load_run_state(self.root, first, 1200, 1500)['started_at_epoch'], 1000)
        with self.assertRaisesRegex(ValueError, 'binding_or_schema'):
            cli.load_run_state(self.root, cli.run_binding({'a':'b'}, 'registry', 'pilot', 'claude', {'transport':'new'}), 1200, 1500)

    def test_manifest_reads_fail_closed_and_includes_mjs(self):
        from test_dot_portfolio_coordinator_observe import coordinator_portfolio as cli
        self.assertIn('dot_chrome.mjs', cli.compute_dir_manifest(self.root))
        broken = self.root/'missing.py'; broken.symlink_to(self.root/'absent')
        with self.assertRaises(OSError): cli.compute_dir_manifest(self.root)

    def test_execution_drift_prevents_driver_and_sender(self):
        from test_dot_portfolio_coordinator_pilot import RecurringPilotTests, cli
        fixture = RecurringPilotTests(); fixture.setUp()
        try:
            with mock.patch('modules.driver_adapter.DriverAdapter.decide') as decide:
                result = cli.run_pilot_slot(fixture.config, fixture.slots[0], fixture.state,
                    fixture.snapshot, fixture.root, 'agy', str(fixture.transport), 10**15,
                    source_receipt_reader=fixture.source_reader,
                    execution_guard=lambda: False)
                self.assertEqual(result['reason'], 'execution_dependency_changed')
                decide.assert_not_called(); fixture.send.assert_not_called()
        finally: fixture.doCleanups()

    def test_adapter_rejects_profile_changed_since_controller_admission(self):
        from modules.driver_adapter import DriverAdapter
        from test_dot_portfolio_coordinator_driver_adapter import TestDriverAdapter
        profile = self.resolve()
        expected = dict(profile, version='different-profile')
        with mock.patch('modules.driver_adapter.shutil.which',return_value=str(self.native)), mock.patch('modules.model_admission.ModelAdmissionChecker.admit_decision_driver',return_value=profile), mock.patch('modules.driver_adapter.run_bounded_command') as run:
            result = DriverAdapter('claude').decide(TestDriverAdapter()._schema_v1_packet(),self.root,expected_profile=expected)
            self.assertEqual(result['reason'],'execution_dependency_changed'); run.assert_not_called()

    def test_node_replacement_changes_restart_dependency(self):
        profile = self.resolve()
        first = self.module.execution_dependencies(profile, str(self.dot))
        other = self.root/'node-other'; other.write_bytes(self.native.read_bytes()); other.chmod(0o700)
        with mock.patch.dict(os.environ, {'DOT_NODE': str(other)}):
            self.assertNotEqual(first, self.module.execution_dependencies(profile, str(self.dot)))

    def test_drift_during_model_does_not_launch_transport(self):
        from test_dot_portfolio_coordinator_pilot import RecurringPilotTests, cli
        fixture = RecurringPilotTests(); fixture.setUp()
        try:
            guard = mock.Mock(side_effect=[True, True, False])
            result = cli.run_pilot_slot(fixture.config, fixture.slots[0], fixture.state,
                fixture.snapshot, fixture.root, 'agy', str(fixture.transport), 10**15,
                source_receipt_reader=fixture.source_reader, execution_guard=guard)
            self.assertEqual(result['reason'], 'execution_dependency_changed')
            fixture.send.assert_not_called()
        finally: fixture.doCleanups()

    def test_drift_after_prepare_never_commits_and_retains_uncertain_hold(self):
        from test_dot_portfolio_coordinator_pilot import RecurringPilotTests, cli
        fixture = RecurringPilotTests(); fixture.setUp()
        try:
            guard = mock.Mock(side_effect=[True, True, True, False])
            result = cli.run_pilot_slot(fixture.config, fixture.slots[0], fixture.state,
                fixture.snapshot, fixture.root, 'agy', str(fixture.transport), 10**15,
                source_receipt_reader=fixture.source_reader, execution_guard=guard)
            self.assertFalse(result['delivery_verified'])
            self.assertFalse(fixture.capture.exists())
            self.assertEqual(guard.call_count, 4)
            ledger = json.loads((fixture.root/'sender-0/account_first.json').read_text())
            self.assertIsNotNone(ledger['pending_delivery'])
        finally: fixture.doCleanups()

    def test_node_bytes_change_dependency_even_when_path_is_unchanged(self):
        profile = self.resolve()
        node = self.root/'node'; node.write_bytes(b'\x7fELFfirst'); node.chmod(0o700)
        with mock.patch.dict(os.environ, {'DOT_NODE': str(node)}):
            first = self.module.execution_dependencies(profile,str(self.dot))
            node.write_bytes(b'\x7fELFsecond')
            self.assertNotEqual(first,self.module.execution_dependencies(profile,str(self.dot)))

    def test_sender_removes_interpreter_preloads_and_restores_parent(self):
        from test_dot_portfolio_coordinator_observe import coordinator_portfolio as cli
        controls = {'NODE_OPTIONS':'--require /fixture/preload.js', 'BASH_ENV':'/fixture/shell', 'ENV':'/fixture/shell'}
        def send(argv, **kwargs):
            for key in controls: self.assertFalse(key in os.environ, "interpreter preload inherited")
            self.assertEqual(os.environ['DOT_NODE'],'/fixture/pinned-node')
            print('COORDINATOR_RESULT '+json.dumps({'outcome':'delivered','delivery_verified':True}))
            return 0
        with mock.patch.dict(os.environ,controls), mock.patch('modules.sender.run_sender_cli',side_effect=send):
            self.assertTrue(cli.call_sender([], 'event', 'message',node_path='/fixture/pinned-node')['delivery_verified'])
            for key,value in controls.items(): self.assertEqual(os.environ[key],value)


if __name__ == '__main__': unittest.main()
