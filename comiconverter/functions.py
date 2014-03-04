#!/usr/bin/env python

import os, sys, tarfile, bz2, shutil
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

def getExtention(fileName):
    return os.path.splitext(fileName)[1].lower()

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

def convertFile(origin,imageFormat,resize):
    try:
        im = Image.open(origin).convert("RGB")

        if resize[0]:
            im.thumbnail((int(resize[0]),int(resize[1])), Image.ANTIALIAS)

        tmpFile = BytesIO()
        im.save(tmpFile, imageFormat, quality=85)
        tmpFile.seek(0)

        return tmpFile
    except Exception as e:
        print("---- error occured while converting: %s" % origin)
        print("------ %s" % e)
        return None


def convertArchive(workingDir, destFile, imageFormat="JPEG", resize=None):
    print("--- converting to %s %s: %s" % (imageFormat, resize, destFile))

    with tarfile.open(destFile, "w") as tarFile:
        for dirName, subdirList, fileList in os.walk(workingDir):
            for fileName in fileList:

                filePath = os.path.join(dirName,fileName)

                futurFileName = '%s%s' % (os.path.splitext(fileName)[0],extentionByFormat[imageFormat])

                if getExtention(fileName) in extentionByFormat.values():
                    #print("---- converting %s" % filePath)
                    print("---- to %s" % futurFileName)

                    tmpFile = convertFile(filePath,imageFormat,resize)

                    if tmpFile:

                        if dirName != workingDir:
                            subdirectory = dirName.replace(workingDir+"/","")
                            futurFileName = "%s/%s" % (subdirectory,futurFileName)

                        info = tarfile.TarInfo(futurFileName)
                        info.size = len(tmpFile.getbuffer())
                        tarFile.addfile(info,tmpFile)
                        tmpFile.close()
                        #print("------ %s converted" % futurFileName)



def launch(path="./",imageFormat="JPEG", resize=None):
    root_dir = os.getcwd()
    for dirName, subdirList, fileList in os.walk(path):
        print("working in: %s" % dirName)

        for fileName in fileList:
            if getExtention(fileName).replace(".","") in patoolib.ArchiveFormats:
                print("- Unpacking: %s" % fileName)
                filePath = os.path.join(root_dir,dirName,fileName)
                unpackedArchive = unpackArchive(filePath)

                newTarFileName = "%s.tar" % os.path.splitext(filePath)[0]
                convertArchive(unpackedArchive,newTarFileName, imageFormat, resize)
                shutil.rmtree(unpackedArchive)
                print("- Finished: %s" % newTarFileName)
            else:
                print("%s is not a supported archive" % fileName)




# def convertArchive(path="./",imageFormat="JPEG", resize=None):
#     workingDirectoryList = []

#     #os.fchdir()
#     for archivePath in getFileList(path):
#         try:
#             unpackedPath = unpackArchive(archivePath)
#             workingDirectoryList.append((filenameFromPath(archivePath),unpackedPath))
#         except Exception as err:
#             print('%s : %s' % ('Error while unpacking archives',err))


#     for workingDirInfo in workingDirectoryList:
#         name = workingDirInfo[0]
#         workingDir = workingDirInfo[1]

#         with tarfile.open('%s/%s-rev.tar' % (os.path.dirname(archivePath),name), "w") as tarFile:
#             files = os.listdir(workingDir)
#             files.sort()
#             for f in files:
#                 filePath = '%s/%s' % (workingDir,f)
                
#                 extention = os.path.splitext(f)[1]
#                 extention = extention.lower()

#                 if not os.path.isdir(filePath) and extention in extentionByFormat.values():
#                     futurFileName = '%s%s' % (os.path.splitext(f)[0],extentionByFormat[imageFormat])

#                     #convert and resize
#                     im = Image.open(filePath).convert("RGB")

#                     if resize[0]:
#                         im.thumbnail((int(resize[0]),int(resize[1])), Image.ANTIALIAS)

#                     #put in tmpfile
#                     tmpFile = BytesIO()
#                     im.save(tmpFile, imageFormat, quality=85)
#                     tmpFile.seek(0)

#                     #put in tar
#                     info = tarfile.TarInfo(futurFileName)
#                     info.size = len(tmpFile.getbuffer())
#                     #info.type = "WEBP"
#                     tarFile.addfile(info,tmpFile)
#                     tmpFile.close()
#                     print("file %s compressed" % futurFileName)
#                 else:
#                     print("file NOT %s compressed" % name)

#         shutil.rmtree(workingDir)

#         #bz2
#         '''
#         with open('%s.tar' % name, 'rb') as input:
#             with bz2.BZ2File('%s.bz2' % name, 'wb', compresslevel=9) as output:
#                 copyfileobj(input, output)
#         '''
