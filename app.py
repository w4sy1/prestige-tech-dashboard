from pathlib import Path
import sys
from launcher import CATALOG,launch,menu,resolve,tools
from runtime import entry,parser

def build():
    p=parser('Launcher Prestige Tech. Bez argumentów otwiera polskie menu.')
    p.add_argument('--tools-root',default=str(Path(__file__).resolve().parent.parent))
    p.add_argument('--list',action='store_true');p.add_argument('--tool',choices=tools())
    p.add_argument('arguments',nargs='*')
    return p

def handle(a):
    if a.list:
        rows=[]
        for tool in tools():
            try:resolve(a.tools_root,tool);available=True
            except (OSError,ValueError):available=False
            rows.append({'tool':tool,'available':available})
        return rows
    if a.tool:
        code=launch(a.tools_root,a.tool,a.arguments)
        return {'exit_code':code,'ok':code==0}
    return {'exit_code':menu(a.tools_root)}

if __name__=='__main__':
    try:sys.exit(entry(build,handle))
    except (KeyboardInterrupt,EOFError):sys.exit(130)
