""" Update the workshops page by removing old posts and creating new posts for upcoming workshops.

Usage:
    update-workshops.py -h | --help
    update-workshops.py [--dryrun --remove-old --workdir=<workdir> --username=<username> --token=<token>]

Options:
    -h --help                       Display this help message.
    -d --dryrun                     Print posts to be added and removed without doing it.
    -a --remove-old                 Remove past workshop posts and only add upcoming ones.
    -w --workdir=<workdir>          Directory containing workshop posts. [default: workshops/_posts]
    -u --username=<username>        The GitHub username or organization name. [default: umswc]
    -t --token=<token>              Github authorization token
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
    if args['--token']:
        github = Github(args['--token'])
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

def test():
    """ Get repos for testing interactively
    :return: list of pygithub repos
    """
    with open(".token", 'r') as token_file:
        token = token_file.readline().strip()
    github = Github(token)
    user_swc = github.get_user('umswc')
    return sorted([repo for repo in user_swc.get_repos() if repo.name.split('-')[0].isnumeric()],
                   key=lambda repo: repo.name, reverse=True)


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
                       date=format_date(header['startdate']),
                       end_date=format_date(header['enddate']),
                       instructors=join_list(header['instructor']),
                       helpers=join_list(header['helper']),
                       site=f'https://{repo.owner.login}.github.io/{repo.name}',
                       etherpad=header['collaborative_notes'] if 'collaborative_notes' in header else header['etherpad'],
                       eventbrite=header['eventbrite'],
                       material=material,
                       audience="",)
        return workshop

    @classmethod
    def get_header(cls, repo):
        """
        Get the YAML header from the index file
        :param repo: Github repository corresponding to a workshop
        :return: dictionary
        """
        repo_contents = [file for file in repo.get_contents("", ref="gh-pages") if file.path in {"index.md",
                                                                                             "index.html"}]  #
        # index could be markdown or html. expect only one
        index_file = repo_contents.pop()
        header = {key: (value if value else '') for key, value in yaml.load(decode_gh_file(index_file).split('---')[1], Loader=yaml.Loader).items()}
        if 'carpentry' not in header: # new template has 'carpentry' field in _config.yaml only, not index.md
            config_file = repo.get_contents("_config.yml", ref="gh-pages")
            config_dict = yaml.load(decode_gh_file(config_file), Loader=yaml.Loader)
            if 'carpentry' in config_dict:
                header['carpentry'] = config_dict['carpentry']

        return header

    @classmethod
    def get_syllabus_lessons(cls, repo, carpentry):
        """ Get the lesson titles from the syllabus html
        :param carpentry: The Carpentry organization (swc, dc, lc)
        :param repo: Github repository corresponding to a workshop
        :return: string containing the lesson titles separated by commas
        """
        material = list()
        includes_dir = "_includes"
        syllabus_filename = "syllabus.html"
        index_filename = "index.html"
        content_paths = {file.path for file in repo.get_contents(includes_dir, ref="gh-pages")}
        # pick correct syllabus path
        if f"{includes_dir}/{carpentry}" in content_paths:  # TODO: upgrade to python=3.8 and use walrus operator
            filepath = f"{includes_dir}/{carpentry}/{syllabus_filename}"
        elif carpentry == "swc" and f"{includes_dir}/sc" in content_paths:
            # previous abbr for 'swc' dir was 'sc'; handle both versions
            filepath = f"{includes_dir}/sc/{syllabus_filename}"
        else: # TODO: handle old-style workshop repos with syllabus content in index.html
            #filepath = index_filename
            filepath = None
        # only get syllabus if the file could be found
        if filepath and syllabus_filename in filepath:
            syllabus = [line.strip() for line in decode_gh_file(repo.get_contents(filepath, ref="gh-pages")).split('\n')]
            is_comment = False
            for line in syllabus:
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


def format_date(date):
    """ Format a datetime.date object in ISO 8601 format.
    If the date given is not a datetime.date object, it returns the object but type-casted as a string.
    :param date: a datetime.date object
    :return: a string in ISO 8601 format
    """
    return date.strftime('%Y-%m-%d') if type(date) == date else str(date)


def join_list(this_list):
    """ Join the elements of a list into a string of items separated by hyphens & newlines.
    :param this_list: a list
    :return: a string of the list items separated by hyphens & newlines.
    """
    return '\n'.join(f"- {thing}" for thing in this_list)

def decode_gh_file(gh_file):
    return base64.b64decode(gh_file.content).decode('utf-8').strip("'")

if __name__ == "__main__":
    main(docopt(__doc__))
