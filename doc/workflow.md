# Workflow

0. load site.yaml file
1. go through the directories, creating a interpret-list of all .md and .html files,
and a copy-list of all other files that should be copied 
2. go through the interpret-list, loading the yaml frontmatter of all these files
3. creating the site object during that travel that stores the yaml frontmatter
4. start rendering
5. copy all files from the copy list to render directory
6. load each file from the interpret-list, move it through the filter-list
and the template machine (mako) and write it out to render directory
7. done