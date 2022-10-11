README
====================

The [website](https://UMCarpentries.github.io) for the University of Michigan chapter of Software and Data Carpentry


## Updating the workshops page

After creating a workshop repository and filling in the required information in the repo's `index.md`, fork it into this organization.
Then you can update the workshops listed on the website by running the [`update-workshops`](update-workshops.py) script from the website repo's working directory.

Dependences are listed in [`environment.yml`](environment.yml).
Minimally, you'll need `python 3.7`, `pygithub`, `pyyaml`, & `docopt`.
You can install them with your preferred package manager, or use [conda](https://docs.conda.io/en/latest/miniconda.html):

```
cd UMCarpentries.github.io
conda env create -f environment.yml
conda activate umcarp
```

Update the workshops page with
```
python workshops.py --token $(cat .token)
```
where `.token` is a plain text file containing a [GitHub access token](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line).

By default, all workshops -- past & upcoming -- will be included.
If a workshop post already exists, it will be overwritten with content from the repository.

Alternatively, you can display only upcoming workshops using the `--remove-old` flag.
Workshops with a start date before today (the day you run the script) will be removed from the page;
workshops with a start date after today will be added using information from the repo's `index.md` file.
```
python workshops.py --remove-old
```

Make sure you're happy with the changes in [`workshops/_posts`](workshops/_posts), then commit & push them to make the changes go live.

View available command-line options with the help flag:
```
python workshops.py --help
```
