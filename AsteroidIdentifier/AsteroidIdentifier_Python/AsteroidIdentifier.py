import astropy as ast
import os
import requests
import re
from lxml import html
import datetime
from astropy.io import fits
from matplotlib import pyplot as plt
import numpy as np
import sys

def printMessage(message, *args, **kwargs):
    print("--|| message ||-- {}".format(message))

def printWarning(message, *args, **kwargs):
    print("--|| warning ||-- {}".format(message), args = args, kwargs = kwargs)

def createDataLocationFile(newFile = True):
    printMessage("setting up software configuration")

    location = input("Where should the program download data to?\n>>> ")

    file = open("./.config/saveData.txt", "a" if newFile else "w")
    file.write(location)
    file.close()

printMessage("attempting to find existing data")
dataDirectory = None
while True:
    if not os.path.exists("./.config"):
        os.mkdir("./.config")
        createDataLocationFile()
        continue

    if not os.path.exists("./.config/saveData.txt"):
        createDataLocationFile()
        continue

    file = open("./.config/saveData.txt", "r")
    locationFromFile = file.readline()
    file.close()

    if not os.path.exists(locationFromFile):
        createDataLocationFile(newFile = False)
        continue

    dataDirectory = locationFromFile

    break

printMessage("checking for the latest data")

request = requests.get("https://www.schoolsobservatory.org/discover/projects/asteroidwatch/ast_download", stream = True)
htmlTree = html.fromstring(request.text)

# tr[1] is the first element as it is NOT 0 based!
groupName = htmlTree.xpath("//table/tbody/tr[1]/td[1]/b/text()")[0]
observationDate = htmlTree.xpath("//table/tbody/tr[1]/td[3]/text()")[0]
files = htmlTree.xpath("//table/tbody/tr[1]/td[4]/a/@href")

observationSetName = groupName

dataSetDirectory = os.path.join(dataDirectory, observationSetName)
if not os.path.exists(dataSetDirectory):
    printMessage("downloading latest data")

    os.mkdir(dataSetDirectory)

    for file in files:
        fileLink = "https://www.schoolsobservatory.org" + file
        fileName = os.path.split(file)[1]
        filePath = os.path.join(dataSetDirectory, fileName)

        printMessage("downloading file: {}".format(fileName))

        request = requests.get(fileLink, stream = True)

        with open(filePath, "wb") as imageFile:
            for chunk in request.iter_content(chunk_size=1024):
                if chunk:
                    imageFile.write(chunk)

    with open(os.path.join(dataSetDirectory, "AsteroidIdentifier.config"), "a") as configFile:
        configFile.write("group_name={}\n".format(groupName))
        configFile.write("observation_data={}\n".format(observationDate))
        configFile.write("analysed=false\n")

    printMessage("latest data downloaded")


printMessage("selecting the latest data")

observationSets = []
dates = []
for folder in os.listdir(dataDirectory):
    folderPath = os.path.join(dataDirectory, folder)
    if not os.path.isfile(folder) and os.path.exists(os.path.join(folderPath, "AsteroidIdentifier.config")):
        file = open(os.path.join(folderPath, "AsteroidIdentifier.config"), "r")
        lines = file.readlines()
        date = datetime.datetime.strptime(lines[1][:-1].split("=")[1].rsplit(" ", 1)[0], "%Y-%m-%d %H:%M:%S")
        analysed = True if lines[2][:-1].split("=")[1] == "true" else False
        file.close()

        if not analysed:
            dates.append(date)
            observationSets.append(folder)
    
sortedDates = dates.copy()
sortedDates.sort(reverse = True)

if len(sortedDates) == 0:
    printWarning("there were no new data files")
    input("Press enter to exit... ")
    sys.exit()

latestSet = observationSets[dates.index(sortedDates[0])]

printMessage("selected observation set: {}".format(latestSet))

latestSetDirectory = os.path.join(dataDirectory, latestSet)

dataFiles = []
for file in os.listdir(latestSetDirectory):
    if file.endswith("fits"):
        dataFiles.append(os.path.join(latestSetDirectory, file))

# Use astropy to analyse the data
imageFiles = [fits.open(file) for file in dataFiles]
imageData = [file[0].data for file in imageFiles]
for file in imageFiles:
    file.close()

#for image in imageData:
#    plt.imshow(image, cmap = "gray")
#    plt.show()

print(imageData[0].shape)
print(imageData[1].shape)
print(imageData[2].shape)
print(imageData[3].shape)

#plt.imshow((imageData[0] + imageData[1] + imageData[2] + imageData[3]) / 4, cmap = "gray")
#plt.colorbar()
#plt.show()

plt.imshow(imageData[0], cmap = "gray")
plt.colorbar()
plt.show()