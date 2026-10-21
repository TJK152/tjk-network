from pathlib import Path
import json, shutil, re, sys
source=Path(__file__).resolve().parents[1]
out=source/'_site'
if out.exists(): shutil.rmtree(out)
out.mkdir()
exclude={'.git','.github','scripts','_site','node_modules','__pycache__'}
for p in source.rglob('*'):
    rel=p.relative_to(source)
    if any(x in exclude or x.startswith('.') for x in rel.parts): continue
    if p.is_file():
        dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
html=[p for p in out.rglob('*.html') if p.name not in ('404.html',) and p != out/'index.html']
base='/' if (out/'CNAME').exists() else '/'+source.name+'/' # override via --base
if len(sys.argv)>1: base=sys.argv[1].rstrip('/')+'/'
route_candidates={}
for p in html:
    rel=p.relative_to(out)
    if p.name=='index.html': route='/'.join(rel.parts[:-1])
    else: route='/'.join([*rel.parts[:-1],p.stem])
    if route: route_candidates.setdefault(route.lower(),rel)
from collections import Counter
counts=Counter(p.stem.lower() for p in html if p.name!='index.html')
for p in html:
    if p.name!='index.html' and counts[p.stem.lower()]==1:
        route_candidates.setdefault(p.stem.lower(),p.relative_to(out))
created={};skipped={}
for route,rel in sorted(route_candidates.items()):
    target=out/route/'index.html'
    if target.exists() or (out/route).is_file():
        skipped[route]='already exists';continue
    original=(out/rel).read_text(encoding='utf-8')
    directory='/'.join(rel.parts[:-1]); original_base=base+(directory+'/' if directory else '')
    # The base element preserves relative JS/CSS/images/fetch paths of original HTML.
    injection='<base href="'+original_base+'">'
    if re.search(r'<base\s',original,re.I):
        # Preserve explicitly defined base rather than override it.
        injection=''
    if re.search(r'<head\b[^>]*>',original,re.I):
        original=re.sub(r'(<head\b[^>]*>)',lambda m:m.group(1)+'\n    '+injection,original,count=1,flags=re.I)
    elif injection:
        original=injection+'\n'+original
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(original,encoding='utf-8')
    created[route]=rel.as_posix()
(out/'routes.json').write_text(json.dumps(created,indent=2)+'\n')
print('Generated',len(created),'clean pages; skipped',skipped,'base',base)
