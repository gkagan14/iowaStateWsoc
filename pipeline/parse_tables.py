import re,sys
from html.parser import HTMLParser

class T(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.cur=None; self.row=None; self.cell=None; self.depth=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='table':
            self.cur={'id':a.get('id',''),'cls':a.get('class',''),'rows':[]}; self.tables.append(self.cur)
        elif tag=='tr' and self.cur is not None:
            self.row=[]
        elif tag in ('td','th') and self.row is not None:
            self.cell=[]
    def handle_endtag(self,tag):
        if tag=='table' and self.cur is not None:
            self.cur=None
        elif tag=='tr' and self.row is not None:
            self.cur['rows'].append(self.row); self.row=None
        elif tag in ('td','th') and self.cell is not None:
            if self.row is not None: self.row.append(' '.join(''.join(self.cell).split()))
            self.cell=None
    def handle_data(self,d):
        if self.cell is not None: self.cell.append(d)

def tables(path):
    p=T(); p.feed(open(path,encoding='utf-8',errors='ignore').read()); return p.tables

if __name__=='__main__':
    for i,t in enumerate(tables(sys.argv[1])):
        rows=[r for r in t['rows'] if r]
        print(i, t['id'], t['cls'][:40], 'rows',len(rows))
        for r in rows[:3]: print('   ',r)
