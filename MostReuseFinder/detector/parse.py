import os
import re
import subprocess
import tlsh  # Ensure python-tlsh is installed
from tqdm import tqdm
import sys

print("lalal")

# Set global paths
currentPath = os.getcwd()  # Current working directory
clonePath = os.path.join(currentPath, "crown")  # Path to cloned repositories
resultPath = os.path.join(currentPath, "repo_functions")  # Path to store parsing results
ctagsPath = "/usr/bin/ctags"  # Path to the ctags binary

# Create directory for storing parsing results if it doesn't exist
if not os.path.exists(resultPath):
    os.makedirs(resultPath)

def computeTlsh(string):
    string = str.encode(string)
    return tlsh.forcehash(string)

def removeComment(string):
    java_regex = re.compile(
        r'(?P<comment>//.*?$|/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
        re.DOTALL | re.MULTILINE)
    return ''.join([c.group('noncomment') for c in java_regex.finditer(string) if c.group('noncomment')])

def normalize(string):
    return ''.join(string.replace('\n', '').replace('\r', '').replace('\t', '').replace('{', '').replace('}', '').split(' ')).lower()

def hashing(repoPath):
    possible_extensions = (".java")  # Target Java files
    resDict = {}  # Dictionary to store results
    fileCnt = funcCnt = lineCnt = 0  # Counters for files, functions, and lines

    for path, dirs, files in os.walk(repoPath):
        for file in files:
            filePath = os.path.join(path, file)

            if file.endswith(possible_extensions):
                try:
                    # Execute ctags command to extract functions
                    ctags_command = f'ctags -f - --languages=java --fields=neKSt "{filePath}"'
                    functionList = subprocess.check_output(ctags_command, stderr=subprocess.STDOUT, shell=True).decode()

                    # Read file content
                    with open(filePath, 'r', encoding="UTF-8", errors="ignore") as f:
                        lines = f.readlines()

                    # Parse functions from ctags output
                    allFuncs = functionList.split('\n')
                    func_pattern = re.compile(r'(method)')  # Identify methods
                    line_pattern = re.compile(r'(\d+)')  # Identify line numbers

                    for i in allFuncs:
                        elemList = re.sub(r'[\t\s]{2,}', '', i).split('\t')
                        if i and len(elemList) >= 7 and func_pattern.fullmatch(elemList[3]):
                            funcStartLine = int(line_pattern.search(elemList[4]).group(0))
                            funcEndLine = int(line_pattern.search(elemList[6]).group(0))
                            funcBody = ''.join(lines[funcStartLine - 1: funcEndLine])

                            # Remove comments and normalize function body
                            funcBody = removeComment(funcBody)
                            funcBody = normalize(funcBody)

                            # Generate TLSH hash
                            funcHash = computeTlsh(funcBody)
                            if len(funcHash) == 72 and funcHash.startswith("T1"):
                                funcHash = funcHash[2:]  # Remove TLSH prefix for storage

                            storedPath = filePath.replace(repoPath, "")
                            resDict.setdefault(funcHash, []).append(storedPath)
                            funcCnt += 1

                    lineCnt += len(lines)
                    fileCnt += 1

                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] Ctags failed for file {filePath}: {e}")
                except Exception as e:
                    print(f"[ERROR] Unexpected error parsing file {filePath}: {e}")

    return resDict, fileCnt, funcCnt, lineCnt

def indexing(resDict, title, filePath):
    with open(filePath, 'w', encoding='utf-8') as f:
        f.write(title + '\n')  # Write repository details
        for hashval, paths in resDict.items():
            f.write(hashval + '\t' + '\t'.join(paths) + '\n')  # Save hash and associated paths

def parse_repositories():
    for repoName in tqdm(os.listdir(clonePath), desc="Parsing repositories"):
        repoPath = os.path.join(clonePath, repoName)
        if not os.path.isdir(repoPath):
            continue

        print(f"[+] Parsing {repoName}")
        try:
            # Parse the repository
            resDict, fileCnt, funcCnt, lineCnt = hashing(repoPath)
            if resDict:
                repoResultPath = os.path.join(resultPath, repoName)
                os.makedirs(repoResultPath, exist_ok=True)
                title = f"{repoName}\t{fileCnt}\t{funcCnt}\t{lineCnt}"  # Repository details
                resultFilePath = os.path.join(repoResultPath, f"fuzzy_{repoName}.hidx")  # Result file
                indexing(resDict, title, resultFilePath)  # Save results
        except Exception as e:
            print(f"[ERROR] Error processing repository {repoName}: {e}")

if __name__ == "__main__":
    parse_repositories()
