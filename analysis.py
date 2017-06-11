# http://chase-seibert.github.io/blog/2016/07/22/pygithub-examples.html
# https://stackoverflow.com/questions/41691327/ssl-sslerror-ssl-certificate-verify-failed-certificate-verify-failed-ssl-c
from github import Github
from github import UnknownObjectException
import pandas as pd
# creating your own Github token:
# https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/
from config import GITHUB_API_TOKEN
import argparse
import time


def generate_argument_parser():
    """
    Generates a parser for command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Get total lines of code for a github user."
    )
    parser.add_argument(
        'github_username',
        help='''
        the github username
        usage: python analysis.py [GITHUB_USERNAME]
        example: python analysis.py EricSchles
        '''
    )
    return parser


def get_sha(repo) -> str:
    """
    get the sha from the repository object

    Parameter
    ---------
    repo - the repository object from
    http://pygithub.readthedocs.io/en/latest/github_objects/Repository.html
    """
    default_branch = repo.raw_data["default_branch"]
    ref = [ref for ref in repo.get_git_refs()
           if default_branch in ref.url]
    if ref != []:
        ref = ref[0]
        return ref.raw_data["object"]["sha"]
    else:
        return None


def get_file_paths(repo, sha):
    """
    Get the relative files paths within the repo.

    Parameters
    ----------
    repo - the repository object from the github api:
    http://pygithub.readthedocs.io/en/latest/github_objects/Repository.html
    sha - the sha hash from get_sha (defined above)
    """
    files = []
    file_tree = repo.get_git_tree(sha, recursive=True).tree
    for file_obj in file_tree:
        files.append(file_obj.path)
    return files


def get_num_lines(repo, File) -> int:
    """
    gets the number of lines in the file.

    Parameters
    ----------
    repo - the repository object from the github api:
    http://pygithub.readthedocs.io/en/latest/github_objects/Repository.html
    File - the file path within the repo
    """
    file_obj = repo.get_file_contents(File)
    file_content = file_obj.decoded_content.decode("utf-8")
    return len(file_content.split("\n"))


def pause_if_exceed_rate_limit(github_api):
    """
    Pauses the code, while the rate limit resets

    Parameter
    ---------
    github_api - the github api object:
    http://pygithub.readthedocs.io/en/latest/github.html
    """
    # assume base of 1 second
    MINUTE = 60
    HOUR = 60 * MINUTE
    rate_limit = github_api.get_rate_limit()
    if rate_limit.rate.remaining == 0:
        print("You've hit the rate limit for the github API (5000 requests).")
        print("The rate limit resets after about an hour.")
        print("The program will pause now for an hour.")
        print("Alternatively you can hit CTRL-C.")
        print("And try again in an hour.")
        print("Happy hacking!")
        time.sleep(HOUR)
    return

if __name__ == '__main__':
    parser = generate_argument_parser()
    args = parser.parse_args()
    github_api = Github(login_or_token=GITHUB_API_TOKEN)
    user = github_api.get_user()
    repos = [elem for elem in user.get_repos()]
    df = pd.DataFrame()
    total_num_lines = 0
    repos = [repo for repo in repos
             if args.github_username in repo.url]
    for repo in repos:
        pause_if_exceed_rate_limit(github_api)
        sha = get_sha(repo)
        if sha is None:
            continue
        files = get_file_paths(repo, sha)
        for File in files:
            if File.endswith(".py"):
                try:
                    num_lines = get_num_lines(repo, File)
                except UnknownObjectException:
                    continue
                df = df.append(
                    {
                        "number_lines": num_lines,
                        "file_path": File,
                        "repo": repo.url
                    }, ignore_index=True)
                total_num_lines += num_lines
    print("Total number of lines", total_num_lines)
    df.to_csv("results.csv")
