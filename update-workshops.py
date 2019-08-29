""" Update the workshops page by removing old posts and creating new posts for upcoming workshops.

Usage:
    update-workshops.py -h | --help
    update-workshops.py [--dryrun --remove-old --workdir=<workdir> --username=<username> --tokenpath=<tokenpath>]

Options:
    -h --help                       Display this help message.
    -d --dryrun                     Print posts to be added and removed without doing it.
    -a --remove-old                 Remove past workshop posts and only add upcoming ones.
    -w --workdir=<workdir>          Directory containing workshop posts. [default: workshops/_posts]
    -u --username=<username>        The GitHub username or organization name. [default: umswc]
    -t --tokenpath=<tokenpath>      The path to a text file containing a Github authorization token
"""

import base64
import datetime
from docopt import docopt
from github import Github
import os
import yaml


def main(args):
    """ Gather workshop repositories and update the workshop posts.
    By default, all workshops (past and upcoming) will be written to posts.
    If the flag --remove-old is used, old workshop posts will be removed and only upcoming workshops will be written to posts.
    :param args: command-line arguments from docopt
    """
    if args['--tokenpath']:
        with open(args['--tokenpath'], 'r') as token_file:
            token = token_file.readline().strip()
        github = Github(token)
    else:
        github = Github()
    user_swc = github.get_user(args['--username'])
    repos = sorted([repo for repo in user_swc.get_repos() if repo.name.split('-')[0].isnumeric()],
                   key=lambda repo: repo.name, reverse=True)
    if args['--remove-old']:
        remove_old_posts(args['--workdir'], dryrun=args['--dryrun'])
        write_upcoming_posts(repos, args['--workdir'], dryrun=args['--dryrun'])
    else:
        write_all_posts(repos, args['--workdir'], dryrun=args['--dryrun'])


def remove_old_posts(workdir, dryrun=False):
    """ Remove past workshops from the posts directory
    :param workdir: directory containing workshop posts
    :param dryrun: if True, print workshops to remove without removing them.
    :return: None
    """
    print("Removing old workshop posts")
    today = datetime.datetime.today()
    for filename in os.listdir(workdir):
        if filename.endswith('md'):
            workshop_date = datetime.datetime.strptime(''.join(filename.split('-')[:3]), '%Y%m%d')
            if workshop_date < today:
                print(f"Removing workshop {workshop_date.strftime('%Y-%m-%d')}")
                if not dryrun:
                    os.remove(os.path.join(workdir, filename))


def write_upcoming_posts(repos, workdir, dryrun=False):
    """ Write upcoming workshops to the posts directory
    :param repos: list of Github repositories
    :param workdir: directory containing workshop posts
    :param dryrun: if True, print workshops to remove without removing them
    :return: None
    """
    print("Writing upcoming workshop posts")
    workshop = Workshop.from_repo(repos.pop(0))
    while workshop.is_upcoming:  # if workshop date is after today, add/update on website
        if not dryrun:
            workshop.write_markdown(workdir)
        workshop = Workshop.from_repo(repos.pop(0))


def write_all_posts(repos, workdir, dryrun=False):
    """ Write all workshops, past and upcoming, to the posts directory.
    :param repos: list of Github repositories
    :param workdir: directory containing workshop posts
    :param dryrun: if True, print workshops to remove without removing them
    :return: None
    """
    print("Writing all workshop posts")
    for repo in repos:
        workshop = Workshop.from_repo(repo)
        if not dryrun:
            workshop.write_markdown(workdir)


class Workshop:
    """
    Store & format Workshop information
    """
    titles = {'swc': "Software Carpentry",
              'dc': "Data Carpentry",
              'lc': "Library Carpentry",
              '': ''}

    def __init__(self, name, title, date, end_date, instructors, helpers, site, etherpad, eventbrite, material, audience):
        self.name = name
        self.title = title
        self.date = date
        self.end_date = end_date
        self.instructors = instructors
        self.helpers = helpers
        self.site = site
        self.etherpad = etherpad
        self.eventbrite = eventbrite
        self.material = material
        self.audience = audience

    @property
    def yaml(self):
        """ Format workshop attributes as YAML
        :return: YAML-formatted string of workshop attributes
        """
        return f"---\ntitle: {self.title}\ndate: {self.date}\nend_date: {self.end_date}\ninstructors:\n{self.instructors}\nhelpers:\n{self.helpers}\nsite: {self.site}\netherpad: {self.etherpad}\neventbrite: {self.eventbrite}\nmaterial: {self.material}\naudience: {self.audience}\n---"

    @property
    def is_upcoming(self):
        """ Check whether the workshop end date is after today
        :return: True if workshop end date is after today, else False
        """
        return datetime.datetime.today() < datetime.datetime.strptime(self.end_date, '%Y-%m-%d')

    @classmethod
    def from_repo(cls, repo):
        """ Create a Workshop from a Github repository
        :param repo: a Github repository object from pygithub
        :return: a Workshop instance
        """
        print(f"Writing workshop from repo {repo.name}")
        header = cls.get_header(repo)
        carpentry = header['carpentry'] if 'carpentry' in header else ''
        material = cls.get_syllabus_lessons(repo, carpentry)
        workshop = cls(name=repo.name,
                       title=f'{cls.titles[carpentry]} Workshop',
                       date=header['startdate'].strftime('%Y-%m-%d'),
                       end_date=header['enddate'].strftime('%Y-%m-%d'),
                       instructors='\n'.join("- " + name for name in header['instructor']),
                       helpers='\n'.join("- " + name for name in header['helper']),
                       site=f'https://{repo.owner.login}.github.io/{repo.name}',
                       etherpad=header['collaborative_notes'] if 'collaborative_notes' in header else header['etherpad'],
                       eventbrite=header['eventbrite'],
                       material=material,
                       audience="",)
        return workshop

    @classmethod
    def get_header(cls, repo):
        repo_contents = [file for file in repo.get_contents("") if file.path in {"index.md", "index.html"}]  # index could be markdown or html
        index_file = repo_contents.pop()
        header = {key: (value if value else '') for key, value in yaml.load( base64.b64decode(index_file.content).decode('utf-8').strip("'").split('---')[1], Loader=yaml.Loader).items()}
        return header

    @classmethod
    def get_syllabus_lessons(cls, repo, carpentry):
        """ Get the lesson titles from the syllabus html
        :param carpentry: The Carpentry organization (swc, dc, lc)
        :param repo: Github repository corresponding to a workshop
        :return: string containing the lesson titles separated by commas
        """
        material = list()
        filepath = f"_includes/{'sc' if carpentry == 'swc' else carpentry}/syllabus.html"
        # TO-DO: handle old-style workshop repos with syllabus content in index.html
        # (e.g. https://github.com/UMSWC/2017-12-18-umich)
        content_paths = {file.path for file in repo.get_contents("_includes")}
        if '_includes/sc' in content_paths:
            syllabus = [line.strip() for line in base64.b64decode(repo.get_contents(filepath).content).decode('utf-8').strip("'").split('\n')]
            is_comment = False
            while syllabus:
                line = syllabus.pop(0)
                if line.startswith('<!--'):
                    is_comment = True
                elif line.endswith('-->'):
                    is_comment = False
                elif not is_comment and line.startswith('<h3'):
                    lesson = line.split('>')[1].split('</')[0].strip() if "href" not in line else line.split('>')[2].split('</')[0].strip()
                    material.append(lesson)
        return ', '.join(material)

    def write_markdown(self, workdir):
        """ Write a markdown file containing the yaml header
        :param workdir: directory to write the file to
        :return: None
        """
        with open(os.path.join(workdir, f"{self.name}.md"), 'w') as file:
            file.write(self.yaml)


if __name__ == "__main__":
    main(docopt(__doc__))
