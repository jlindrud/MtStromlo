
import sys

# Write out a dummy HTML file.

print('Runnning Python from: {}'.format(sys.executable))

html = '''\
<html>
<head>
</head>
<body>
Brought to you courtesy of DummyIndex.py!
</body>
</html>
'''

outFile = 'index.html'
print('Generating file: {}'.format(outFile))

with open(outFile, 'w') as fout:
    fout.write(html)
