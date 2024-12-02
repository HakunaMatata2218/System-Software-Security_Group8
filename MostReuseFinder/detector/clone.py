import os
import subprocess
from tqdm import tqdm

# Set global paths
currentPath = os.getcwd()
gitCloneURLS = os.path.join(currentPath, "target_java")  # File path containing Git repository URLs
clonePath = os.path.join(currentPath, "crown")  # Path where repositories will be cloned

# Create a directory for storing cloned repositories if it doesn't already exist
if not os.path.exists(clonePath):
    os.makedirs(clonePath)

def clone_repositories():
    try:
        # Read the file containing Git URLs
        with open(gitCloneURLS, 'r', encoding="UTF-8") as fp:
            urls = [line.strip() for line in fp if line.strip()]  # Remove empty lines

        # Iterate through the list of URLs and clone each repository
        for eachUrl in tqdm(urls, desc="Cloning repositories"):
            # Generate a unique repository name based on its URL
            repoName = eachUrl.split("github.com/")[1].replace(".git", "").replace("/", "@@")
            repoPath = os.path.join(clonePath, repoName)
            print(f"[+] Processing {repoName}")

            # Skip cloning if the repository already exists
            if os.path.exists(repoPath):
                print(f"Repository {repoName} already exists. Skipping...")
                continue

            try:
                # Construct the correct Git clone command
                cloneCommand = f"{eachUrl} {repoPath}"
                subprocess.run(cloneCommand, check=True, shell=True)
                print(f"Successfully cloned {repoName}.")
            except subprocess.CalledProcessError as e:
                print(f"Error cloning {repoName}: {e}")
            except Exception as e:
                print(f"Unexpected error while cloning {repoName}: {e}")
    except FileNotFoundError:
        # Handle the case where the file containing Git URLs is not found
        print(f"Error: The file '{gitCloneURLS}' was not found.")
    except Exception as e:
        # Handle any other unexpected errors during the cloning process
        print(f"Unexpected error while processing repositories: {e}")

if __name__ == "__main__":
    clone_repositories()
