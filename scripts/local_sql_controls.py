"""Trusted SQL limit and authorization probes, executed only in the local verifier."""
import json
from pathlib import Path
import subprocess
import sys
import time
base=Path('/tests')
worker=base/'workpaperbench/workflow_sql_worker.py'
db=base/'data.sqlite'
checks={}
queries={
 'time':"WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<1000000000) SELECT SUM(x) total FROM n",
 'memory':"SELECT length(replace(replace('" + "x"*1000 + "','x','" + "x"*1000 + "'),'x','" + "x"*1000 + "')) size",
 'rows':"WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<101) SELECT x FROM n",
 'cell':"SELECT '" + "x"*2000 + "' large_cell",
 'bytes':"WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<100) SELECT x,'" + "x"*1000 + "' large_cell FROM n",
 'write':"DELETE FROM revenues",
 'attach':"ATTACH '/tmp/forbidden.sqlite' AS other",
 'extension':"SELECT load_extension('/tmp/forbidden')",
 'file':"SELECT readfile('/tests/gold.json')",
}
for name,sql in queries.items():
 start=time.monotonic()
 result=subprocess.run([sys.executable,'-I','-S',str(worker)],input=json.dumps({'db':str(db),'sql':sql}),capture_output=True,text=True,timeout=3)
 checks[name]={'rejected':result.returncode!=0,'seconds':round(time.monotonic()-start,3),'stdout_bytes':len(result.stdout.encode()),'diagnostic':result.stdout[:100]}
 assert checks[name]['rejected'] and checks[name]['seconds']<3 and checks[name]['stdout_bytes']<200, (name,checks[name])
print(json.dumps(checks,indent=2))
