# Leiden University System & Software Security Assignment 2: Hands-on Project - Group 8

Welcome to the official repository of Group 8 for Assignment 2 of the System &amp; Software Security course, part of the Master’s program at Leiden University. 

# CENTRIS: Reuse Detection Tool

### Requirements

#### Install Ctags
Install the universal-ctags tool to parse function definitions:
```bash
sudo apt install universal-ctags
```
#### Install python3-tlsh
Install the python-tlsh library using pip:
```bash
sudo apt-get install python3-pip
sudo pip3 install py-tlsh
```
#### Specify Ctags Path
Update the ctags path
```bash
ctags_path = "/path/to/ctags"  # Replace with the correct ctags path
```
# Using the Provided Dataset to reproduce the paper experiment

## Dataset
Download the dataset from [Zenodo](https://zenodo.org) (5 GB).

### Steps:

1. **Extract the downloaded file**  
   Extract `Centris_dataset.tar`:
   ```bash
   tar -xvf Centris_dataset.tar

2. There are four sample target software (ArangoDB, Crown, Cocos2dx, and Splayer, which are utilized in the in-depth comparison in the paper

3. To check the detection result for these four target software programs, set "**testmode**" in **line 193** of "**Detector_for_OSSList.py**" file to** 1**, and adjust the file paths in **lines 196 and 197** in the "**Detector_for_OSSList.py**" file.

4. Execute the "Detector_for_OSSList.py".
```bash
python3 Detector_for_OSSList.py
```
5. See the results (default output path: ./res/.)
