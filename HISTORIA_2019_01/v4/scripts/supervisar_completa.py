import argparse,json,time,urllib.request
from pathlib import Path
from supervisar import supervise
p=argparse.ArgumentParser();p.add_argument('--deadline',type=float,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('cmd',nargs=argparse.REMAINDER);a=p.parse_args()
r=supervise(a.cmd,a.deadline,a.output);print(r,flush=True)
time.sleep(60)
try:
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
 with urllib.request.urlopen(req,timeout=10) as response:token=json.load(response)['access_token']
 url='https://compute.googleapis.com/compute/v1/projects/proj-uba-261002122233861/zones/northamerica-northeast2-b/instances/clari-c1-fundados/stop'
 req=urllib.request.Request(url,data=b'',headers={'Authorization':'Bearer '+token},method='POST')
 with urllib.request.urlopen(req,timeout=20) as response:result=json.load(response)
 (a.output/'shutdown_request.json').write_text(json.dumps({'status':'REQUESTED','operation':result.get('name')}))
except Exception as e:
 (a.output/'shutdown_request.json').write_text(json.dumps({'status':'FALLBACK_PROVIDER_16H','error_type':type(e).__name__}))
