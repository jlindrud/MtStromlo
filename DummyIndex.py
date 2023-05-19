
# Write out a dummy HTML file.

html = '''\
<html>
<head>
</head>
<body>
Brought to you courtesy of DummyIndex.py!
</body>
</html>
'''

with open('index.html', 'w') as fout:
    fout.write(html)


