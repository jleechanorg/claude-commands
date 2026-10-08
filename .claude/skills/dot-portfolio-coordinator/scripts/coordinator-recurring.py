#!/usr/bin/env python3
"""Shared admission RPC and finite hourly host worker. Never starts itself."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from modules.recurring_ledger import SharedLedger,load_schedule
from modules.recurring_worker import RecurringWorker,inspect_execution,source_digest,service_definitions
from modules.process_utils import run_bounded_command


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--schedule',required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--role',choices=('mac','linux'))
    parser.add_argument('command',choices=('initialize','broker','inspect','render','run','run-worker'))
    args=parser.parse_args()
    config=load_schedule(args.schedule,args.sha256)
    if args.command=='inspect':
        if not args.role:raise ValueError('role_required')
        _,_,digest=inspect_execution(config['hosts'][args.role])
        print(json.dumps({'execution_sha256':digest,'source_digest':source_digest()}));return
    if args.command=='render':
        print(json.dumps(service_definitions(sys.executable,str(Path(__file__).resolve()),args.schedule,args.sha256,mac_utc_offset_minutes=int(datetime.now().astimezone().utcoffset().total_seconds()/60))));return
    if source_digest()!=config['source_digest']:raise ValueError('source_digest_mismatch')
    if args.command=='initialize':
        SharedLedger(config,args.sha256).initialize()
        print(json.dumps({'status':'initialized'}));return
    if args.command=='broker':
        raw=sys.stdin.buffer.read(4097)
        if len(raw)>4096:raise ValueError('request_too_large')
        request=json.loads(raw)
        if not isinstance(request,dict):raise ValueError('invalid_request')
        print(json.dumps(SharedLedger(config,args.sha256).apply(request)));return
    if not args.role:raise ValueError('role_required')
    if args.command=='run':
        rc,stdout,_=run_bounded_command([sys.executable,str(Path(__file__).resolve()),'--schedule',args.schedule,'--sha256',args.sha256,'--role',args.role,'run-worker'],cwd='/tmp',timeout_secs=3600)
        print(stdout,end='');sys.exit(rc)
    RecurringWorker(config,args.sha256,args.role,schedule_path=args.schedule).run_batch()


if __name__=='__main__':
    try:main()
    except Exception:
        print(json.dumps({'status':'held','reason':'recurring_preflight_failed'}))
        sys.exit(2)
