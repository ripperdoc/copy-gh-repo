import os
import git
import re
import inquirer
from github import Github

from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
if not token:
    print("Error: GITHUB_TOKEN environment variable not set.")
    exit()

# Authenticate with the GitHub API using a personal access token
g = Github(token)

# Get the name of the source repository and the two branch names from the user.
source_repo_path = os.getcwd()
source_repo_path = input(f"Enter the path of the source repository [{source_repo_path}]: ") or source_repo_path

repo = git.Repo(source_repo_path)
repo_name = source_repo_path.split("/")[-1]

branch_names = [b.name for b in repo.branches]

questions = [
    inquirer.List("branch_name",
                  message="Select the default branch for the new repo:",
                  choices=branch_names)
]
answers = inquirer.prompt(questions)
default_branch_name = answers["branch_name"]

questions = [
    inquirer.List("branch_name",
                  message="Select the Pull Request branch for the new repo:",
                  choices=branch_names)
]
answers = inquirer.prompt(questions)
pr_branch_name = answers["branch_name"]
assert pr_branch_name != default_branch_name, "Error: The default branch and the Pull Request branch must be different."

org_name = "fictive-reality"
org_name = input(f"Enter the name of the organization to create new repo in [{org_name}]: ") or org_name

# Get the organization
org = g.get_organization(org_name)

username = input("Enter the Github username to challenge: ")

new_repo_name = f"{repo_name}-challenge-{username}"
new_repo_name = input(f"Enter the name of the new repo [{new_repo_name}]: ") or new_repo_name

body_file = "CHALLENGE.md"
body_file = input(f"Enter the filename of the body of the new PR [{body_file}]: ") or body_file

with open(body_file, "r") as f:
    markdown_body = f.read()

lines = markdown_body.split("\n")
first_line = lines[0]

pr_title = re.sub(r"[^a-zA-Z0-9 ]", "", first_line).strip()

pr_title = input(f"Enter the title of the PR [{pr_title}]: ") or pr_title

# Create a new private repository on GitHub under the org account.
new_repo = org.create_repo(new_repo_name, private=True)

# Add the new repository as a new remote to the local repository.
new_remote = repo.create_remote(new_repo_name, new_repo.clone_url)

# Push the two selected branches to the new remote.
new_remote.push(f"{default_branch_name}:{default_branch_name}")
new_remote.push(f"{pr_branch_name}:{pr_branch_name}")

# Create a new pull request on the new repository from the second branch to the first branch.
new_pull_request = new_repo.create_pull(
        title=pr_title,
        body=markdown_body,
        base=default_branch_name,
        head=pr_branch_name,
    )

if username:
    new_repo.add_to_collaborators(username, permission="push")

print(new_pull_request.html_url)