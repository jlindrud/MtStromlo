
import os
import sys
import datetime
import shutil
import argparse
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

parser = argparse.ArgumentParser(description='Retrieve web cam pictures from Mt Stromlo.')
parser.add_argument('-d', '--dir', type=str, dest='localFolder', required=True, help='Local folder to save files to.')
parser.add_argument('-u', '--url', type=str, dest='url', help='Url of webcam page', default='https://ozforecast.com.au/cgi-bin/weatherstation.cgi?station=11550&animate=10')
args = parser.parse_args()
localFolder = args.localFolder
url = args.url

scriptDir = os.path.split( os.path.realpath(__file__) )[0]
templateFile = os.path.join(scriptDir, 'PageTemplate.html')
indexTemplateFile = os.path.join(scriptDir, 'IndexTemplate.html')
cssFile = os.path.join(scriptDir, 'MtStromloScraper.css')
indexFile = os.path.join(localFolder, 'index.html')

print('Script dir: {}'.format(scriptDir))
print('Template file: {}'.format(templateFile))

def doDownload(url, localFolder):

    print('*** Downloading to directory: {}'.format(localFolder))
    print('*** Downloading from URL: {}'.format(url))

    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')

    #f = open('C:\\MtStromloScraper\\MtStromloScraper.html', 'r')
    #content = f.read()
    #f.close()
    #soup = BeautifulSoup(content, 'html.parser')


    downloadCount = 0

    imgDivs = soup.find_all('div', class_='webcamimg')
    for imgDiv in imgDivs:
        img = imgDiv.find('img')
        imgSrc = img.get('src')
        imgUrl = 'https://ozforecast.com.au' + imgSrc
        imgName = os.path.split(imgUrl)[1]
        localFile = os.path.join(localFolder, imgName)
        imgTime = localFile.split('-')[-1][:6]
        if imgTime < '050000' or imgTime > '190000':
            print('Skipping (time out of range): {}'.format(localFile))
        elif not os.path.exists(localFile):
            # Download it.
            print('* Downloading: ' + localFile)
            r = requests.get(imgUrl, stream=True, verify=False)
            if r.status_code == 200:
                with open(localFile,'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                fileSize = os.path.getsize(localFile)/1000.0
                print('File downloaded OK. Size: {} kb'.format(fileSize))
                downloadCount += 1
            else:
                print('Failed to download: ' + localFile)
                print('Response status: {}'.format(r.status_code))

    print('*** Downloaded {} new files.'.format(downloadCount))


def doDeleteOldFiles(localFolder):
    dtNow = datetime.datetime.now()
    dtCutoff = dtNow + datetime.timedelta(days=-5)
    strCutoff = dtCutoff.strftime('%Y%m%d')
    print('*** Deleting images older than : {}'.format(strCutoff))
    deletedFileCount = 0
    files = Path(localFolder).glob('*.jpg')
    for file in files:
        imgFileName = os.path.split(file)[1]
        imgDate = imgFileName.split('-')[1]        
        if imgDate < strCutoff:
            print('Deleting old file: {}'.format(file))
            os.remove(file)
            deletedFileCount += 1
    print('*** Deleted {} files.'.format(deletedFileCount))

def makeImgPageName(imgDate, imgHour):
    return imgDate + '-' + imgHour + '00.html'

def generatePage(pageFile, imgDate, imgHour, imgFiles, prevFileName, nextFileName):
    
    # Grab the file names for this (date, hour) group.
    fileNames = imgFiles[(imgDate, imgHour)]
    
    # Use the template to write out the page.
    with open(templateFile, 'r') as fin:
        with open(pageFile, 'w') as fout:
            for line in fin.readlines():
            
                if 'GENERATED_IMAGE_LIST' in line:
                    idx = 1
                    for fileName in fileNames:
                        timeStamp =  (os.path.splitext(fileName)[0]).split('-')[-1]
                        timeStamp = timeStamp[0:2] + ':' + timeStamp[2:4] + ':' + timeStamp[4:6]
                        fileTime = imgDate[:4] + '-' + imgDate[4:6] + '-' + imgDate[6:8] + ' ' + timeStamp
                        fout.write('  {{"name":"img{}", "src":"https://www.deltavsoft.com/MtStromlo/{}", "time":"{}"}},\n'.format(idx, fileName, fileTime))
                        idx += 1
                elif 'GENERATED_PREV_BUTTON' in line:
                    fout.write('''<button onclick="window.location='{}';">&lt;&lt; Previous</button>'''.format(prevFileName))
                elif 'GENERATED_NEXT_BUTTON' in line:
                    fout.write('''<button onclick="window.location='{}';">Next &gt;&gt;</button>'''.format(nextFileName))
                else:
                    fout.write(line)

    print('Generated file: {}'.format(pageFile))
    
pageLink = '''
<p>
<table>
<tr>
<td><a href="{0}">{0}</a></td>
<td><img src="{1}" width="100px" height="auto"/></td>
</tr>
</table>
</p>
'''
    
    
def generateIndexPage(imgFiles):

    keyList = list(imgFiles.keys())
    keyList.reverse()

    with open(indexTemplateFile, 'r') as fin:
        with open(indexFile, 'w') as fout:
            for line in fin.readlines():
                if 'GENERATED_INDEX' in line:
                    imgDatePrev = None
                    for (imgDate, imgHour) in keyList:
                    
                        if imgDate != imgDatePrev:
                            fout.write('<hr/>')
                            imgDatePrev = imgDate
                            
                        pageName = makeImgPageName(imgDate, imgHour)
                        thumbnailImg = imgFiles[(imgDate, imgHour)][0]
                        fout.write(pageLink.format(pageName, thumbnailImg))
                else:
                    fout.write(line)
    
    print('Generated file: {}'.format(indexFile))
        

def generatePages(localFolder):

    # Copy the .css file across.
    fromPath = cssFile
    toPath = os.path.join(localFolder, os.path.split(fromPath)[1])
    if os.path.exists(toPath):
        os.remove(toPath);
    shutil.copy(fromPath, toPath)
       
    # Group all image files by (date, hour). We'll make one page for each group.
    files = Path(localFolder).glob('*.jpg')
    fileNames = [os.path.split(file)[1] for file in files]
    fileNames.sort()
    imgFiles = dict()
    for fileName in fileNames:
        
        imgDate = fileName.split('-')[1]        
        imgHour = fileName.split('-')[2][:2]
        
        if (imgDate, imgHour) not in imgFiles.keys():
            imgFiles[(imgDate, imgHour)] = []
        imgFiles[imgDate, imgHour].append(fileName)        
    
    # For each (date, hour) group, generate a web page.
    keyList = list(imgFiles.keys())
    for idx, (imgDate, imgHour) in enumerate(keyList):
        
        # Name of page we are generating.
        pageName = makeImgPageName(imgDate, imgHour)
        pageFile = os.path.join(localFolder, pageName)
        
        # Need to link to the previous page.
        prevFileName = None
        if idx > 0:
            prevFile = keyList[idx-1]
            prevFileName = makeImgPageName(prevFile[0], prevFile[1])
        
        # Need to link to the next page.        
        nextFileName = None
        if idx < len(keyList)-1:
            nextFile = keyList[idx+1]
            nextFileName = makeImgPageName(nextFile[0], nextFile[1])
        
        # TODO: seems unnecessary to regen files that are fully generated already, but maybe it doesn't matter.
        # ...
        
        generatePage(pageFile, imgDate, imgHour, imgFiles, prevFileName, nextFileName)
    
    generateIndexPage(imgFiles)
        
    

# Turn off cert validation.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

doDownload(url, localFolder)
doDeleteOldFiles(localFolder)
generatePages(localFolder)

