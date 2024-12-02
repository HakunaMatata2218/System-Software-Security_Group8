
"""
Dataset Collection Tool.
Author:		Seunghoon Woo (seunghoonwoo@korea.ac.kr)
Modified: 	December 16, 2020.
"""

import os
import sys
import subprocess
import re
import tlsh # Please intall python-tlsh
from tqdm import tqdm

"""GLOBALS"""

currentPath	= os.getcwd()
gitCloneURLS= currentPath + "/github_repos_java" 			# Please change to the correct file (the "sample" file contains only 10 git-clone urls)
clonePath 	= currentPath + "/repo_src/"		# Default path
tagDatePath = currentPath + "/repo_date/"		# Default path
resultPath	= currentPath + "/repo_functions/"	# Default path
ctagsPath	= "/usr/bin/ctags" 			# Ctags binary path (please specify your own ctags path)

# Generate directories
shouldMake = [clonePath, tagDatePath, resultPath]
for eachRepo in shouldMake:
	if not os.path.isdir(eachRepo):
		os.mkdir(eachRepo)


# Generate TLSH
def computeTlsh(string):
	string 	= str.encode(string)
	hs 		= tlsh.forcehash(string)
	return hs


def removeComment(string):
	# Comment format for Java
	java_regex = re.compile(
		r'(?P<comment>//.*?$|/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
		re.DOTALL | re.MULTILINE)
	return ''.join([c.group('noncomment') for c in java_regex.finditer(string) if c.group('noncomment')])

def normalize(string):
	# Format method codes
	return ''.join(string.replace('\n', '').replace('\r', '').replace('\t', '').replace('{', '').replace('}', '').split(' ')).lower()

def hashing(repoPath):
	possible = (".java")

	fileCnt  = 0
	funcCnt  = 0
	lineCnt  = 0

	resDict  = {}

	for path, dir, files in os.walk(repoPath):
		for file in files:
			filePath = os.path.join(path, file)

			if file.endswith(possible):
				try:
					# Execute Ctgas command,Change to java
					functionList 	= subprocess.check_output(ctagsPath + ' -f - --languages=java --fields=neKSt "' + filePath + '"', stderr=subprocess.STDOUT, shell=True).decode()

					f = open(filePath, 'r', encoding = "UTF-8")

					# For parsing functions,Java is method
					lines 		= f.readlines()
					allFuncs 	= str(functionList).split('\n')
					func   		= re.compile(r'(method)')
					number 		= re.compile(r'(\d+)')
					funcSearch	= re.compile(r'{([\S\s]*)}')
					tmpString	= ""
					funcBody	= ""

					fileCnt 	+= 1

					for i in allFuncs:
						elemList	= re.sub(r'[\t\s ]{2,}', '', i)
						elemList 	= elemList.split('\t')
						funcBody 	= ""
						#8 to 7, related to the return value of ctags
						if i != '' and len(elemList) >= 7 and func.fullmatch(elemList[3]):
							funcStartLine 	 = int(number.search(elemList[4]).group(0))
							funcEndLine 	 = int(number.search(elemList[6]).group(0))

							tmpString	= ""
							tmpString	= tmpString.join(lines[funcStartLine - 1 : funcEndLine])

							if funcSearch.search(tmpString):
								funcBody = funcBody + funcSearch.search(tmpString).group(1)
							else:
								funcBody = " "

							funcBody = removeComment(funcBody)
							funcBody = normalize(funcBody)
							funcHash = computeTlsh(funcBody)

							if len(funcHash) == 72 and funcHash.startswith("T1"):
								funcHash = funcHash[2:]
							elif funcHash == "TNULL" or funcHash == "" or funcHash == "NULL":
								continue

							storedPath = filePath.replace(repoPath, "")
							if funcHash not in resDict:
								resDict[funcHash] = []
							resDict[funcHash].append(storedPath)

							lineCnt += len(lines)
							funcCnt += 1

				except subprocess.CalledProcessError as e:
					print("Parser Error:", e)
					continue
				except Exception as e:
					print ("Subprocess failed", e)
					continue

	return resDict, fileCnt, funcCnt, lineCnt

def indexing(resDict, title, filePath):
	# For indexing each OSS

	fres = open(filePath, 'w')
	fres.write(title + '\n')

	for hashval in resDict:
		if hashval == '' or hashval == ' ':
			continue

		fres.write(hashval)

		for funcPath in resDict[hashval]:
			fres.write('\t' + funcPath)
		fres.write('\n')

	fres.close()


def main():
	with open(gitCloneURLS, 'r', encoding = "UTF-8") as fp:
		funcDateDict = {}
		lines		 = [l.strip('\n\r') for l in fp.readlines()]

		for eachUrl in tqdm(lines):
			os.chdir(currentPath)
			repoName 	= eachUrl.split("github.com/")[1].replace(".git", "").replace("/", "@@") # Replace '/' -> '@@' for convenience
			print ("[+] Processing", repoName)

			try:
				cloneCommand 	= eachUrl + ' ' + clonePath + repoName
				cloneResult 	= subprocess.check_output(cloneCommand, stderr = subprocess.STDOUT, shell = True).decode()

				os.chdir(clonePath + repoName)

				dateCommand 	= 'git log --tags --simplify-by-decoration --pretty="format:%ai %d"'  # For storing tag dates
				dateResult		= subprocess.check_output(dateCommand, stderr = subprocess.STDOUT, shell = True).decode()
				tagDateFile 	= open(tagDatePath + repoName, 'w')
				tagDateFile.write(str(dateResult))
				tagDateFile.close()


				tagCommand		= "git tag"
				tagResult		= subprocess.check_output(tagCommand, stderr = subprocess.STDOUT, shell = True).decode()

				resDict = {}
				fileCnt = 0
				funcCnt = 0
				lineCnt = 0


				if tagResult == "":
					# No tags, only master repo

					resDict, fileCnt, funcCnt, lineCnt = hashing(clonePath + repoName)
					if len(resDict) > 0:
						if not os.path.isdir(resultPath + repoName):
							os.mkdir(resultPath + repoName)
						title = '\t'.join([repoName, str(fileCnt), str(funcCnt), str(lineCnt)])
						resultFilePath 	= resultPath + repoName + '/fuzzy_' + repoName + '.hidx' # Default file name: "fuzzy_OSSname.hidx"

						indexing(resDict, title, resultFilePath)

				else:
					for tag in str(tagResult).split('\n'):
						# Generate function hashes for each tag (version)

						checkoutCommand	= subprocess.check_output("git checkout -f " + tag, stderr = subprocess.STDOUT, shell = True)
						resDict, fileCnt, funcCnt, lineCnt = hashing(clonePath + repoName)

						if len(resDict) > 0:
							if not os.path.isdir(resultPath + repoName):
								os.mkdir(resultPath + repoName)
							title = '\t'.join([repoName, str(fileCnt), str(funcCnt), str(lineCnt)])
							resultFilePath 	= resultPath + repoName + '/fuzzy_' + tag + '.hidx'

							indexing(resDict, title, resultFilePath)


			except subprocess.CalledProcessError as e:
				print("Parser Error:", e)
				continue
			except Exception as e:
				print ("Subprocess failed", e)
				continue

""" EXECUTE """
if __name__ == "__main__":
	main()
