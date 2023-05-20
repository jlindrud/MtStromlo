
import os
import sys
import datetime
from bs4 import BeautifulSoup

# Write out a dummy HTML file.

print('Runnning Python from: {}'.format(sys.executable))

html = '''\
<html>
<head>
</head>
<body>
<p>
From the "docs" folder - brought to you courtesy of DummyIndex.py!
</p>
<p>
Current date and time is: {}
</p>
</body>
</html>
'''

outDir = 'docs'
if not os.path.exists(outDir):
    os.makedirs(outDir)

outFile = os.path.join(outDir, 'index.html')
print('Generating file: {}'.format(outFile))

dtNow = datetime.datetime.now()
with open(outFile, 'w') as fout:
    fout.write(html.format(dtNow))
    
