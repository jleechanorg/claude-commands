"""Finite recurring host operations using a single shared account authority."""
import contextlib
import fcntl
import uuid
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from datetime import datetime
import platform
import plistlib
import shlex
import shutil
import socket
import stat
import sys
import tempfile
import time

from modules.decision_execution import execution_dependencies, file_fingerprint
from modules.model_admission import ModelAdmissionChecker
from modules.process_utils import run_bounded_command
from modules.recurring_ledger import PHASES, START_WINDOW, SharedLedger, private_directory, read_private_pinned, due_slot
from modules.sender import _atomic_write, _read_json_file, ACCOUNT_RE

SCRIPTS = Path(__file__).resolve().parent.parent


class PreflightNoSend(Exception):
    """Known failure before any sender or transport could be invoked."""


def controller():
    spec = importlib.util.spec_from_file_location('recurring_controller', SCRIPTS/'coordinator-portfolio.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def batch_start(now, role):
    due = int((now-PHASES[role])//3600)*3600+PHASES[role]
    return due if 0 <= now-due <= START_WINDOW else None


def authority_deadline(claim, rpc_started):
    # Subtract full request/response latency; retries cannot renew fixed expiry.
    now=time.monotonic()
    return now+max(0,claim['deadline_epoch']-claim['authority_epoch']-(now-rpc_started))


def bounded_operation_deadline(claim_deadline,batch_deadline):
    return min(claim_deadline,batch_deadline-120) if batch_deadline is not None else claim_deadline


def validate_service_environment(env):
    if not isinstance(env,dict) or set(env)!={'HOME','PATH'}:raise ValueError('explicit_service_environment_required')
    for value in env.values():
        if not isinstance(value,str) or any(c in value for c in ('\n','\r','\0','%','"','\\')):
            raise ValueError('invalid_service_environment')
    if not Path(env['HOME']).is_absolute() or any(not Path(p).is_absolute() for p in env['PATH'].split(':')):
        raise ValueError('absolute_service_environment_required')
    return env


@contextlib.contextmanager
def service_environment(local):
    env=validate_service_environment(local.get('service_environment'))
    if type(local.get('uid')) is not int or local['uid']!=os.getuid():raise ValueError('service_user_mismatch')
    old={key:os.environ.get(key) for key in env}
    try:
        os.environ.update(env)
        yield
    finally:
        for key,value in old.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value


def source_digest():
    return hashlib.sha256(json.dumps(controller().compute_dir_manifest(SCRIPTS.parent),sort_keys=True).encode()).hexdigest()


@contextlib.contextmanager
def transport_environment(local):
    changes={key:None for key in os.environ if key.startswith(('DOT_','COORDINATOR_','BASH_FUNC_'))}
    changes.update({key:None for key in ('NODE_OPTIONS','NODE_PATH','BASH_ENV','ENV')})
    changes.update({'DOT_CONFIG_FILE':local['dot_config_file'],'DOT_NO_REMOTE':'1'})
    previous={key:os.environ.get(key) for key in changes}
    try:
        for key,value in changes.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
        yield
    finally:
        for key,value in previous.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value


def inspect_execution(local):
    executable=shutil.which(local['driver'])
    if not executable:raise ValueError('driver_unavailable')
    profile=ModelAdmissionChecker.admit_decision_driver(local['driver'],executable)
    with transport_environment(local):
        dependencies=execution_dependencies(profile,local['transport_script'])
    data={'source_digest':source_digest(),'sources':file_fingerprint(local['sources']),
          'dot_config':file_fingerprint(local['dot_config_file']),'execution':dependencies}
    return profile,data,hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()


def probe_for_account(local,account,node,receipt_path=None):
    config=json.loads(Path(local['dot_config_file']).read_text())
    identity=config['accounts'][account]['profile_match']
    if not isinstance(identity,str) or not identity:raise PreflightNoSend('identity_unconfigured')
    expected=hashlib.sha256(identity.encode()).hexdigest()
    with transport_environment(local):
        env=os.environ.copy();env['DOT_NODE']=node
        rc,stdout,_=run_bounded_command([local['transport_script'],'--account',account,'probe',expected],
            cwd='/tmp',timeout_secs=60,env=env)
    if rc or len(stdout)>64000:raise PreflightNoSend('session_probe_failed')
    frames=[json.loads(line[len('DOT_SESSION_PROBE '):]) for line in stdout.splitlines() if line.startswith('DOT_SESSION_PROBE ')]
    if len(frames)!=1 or not isinstance(frames[0],dict):raise PreflightNoSend('session_probe_failed')
    probe=frames[0]
    timestamp=datetime.fromisoformat(probe.get('timestamp','').replace('Z','+00:00')).timestamp()
    if receipt_path is not None:
        safe={'schema_version':1,'observed_epoch':timestamp,
            'status':probe.get('status') if probe.get('status') in ('authenticated','logged_out','challenge','unavailable','unknown') else 'unknown',
            'identity_match':probe.get('identity_match') is True,'composer_available':probe.get('composer_available') is True,
            'endpoint_200':probe.get('endpoint_status')==200,
            'cleanup_resolved':probe.get('cleanup_state') in ('context_closed','browser_disconnected')}
        _atomic_write(str(receipt_path),safe,str(Path(receipt_path).parent))
    if (type(probe.get('schema_version')) is not int or probe['schema_version']!=1 or
            probe.get('status')!='authenticated' or probe.get('identity_match') is not True or
            probe.get('composer_available') is not True or probe.get('endpoint_status')!=200 or
            probe.get('cleanup_state') not in ('context_closed','browser_disconnected') or
            not -5<=time.time()-timestamp<=60):
        raise PreflightNoSend('session_gate_not_ready')
    return probe


class RecurringWorker:
    def __init__(self,config,binding,role,*,rpc=None,schedule_path=None):
        self.config,self.binding,self.role=config,binding,role
        self.rpc=rpc or self.remote_request
        self.schedule_path=schedule_path
        self.claim_deadline=None
        self.batch_deadline=None

    def config_current(self):
        if self.schedule_path is None:return True
        try:return read_private_pinned(self.schedule_path,self.binding)==self.config
        except Exception:return False

    def remote_request(self,request):
        if not self.config_current():raise ValueError('schedule_changed_hold')
        if self.role=='linux':
            return SharedLedger(self.config,self.binding).apply(request)
        authority=self.config['authority_endpoint']
        # Existing SSH alias/authentication only; no fallback to an isolated local ledger.
        command=shlex.join([authority['python'],authority['script'],'--schedule',authority['schedule'],
            '--sha256',self.binding,'broker'])
        rc,stdout,_=run_bounded_command(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','--',
            authority['ssh_host'],command],cwd='/tmp',timeout_secs=20,
            input_text=json.dumps(request)+'\n')
        if rc or len(stdout)>16000:raise ValueError('shared_authority_unavailable')
        reply=json.loads(stdout)
        if not isinstance(reply,dict):raise ValueError('shared_authority_unavailable')
        return reply

    def retry_rpc(self,request):
        # Repeating a request only recovers that handshake; never a new send.
        for _ in range(3):
            try:
                result=self.rpc(request)
                if result.get('reason') not in ('shared_lock_busy','shared_state_unavailable_hold'):
                    return result
            except Exception:
                pass
        raise OSError('shared_authority_unavailable')

    def run_account(self,account,*,recover_only=False):
        if not self.config_current():return {'status':'held','reason':'schedule_changed_hold'}
        if not isinstance(account,str) or not ACCOUNT_RE.fullmatch(account):return {'status':'held','reason':'invalid_account'}
        # One local executor owns an account's durable handshake. Another process
        # cannot replay the same claim into concurrent operation calls.
        root=private_directory(self.config['hosts'][self.role]['state_dir'])
        fd=os.open(root/('rpc-'+account+'.lock'),os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:
                return {'status':'held','reason':'invalid_local_lock'}
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError:return {'status':'held','reason':'local_execution_busy'}
            return self._run_account(account,root,recover_only=recover_only)
        finally:os.close(fd)

    def _run_account(self,account,root,*,recover_only=False):
        path=root/('rpc-'+account+'.json')
        def save(journal):
            if journal['phase'] in ('complete','uncertain'):
                history=private_directory(root/'rpc-history',create=True)
                record=history/(journal['request']['request_id']+'.json')
                prior,reason=_read_json_file(str(record),'journal')
                if prior is not None and prior!=journal:raise ValueError('immutable_journal_conflict')
                if prior is None:
                    if reason!='journal_missing':raise ValueError('journal_history_unavailable')
                    _atomic_write(str(record),journal,str(history))
            _atomic_write(str(path),journal,str(root))
        journal,reason=_read_json_file(str(path),'journal')
        if journal is None and reason!='journal_missing':return {'status':'held','reason':'local_journal_unavailable'}
        if journal is not None and journal.get('binding')!=self.binding:return {'status':'held','reason':'schedule_binding_hold'}
        if journal is None or journal.get('phase')=='complete':
            if recover_only:return {'status':'no_action','reason':'no_unsettled_local_claim'}
            journal={'binding':self.binding,'phase':'claim','request':{'action':'claim','role':self.role,
                     'account':account,'request_id':uuid.uuid4().hex,
                     'due_epoch':due_slot(time.time(),self.role,[a['account'] for a in self.config['accounts']].index(account))}}
            save(journal)  # Identity survives a lost SSH claim reply.
        if journal['phase']=='claim':
            try:
                claim=({'status':'held','reason':'recovery_only'} if recover_only else self.retry_rpc(journal['request']))
            except Exception:claim={'status':'held','reason':'shared_authority_unavailable'}
            if claim.get('status')=='admitted':
                journal.update(phase='claimed',claim=claim);save(journal)
            else:
                try:status=self.retry_rpc({**journal['request'],'action':'status'})
                except Exception:return claim
                if status.get('status')=='not_claimed' and status.get('claim_consumed') is False:
                    journal['phase']='complete';save(journal)
                    return claim
                if status.get('status')=='pending' and isinstance(status.get('claim'),dict):
                    # No local dispatch occurred. Closing this exact claim is
                    # proven no-send even when its delivery deadline has passed.
                    journal.update(phase='finish',claim=status['claim'],
                                   result={'outcome':'no_action','delivery_verified':False});save(journal)
                else:return claim
        claim=journal.get('claim')
        if not isinstance(claim,dict):return {'status':'held','reason':'local_journal_unavailable'}
        if journal['phase']=='claimed' and recover_only:
            journal.update(phase='finish',result={'outcome':'no_action','delivery_verified':False});save(journal)
        if journal['phase']=='claimed':
            started=time.monotonic()
            try:checked=self.retry_rpc({**claim,'action':'check'})
            except Exception:return {'status':'held','reason':'shared_authority_unavailable'}
            if checked.get('status')!='admitted':
                # This worker has not dispatched anything. Expiry/stop is no-send.
                journal.update(phase='finish',result={'outcome':'no_action','delivery_verified':False});save(journal)
            else:self.claim_deadline=bounded_operation_deadline(authority_deadline(checked,started),self.batch_deadline)
        if journal['phase']=='claimed':
            journal['phase']='started';save(journal)
            try:result=self.operation(claim)
            except PreflightNoSend:result={'outcome':'no_action','delivery_verified':False}
            except Exception:result={'outcome':'uncertain','delivery_verified':False}
            journal.update(phase='finish',result=result);save(journal)
        elif journal['phase']=='started':
            # Process loss after dispatch has no proof of no-send. Do not replay.
            return {'status':'held','reason':'local_attempt_uncertain_hold'}
        if journal['phase']=='uncertain':return {'status':'held','reason':'account_pending_hold'}
        if journal['phase']!='finish':return {'status':'held','reason':'local_journal_unavailable'}
        try:
            completion=self.retry_rpc({**claim,'action':'finish','result':journal['result']})
        except Exception:
            try:completion=self.retry_rpc({**claim,'action':'status'})
            except Exception:completion={}
            if completion.get('status')!='recorded' or completion.get('settlement_pending') is not False:
                return {'status':'held','reason':'completion_unacknowledged_hold','event_id':claim['event_id']}
        if completion.get('status')=='recorded':
            journal['phase']='complete' if completion.get('hold_preserved') is False else 'uncertain'
            save(journal)
        return {**completion,'event_id':claim['event_id'],'account':account,'result':journal['result']}

    def operation(self,claim):
        try:
            local=self.config['hosts'][self.role]
            root=private_directory(local['state_dir'])
            if os.path.lexists(root/'STOP'):
                return {'outcome':'no_action','reason':'operator_stop','delivery_verified':False}
            if (socket.gethostname()!=local['hostname'] or
                    platform.system()!=('Darwin' if self.role=='mac' else 'Linux')):
                raise ValueError('host_binding_mismatch')
            profile,pinned,digest=inspect_execution(local)
            if digest!=local['execution_sha256']:raise ValueError('execution_pin_mismatch')
            cli=controller()
            deadline=self.claim_deadline if self.claim_deadline is not None else time.monotonic()+max(0,claim['deadline_epoch']-time.time())
            run=private_directory(root/claim['event_id'],create=True)
            # A prior child directory indicates an interrupted or repeated operation.
            if any(run.iterdir()):
                return {'outcome':'uncertain','reason':'local_event_already_started','delivery_verified':False}
            probe_for_account(local,claim['account'],pinned['execution']['node']['selected_path'],run/'session-probe.json')
            grant={'grant_version':1,'task_id':'dot-coordinator-separated-20261007',
                'account_id':claim['account'],'action':'coordination_message',
                'activated_at_epoch':claim.get('activated_at_epoch',claim['due_epoch']),'expiry_epoch':claim['deadline_epoch'],
                'max_messages':1,'min_interval_secs':3600}
            grant_path=run/'grant.json'
            fd=os.open(grant_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o400)
            os.fchmod(fd,0o400)
            with os.fdopen(fd,'wb') as stream:
                stream.write(json.dumps(grant,sort_keys=True).encode());stream.flush();os.fsync(stream.fileno())
            grant_sha=hashlib.sha256(grant_path.read_bytes()).hexdigest()
            accounts=[{'account':a['account']} for a in self.config['accounts']]
            index=[a['account'] for a in accounts].index(claim['account'])
            accounts[index].update(grant_file=str(grant_path),grant_sha256=grant_sha)
            config={'accounts':accounts,'authority':self.config['authority']}
            sender_root=private_directory(run/'sender',create=True)
        except Exception as error:
            raise PreflightNoSend('preflight_failed') from error
        def guard():
            try:
                if not self.config_current() or os.path.lexists(root/'STOP'):return False
                if source_digest()!=pinned['source_digest']:return False
                if file_fingerprint(local['sources'])!=pinned['sources']:return False
                if file_fingerprint(local['dot_config_file'])!=pinned['dot_config']:return False
                if execution_dependencies(profile,local['transport_script'])!=pinned['execution']:return False
                return self.rpc({**claim,'action':'check'}).get('status')=='admitted'
            except Exception:return False
        with transport_environment(local):
            temp=Path(tempfile.mkdtemp(prefix='dot-recurring-',dir='/tmp'))
            try:
                if not guard():return {'outcome':'no_action','reason':'shared_or_execution_hold','delivery_verified':False}
                registry=cli.SourceRegistry(local['sources'])
                collected=cli.PortfolioCollector(registry,audience='model').collect_all(
                    deadline_mono=min(deadline,time.monotonic()+120))
                snapshot,reader=cli.model_snapshot_and_reader(collected,registry,deadline)
                result=cli.run_pilot_slot(config,{'event_id':claim['event_id'],'account_index':index},
                    {},snapshot,Path(temp),local['driver'],local['transport_script'],deadline,
                    source_receipt_reader=reader,execution_guard=guard,execution_profile=profile,
                    node_path=pinned['execution']['node']['selected_path'],sender_state_dir=sender_root)
                _atomic_write(str(run/'result.json'),dict(result,event_id=claim['event_id'],account=claim['account']),str(run))
                return result
            finally:
                # Retain only bounded existing diagnostic receipts before cleanup.
                # On persistence failure, the private temp directory stays intact.
                for index,path in enumerate(temp.glob('driver-*/.driver-diagnostic-*.json')):
                    with path.open('rb') as stream:raw=stream.read(2049)
                    if len(raw)>2048:raise ValueError('diagnostic_receipt_oversized')
                    _atomic_write(str(run/f'driver-diagnostic-{index}.json'),json.loads(raw),str(run))
                shutil.rmtree(temp)

    def run_batch(self):
        local=self.config['hosts'][self.role]
        root=private_directory(local['state_dir'])
        started=batch_start(time.time(),self.role)
        if started is None:return [{'status':'held','reason':'missed_start_window'}]
        results=[]
        monotonic_deadline=time.monotonic()+3600
        self.batch_deadline=monotonic_deadline
        last_wall=started
        for index,account in enumerate(self.config['accounts']):
            due=started+index*1200
            while True:
                now=time.time()
                if now<last_wall:
                    return results+[{'status':'held','reason':'clock_rollback_hold'}]
                last_wall=now
                if time.monotonic()>=monotonic_deadline:
                    return results+[{'status':'held','reason':'batch_deadline'}]
                if os.path.lexists(root/'STOP'):return results
                if now>=due:break
                time.sleep(min(5,due-now,monotonic_deadline-time.monotonic()))
            if now>due+START_WINDOW:
                results.append({'status':'held','reason':'missed_start_window','account':account['account']})
                continue
            result=self.run_account(account['account']);results.append(result)
            print(json.dumps(result),flush=True)
        return results


def service_definitions(python,script,schedule,binding,*,mac_utc_offset_minutes=0,environments=None):
    for value in (python,script,schedule):
        if not Path(value).is_absolute() or any(c in value for c in ('\n','\r','%')):
            raise ValueError('absolute_service_path_required')
    common=[python,script,'--schedule',schedule,'--sha256',binding]
    mac={'Label':'ai.dot-portfolio-hourly-v1','ProgramArguments':common+['--role','mac','run'],
        'StartCalendarInterval':{'Minute':mac_utc_offset_minutes%60},'RunAtLoad':False,'KeepAlive':False,
        'WorkingDirectory':'/tmp','Umask':0o077,
        'StandardOutPath':str(Path(schedule).parent/'mac-runner.log'),
        'StandardErrorPath':str(Path(schedule).parent/'mac-runner.log')}
    if environments is not None:
        mac['EnvironmentVariables']=validate_service_environment(environments['mac'])
        linux_env=validate_service_environment(environments['linux'])
    else:linux_env=None
    command=shlex.join(common+['--role','linux','run'])
    service='[Unit]\nDescription=Finite hourly dot portfolio operation\n[Service]\nType=oneshot\nUMask=0077\nWorkingDirectory=/tmp\nRuntimeMaxSec=3720\nExecStart='+command+'\n'
    service='# Install as a user unit via systemctl --user; never a system service.\n'+service
    if linux_env is not None:
        service+=''.join('Environment="'+key+'='+value+'"\n' for key,value in linux_env.items())
    timer='[Unit]\nDescription=Staggered hourly dot portfolio trigger\n[Timer]\nOnCalendar=*-*-* *:30:00 UTC\nPersistent=false\nRandomizedDelaySec=0\nAccuracySec=1s\nUnit=dot-portfolio-hourly-v1.service\n[Install]\nWantedBy=timers.target\n'
    return {'mac_plist':plistlib.dumps(mac).decode(),'linux_service':service,'linux_timer':timer}
