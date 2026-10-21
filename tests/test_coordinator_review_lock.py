import fcntl, os, pathlib, subprocess, sys, tempfile, unittest
SCRIPT = pathlib.Path(__file__).resolve().parents[1] / '.claude/skills/agy-dot-coordinator/scripts/review-with-coordinator-lock.py'
class ReviewLock(unittest.TestCase):
 def test_existing_owner_blocks_review(self):
  with tempfile.TemporaryDirectory(dir='/tmp') as d:
   path=pathlib.Path(d)/'lock'
   with path.open('a') as f:
    fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    r=subprocess.run([sys.executable,str(SCRIPT),'--',sys.executable,'-c','raise SystemExit(77)'],env={**os.environ,'COORDINATOR_LOCK_FILE':str(path)},capture_output=True)
    self.assertEqual(r.returncode,2)
 def test_lock_lives_through_exec_and_releases_on_exit(self):
  with tempfile.TemporaryDirectory(dir='/tmp') as d:
   path=pathlib.Path(d)/'lock'; stop=pathlib.Path(d)/'STOP';stop.write_text('operator hold')
   code='import fcntl,sys;f=open(sys.argv[1],"a");\ntry:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)\nexcept BlockingIOError:sys.exit(19)\nsys.exit(99)'
   r=subprocess.run([sys.executable,str(SCRIPT),'--',sys.executable,'-c',code,str(path)],env={**os.environ,'COORDINATOR_LOCK_FILE':str(path)},capture_output=True)
   self.assertEqual(r.returncode,19)
   with path.open('a') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   self.assertEqual(stop.read_text(),'operator hold')
 def test_killed_review_releases_kernel_lock(self):
  with tempfile.TemporaryDirectory(dir='/tmp') as d:
   path=pathlib.Path(d)/'lock'
   p=subprocess.Popen([sys.executable,str(SCRIPT),'--',sys.executable,'-u','-c','import time;print("ready",flush=True);time.sleep(30)'],env={**os.environ,'COORDINATOR_LOCK_FILE':str(path)},stdout=subprocess.PIPE,text=True)
   try:
    self.assertEqual(p.stdout.readline().strip(),'ready')
    with path.open('a') as f:
     with self.assertRaises(BlockingIOError):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    p.kill();p.wait(timeout=5)
    with path.open('a') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   finally:
    if p.poll() is None:p.kill();p.wait(timeout=5)
    p.stdout.close()
if __name__=='__main__':unittest.main()
