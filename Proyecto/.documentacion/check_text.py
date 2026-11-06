from pathlib import Path
from pypdf import PdfReader
import json,re
w=Path('Proyecto/.documentacion');r=PdfReader(w/'final-v3.pdf');texts=[p.extract_text() for p in r.pages]
for i,t in enumerate(texts):
 if len(t)<500:print('LOW',i+1,t[-300:])
