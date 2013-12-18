#!/usr/bin/env python

import os, sys, tarfile, bz2
from io import BytesIO 
from PIL import Image
from shutil import copyfileobj
import patoolib
from tempfile import mkdtemp


extentionByFormat = {
    "JPEG":".jpeg",
    "JPG":".jpg",
    "WEBP":".webp",
    "PNG":".png"
}

def filenameFromPath(path):
    return os.path.splitext(os.path.basename(path))[0]

def getFileList(path):
    fileList = []

    itemList = os.listdir(path)
    for item in itemList:
        currentFile = '%s/%s' % (path,item)
        if os.path.isfile(currentFile) and os.path.splitext(item)[1][1:] in patoolib.ArchiveFormats:
            fileList.append(currentFile)

    fileList.sort()
    return fileList

def unpackArchive(path):
    tmpDir = mkdtemp()
    patoolib.extract_archive(path,outdir=tmpDir)
    return tmpDir

def convertArchive(path="./",imageFormat="JPEG", resize=None):
    workingDirectoryList = []

    #os.fchdir()
    for archivePath in getFileList(path):
        try:
            unpackedPath = unpackArchive(archivePath)
            workingDirectoryList.append((filenameFromPath(archivePath),unpackedPath))
        except Exception as err:
            print('%s : %s' % ('Error while unpacking archives',err))


    for workingDirInfo in workingDirectoryList:
        name = workingDirInfo[0]
        workingDir = workingDirInfo[1]

        with tarfile.open('%s/%s-rev.tar' % (os.path.dirname(archivePath),name), "w") as tarFile:
            files = os.listdir(workingDir)
            files.sort()
            for f in files:
                filePath = '%s/%s' % (workingDir,f)
                
                extention = os.path.splitext(f)[1]
                extention = extention.lower()

                if not os.path.isdir(filePath) and extention in extentionByFormat.values():
                    futurFileName = '%s%s' % (os.path.splitext(f)[0],extentionByFormat[imageFormat])

                    #convert and resize
                    im = Image.open(filePath).convert("RGB")

                    if resize[0]:
                        im.thumbnail((int(resize[0]),int(resize[1])), Image.ANTIALIAS)

                    #put in tmpfile
                    tmpFile = BytesIO()
                    im.save(tmpFile, imageFormat, quality=85)
                    tmpFile.seek(0)

                    #put in tar
                    info = tarfile.TarInfo(futurFileName)
                    info.size = len(tmpFile.getbuffer())
                    #info.type = "WEBP"
                    tarFile.addfile(info,tmpFile)
                    tmpFile.close()
                    print("file %s compressed" % futurFileName)
                else:
                    print("file NOT %s compressed" % name)

        #bz2
        '''
        with open('%s.tar' % name, 'rb') as input:
            with bz2.BZ2File('%s.bz2' % name, 'wb', compresslevel=9) as output:
                copyfileobj(input, output)
        '''
