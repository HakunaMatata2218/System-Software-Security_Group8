import os
import json
import tlsh
import sys


# Define paths
hash_result_folder = "./repo_functions"  # Path to the folder where hash files are stored
resultPath = "./res/"
finalDBPath = "../preprocessor/componentDB/"
metaPath = "../preprocessor/metaInfos/"
weightPath = metaPath + "weights/"
currentPath = os.getcwd()
theta = 0.0001
repoFuncPath = "../osscollector/repo_functions/"
verIDXpath = "../preprocessor/verIDX/"
initialDBPath = "../preprocessor/initialSigs/"
aveFuncPath = metaPath + "aveFuncs"
ctagsPath = "/usr/bin/ctags"

def readHashResultsFromFile(filePath):
    """
    Read hash values from a single .hidx file.
    """
    resDict = {}
    try:
        # Open and read the file
        with open(filePath, 'r', encoding='utf-8') as f:
            print(f"Successfully opened file: {filePath}")
            for line in f:
                line = line.strip()  # Remove leading/trailing whitespace
                parts = line.split('\t')  # Split by tab
                
                if len(parts) >= 2:
                    hashval = parts[0]  # Hash value
                    paths = parts[1:]  # List of paths
                    
                    # Store the hash and paths in the dictionary
                    if hashval not in resDict:
                        resDict[hashval] = []
                    resDict[hashval].extend(paths)
    except Exception as e:
        print(f"Error reading file {filePath}: {e}")
    else:
        print(f"Finished reading file: {filePath}. Total hashes: {len(resDict)}")
    
    return resDict

def getAveFuncs():
    aveFuncs = {}
    with open(aveFuncPath, 'r', encoding = "UTF-8") as fp:
        aveFuncs = json.load(fp)
    return aveFuncs


def readComponentDB():
    componentDB = {}
    jsonLst 	= []

    for OSS in os.listdir(finalDBPath):
        componentDB[OSS] = []
        with open(finalDBPath + OSS, 'r', encoding = "UTF-8") as fp:
            jsonLst = json.load(fp)
            for eachHash in jsonLst:
                hashval = eachHash["hash"]
                componentDB[OSS].append(hashval)

    return componentDB

def readAllVers(repoName):
    allVerList 	= []
    idx2Ver		= {}

    with open(verIDXpath + repoName + "_idx", 'r', encoding = "UTF-8") as fp:
        tempVerList = json.load(fp)

        for eachVer in tempVerList:
            allVerList.append(eachVer["ver"])
            idx2Ver[eachVer["idx"]] = eachVer["ver"]

    return allVerList, idx2Ver

def readWeigts(repoName):
    weightDict = {}

    with open(weightPath + repoName + "_weights", 'r', encoding = "UTF-8") as fp:
        weightDict = json.load(fp)

    return weightDict


def is_valid_tlsh_hash(hashval):
    """Checks if the given string is a valid TLSH hash"""
    # A valid TLSH hash must have 72 characters and start with "T1"
    return (len(hashval) > 10 and hashval != "TNULL")



def detector(inputDict, inputRepo):
    componentDB = {}
    componentDB = readComponentDB()
    
    # Construct the full file path by appending the file name to resultPath
    file_path = resultPath + "result_filename.txt"
    
    try:
        # Attempt to open the file for writing
        fres = open(file_path, 'a')
        print(f"Successfully opened file: {file_path}")
    except IOError as e:
        # Handle the error (e.g., if the file cannot be opened)
        print(f"Error opening file {file_path}: {e}")
        return  # Exit the function if the file cannot be opened
    
    aveFuncs = getAveFuncs()
    print("Average functions data retrieved.")

    for OSS in componentDB:
        print(f"Processing {OSS}...")
        commonFunc = []  # List to hold the common (reused) functions
        repoName = OSS.split('_sig')[0]  # Extract repository name from OSS identifier
        
        totOSSFuncs = float(aveFuncs[repoName])
        # print(f"Total OSS functions for {repoName}: {totOSSFuncs}")
        
        if totOSSFuncs == 0.0:
            continue  # Skip if no functions are available for comparison
        
        comOSSFuncs = 0.0
        for hashval in componentDB[OSS]:
            if hashval in inputDict:
                commonFunc.append(hashval)
                comOSSFuncs += 1.0
        
        print(f"Reused functions for {repoName}: {comOSSFuncs}")
        
        # Check if reused functions ratio meets the threshold
        if (comOSSFuncs / totOSSFuncs) >= theta:

            verPredictDict = {}
            allVerList, idx2Ver = readAllVers(repoName)

            for eachVersion in allVerList:
                verPredictDict[eachVersion] = 0.0
            weightDict = readWeigts(repoName)

            with open(initialDBPath + OSS, 'r', encoding="UTF-8") as fi:
                jsonLst = json.load(fi)
                for eachHash in jsonLst:
                    hashval = eachHash["hash"]
                    verlist = eachHash["vers"]
                    if hashval in commonFunc:
                        for addedVer in verlist:
                            verPredictDict[idx2Ver[addedVer]] += weightDict.get(hashval, 0)

            sortedByWeight = sorted(verPredictDict.items(), key=lambda x: x[1], reverse=True)
            predictedVer = sortedByWeight[0][0]

            # Read the function data
            predictOSSDict = {}
            with open(repoFuncPath + repoName + '/fuzzy_' + predictedVer + '.hidx', 'r', encoding="UTF-8") as fo:
                body = ''.join(fo.readlines()).strip()
                for eachLine in body.split('\n')[1:]:
                    ohash = eachLine.split('\t')[0]
                    opath = eachLine.split('\t')[1]
                    predictOSSDict[ohash] = opath.split('\t')

            used = 0
            unused = 0
            modified = 0
            strChange = False

            for ohash in predictOSSDict:
                flag = 0  # Flag to track if the hash is processed

                if ohash in inputDict:
                    used += 1
                    nflag = 0
                    
                    # Compare paths to see if there's any change
                    for opath in predictOSSDict[ohash]:
                        for tpath in inputDict[ohash]:
                            if opath in tpath:
                                nflag = 1
                    if nflag == 0:
                        strChange = True
                    flag = 1
                else:
                    for thash in inputDict:
                        if not is_valid_tlsh_hash(thash):
                            # print(f"Skipping invalid 111 hash: {thash}")
                            continue
                        if not is_valid_tlsh_hash(ohash):
                            # print(f"Skipping invalid 222 hash: {ohash}")
                            continue
                        score = tlsh.diffxlen(ohash, thash)
                        if int(score) <= 50:
                            modified += 1
                            nflag = 0
                            for opath in predictOSSDict.get(ohash, []):  # Ensure we check the hash in the dictionary
                                    for tpath in inputDict.get(thash, []):  # Ensure we check the hash in the dictionary
                                        if opath in tpath:
                                            nflag = 1
                            if nflag == 0:
                                strChange = True
                            flag = 1
                            break
                        
                if flag == 0:
                    unused += 1

            print("Writing to file:", [inputRepo, repoName, predictedVer,used, modified, strChange])
            with open(file_path, 'a', encoding='utf-8') as fres:
                fres.write('\t'.join([inputRepo, repoName, str(used), str(modified), str(strChange)]) + '\n')


    fres.close()  # Close the result file after writing


def main(inputFilePath, inputRepo):
    """
    Main function to process a single hash result file and run the detector.
    """
    # Read the hash results from the single file
    resDict = readHashResultsFromFile(inputFilePath)
    print(f"Processing repository: {inputRepo} from file: {inputFilePath}")

    # Call the detector with the hash results and repository name
    detector(resDict, inputRepo)

""" EXECUTE """
if __name__ == "__main__":
    # Get all files in the hash_result_folder
    inputFiles = [f for f in os.listdir(hash_result_folder) if f.endswith('.hidx')]

    # Process each file individually
    for inputFile in inputFiles:
        # Build the full file path
        full_inputFilePath = os.path.join(hash_result_folder, inputFile)

        # Use the file name (without extension) as the repository name
        inputRepo = os.path.splitext(inputFile)[0]

        # Call the main function with the current file path and repo
        print(f"Processing repository: {inputRepo} from file: {full_inputFilePath}")
        main(full_inputFilePath, inputRepo)