""" Update the workshops page by removing old posts and creating new posts for upcoming workshops.

Usage:
    update-workshops.py -h | --help
    update-workshops.py [--dryrun --workdir=<workdir> --username=<username>]

Options:
    -h --help                       Display this help message.
    -d --dryrun                     Print posts to be added and removed without doing it. [default: False]
    -w --workdir=<workdir>          Directory containing workshop posts. [default: workshops/_posts]
    -u --username=<username>        The GitHub username or organization name. [default: umswc]
"""

import base64
import datetime
from docopt import docopt
from github import Github
import os
import yaml


def main(args):
    """
    :param args: command-line arguments from docopt
    """
    remove_old_posts(args['--workdir'], dryrun=args['--dryrun'])
    update_new_posts(args['--workdir'], dryrun=args['--dryrun'], username=args['--username'])


def remove_old_posts(workdir, dryrun=False):
    """
    :param workdir: directory containing workshop posts
    :param dryrun: if True, print workshops to remove without removing them.
    :return: None
    """
    today = datetime.datetime.today()
    for filename in os.listdir(workdir):
        if filename.endswith('md'):
            workshop_date = datetime.datetime.strptime(''.join(filename.split('-')[:3]), '%Y%m%d')
            if workshop_date < today:
                print(f"Removing workshop {workshop_date.strftime('%Y-%m-%d')}")
                if not dryrun:
                    os.remove(os.path.join(workdir, filename))


def update_new_posts(workdir, dryrun=False, username="umswc"):
    """
    :param workdir: directory containing workshop posts
    :param dryrun: if True, print workshops to remove without removing them
    :param username: The GitHub username or organization name.
    :return: None
    """
    user_swc = Github().get_user(username)
    repos = sorted([repo for repo in user_swc.get_repos() if repo.name.split('-')[0].isnumeric()],
                   key=lambda repo: repo.name, reverse=True)
    workshop = Workshop.from_repo(repos.pop(0))
    while workshop.is_upcoming:  # if workshop date is after today, add/update on website
        print(f"Adding workshop {workshop.date}")
        if not dryrun:
            with open(os.path.join(workdir, f"{workshop.name}.md"), 'w') as file:
                file.write(workshop.yaml)
        workshop = Workshop.from_repo(repos.pop(0))


class Workshop:
    """
    Store & format Workshop information
    """
    titles = {'swc': "Software Carpentry",
              'dc': "Data Carpentry",
              'lc': "Library Carpentry"}

    def __init__(self, name, title, date, end_date, instructors, helpers, site, etherpad, eventbrite):
        self.name = name
        self.title = title
        self.date = date
        self.end_date = end_date
        self.instructors = instructors
        self.helpers = helpers
        self.site = site
        self.etherpad = etherpad
        self.eventbrite = eventbrite

    @property
    def yaml(self):
        """
        Format workshop attributes as YAML
        :return: YAML-formatted string of workshop attributes
        """
        return f"---\ntitle: {self.title}\ndate: {self.date}\nend_date: {self.end_date}\ninstructors:\n{self.instructors}\nhelpers:\n{self.helpers}\nsite: {self.site}\netherpad: {self.etherpad}\neventbrite: {self.eventbrite}\n---"

    @property
    def is_upcoming(self):
        """
        Check whether the workshop end date is after today
        :return: True if workshop end date is after today, else False
        """
        return datetime.datetime.today() < datetime.datetime.strptime(self.end_date, '%Y%m%d')

    @classmethod
    def from_repo(cls, repo):
        """
        Create a Workshop from a Github repository
        :param repo: a Github repository from pygithub
        :return: a Workshop instance
        """
        header = {key: (value if value else '') for key, value in yaml.load(
            base64.b64decode(repo.get_contents('index.md').content).decode('utf-8').strip("'").split('---')[1],
            Loader=yaml.Loader).items()}
        return cls(name=repo.name,
                   title=f'{cls.titles[header["carpentry"]]} Workshop',
                   date=header['startdate'].strftime('%Y%m%d'),
                   end_date=header['enddate'].strftime('%Y%m%d'),
                   instructors='\n'.join("- " + name for name in header['instructor']),
                   helpers='\n'.join("- " + name for name in header['helper']),
                   site=f'https://{repo.owner.login}.github.io/{repo.name}',
                   etherpad=header['collaborative_notes'],
                   eventbrite=header['eventbrite'])


if __name__ == "__main__":
    main(docopt(__doc__))
