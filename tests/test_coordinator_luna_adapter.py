import json, os, pathlib, subprocess, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1] / '.claude/skills/agy-dot-coordinator/scripts'
class AdapterContract(unittest.TestCase):
 def run_adapter(self, args, code=0):
  with tempfile.TemporaryDirectory(prefix='dot-adapter-test-',dir='/tmp') as d:
   stub=pathlib.Path(d)/'pi'
   stub.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit('+str(code)+')\n');stub.chmod(0o700)
   return subprocess.run(['bash',str(ROOT/'pi-codex-luna-adapter.sh'),*args],env={**os.environ,'PATH':d+os.pathsep+os.environ['PATH']},capture_output=True,text=True)
 def test_launcher_contract_forwarded_without_reencoding(self):
  args=['--print','--no-session','--approve','--no-extensions','-e','builtin:mcp','--no-skills','--skill','/tmp/a skill.md','--tools','read,bash,edit,write,mcp__dot_browser__*','Owner task\nExact payload: $HOME `no execution`']
  r=self.run_adapter(args);self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout),['--provider','openai-codex','--model','gpt-6-luna','--thinking','medium',*args])
 def test_no_provider_fallback_on_failure(self):
  self.assertEqual(self.run_adapter(['task'],23).returncode,23)
if __name__=='__main__':unittest.main()
