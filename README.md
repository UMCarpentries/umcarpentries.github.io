README
====================

The [website](https://umswc.github.io) for the University of Michigan chapter of Software and Data Carpentry


## Updating the workshops page

After creating a workshop repository and filling in the required information in the repo's `index.md`, fork it into this organization.
Then you can update the workshops listed on the website by running the [`update-workshops`](update-workshops.py) script from the website repo's working directory.

Dependences are listed in [`env.yaml`](env.yaml).
You can install them with your preferred package manager, or use [conda](https://docs.conda.io/en/latest/miniconda.html):

```
cd umswc.github.io
conda env create -f env.yaml
conda activate umswc
```

Update the workshops page:
```
python update-workshops.py
```

Workshops with a start date before today (the day you run the script) will be removed from the page;
workshops with a start date after today will be added using information from the repo's `index.md` file.
If an upcoming workshop post exists, it will be overwritten with content from the repository.

Alternatively, you can display all workshop posts -- past & upcoming -- using the `--write-all` flag:
```
python update-workshops.py --write-all
```

Make sure you're happy with the changes in [`workshops/_posts`](workshops/_posts), then commit & push them to make the changes go live.

View available command-line options with the help flag:
```
python update-workshops.py --help
```
