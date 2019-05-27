""" Update the workshops page by purging old posts and creating new posts for upcoming workshops.

Usage:
    git-repos.py -h | --help
    git-repos.py --username=<your_username> [--dryrun]

Options:
    -h --help                       Display this help message.
    -u --username=<your_username>   Your GitHub username.
    -d --dryrun                     Print posts to be added and removed without doing it. [default: False]
"""

import datetime
from docopt import docopt
from getpass import getpass
from github import Github
import json
import os
import yaml

def main(args):
    """
    :param args: command-line arguments from docopt
    """
    # TODO: purge old workshop posts

    # gather upcoming workshops
    user_swc = Github().get_user("umswc")
    user_swc.get_repos()
    for repo in user_swc.get_repos():
        print(repo.name)
        # TODO: if workshop date is after today, add/update on website

if __name__ == "__main__":
    main(docopt(__doc__))
