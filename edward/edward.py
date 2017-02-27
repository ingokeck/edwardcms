#   Copyright 2017 Ingo R.Keck
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ruamel.yaml as yaml
import markdown
from mako.lookup import TemplateLookup
from mako.template import Template
import sys, argparse, fnmatch, os
import copy, shutil
from . import create_default_files


DEFAULT_SITE_CONFIG = 'site.yaml'
SITE_DIR_SEPARATOR = '/'
TEMPLATE_EXTENTION = '.mako'
VERBOSE = True

class MySite(object):
    def __init__(self):
        self.config = dict()
        self.pages = dict()
        self.folders = dict()
def file_type(filename):
    """
    Detects the file type based on file name for filtering
    :param filename: Filename to be detected
    :return: type
    """
    name, ext = os.path.splitext(filename)
    if ext.lower() == '.md':
        return "markdown"
    elif ext.lower() == '.htm':
        return "html"
    elif ext.lower() == '.html':
        return "html"
    return ""


def new_site(sitepath, sitetemplate=None):
    """
    Create a new Edward site
    :param sitepath: Path where the new Edward site is going to be created
    :return: True if all went well
    """
    create_default_files.create_folders(sitepath)
    create_default_files.create_conf(os.path.join(sitepath, DEFAULT_SITE_CONFIG))
    if sitetemplate:
        # copy files from the template
        create_default_files.copy_files(sitepath, sitetemplate)
    return True

def render_site(sitepath, outpath=None):
    """
    Render the files in the Edward site directory
    :param sitepath: Path to Edward site directory
    :param outpath: Path to render the site to
    :return: True if all went well
    """
    # load site.yaml
    site = MySite()
    with open(os.path.join(sitepath, DEFAULT_SITE_CONFIG)) as infile:
        site.config = yaml.safe_load(infile)
        infile.close()
    site.pages = dict()
    # get root folders of site
    root_folders = os.scandir(sitepath)
    for folder in root_folders:
        if folder.is_dir():
            if not fnmatch.fnmatch(folder.name, site.config['exclude']):
                site.folders[folder.name] = folder.name
    # scan all templates
    template_dict = dict()
    ts = os.scandir(os.path.join(sitepath, '_templates'))
    for t in ts:
        if t.is_file():
            template_dict[os.path.splitext(t.name)[0]]=t.name
    if VERBOSE:
        print("The following templates have been found:", template_dict)
    #print(template_dict)
    # create render directory
    if not outpath:
        raise "please state an output directory"
    if not os.path.exists(outpath):
        os.mkdir(outpath)
    # go through the whole site, generating our site construct holding all information of the files within
    for dirpath, dirnames, filenames in os.walk(sitepath):
        if os.path.abspath(outpath) in os.path.abspath(dirpath):
            continue
        #print("path: " , os.path.abspath(dirpath), os.path.abspath(outpath))
        # match all files in the "interpret" list of site.yaml
        matched_files = []
        for pat in site.config['interpret']:
            matched_files += fnmatch.filter(filenames,pat)
        #print(matched_files)
        # read in frontmatter of all matched files
        for filename in matched_files:
            # remove filename from filenames, because will will simply copy all other files
            filenames.remove(filename)
            # now read in the file
            with open(os.path.join(dirpath, filename)) as infile:
                front_matter, content = list(yaml.safe_load_all(infile))[:2]
                infile.close()
            #print(front_matter)
            #print(content)
            front_matter["filepath"] = os.path.join(dirpath, filename)
            # get filetype - mostly markdown or html right now
            front_matter["filetype"] = file_type(filename)
            # we use the permalink as page ID
            if not 'permalink' in front_matter:
                # set permalink based on filename and relative path
                # we assume that os.walk always uses "/" as path separator. On the mac it does.
                htmlpath = dirpath.split(sitepath)[1] + SITE_DIR_SEPARATOR
                # remove leading separator
                if htmlpath[:len(SITE_DIR_SEPARATOR)] == SITE_DIR_SEPARATOR:
                    htmlpath = htmlpath[len(SITE_DIR_SEPARATOR):]
                front_matter['permalink'] = htmlpath + os.path.splitext(filename)[0] + site.config['html extention']
            # calculate relative path to root folder
            relpath = "../" * (dirpath.split(sitepath)[1].count("/"))
            #print(relpath)
            # add folder info
            front_matter['folders'] = dict()
            for folder in site.folders:
                front_matter['folders'][folder] = relpath + site.folders[folder]
            # now copy all that info to the pages dict in the site object
            site.pages[front_matter['permalink']]=copy.deepcopy(front_matter)
            #print(front_matter)
        # now all files left in filenames are files we will simply copy
        # unless we are in an ignored directory
        if fnmatch.fnmatch(os.path.split(dirpath)[1], site.config['exclude']):
            continue
        # calculate target directory
        targetdir = os.path.join(outpath, dirpath.split(sitepath)[1][1:])
        #print(targetdir)
        for fname in filenames:
            if fname.lower() == "site.yaml":
                continue
            # copy file
            #print("copy file:", os.path.join(dirpath, fname), os.path.join(targetdir, fname))
            shutil.copyfile(os.path.join(dirpath, fname), os.path.join(targetdir, fname))
        for dname in dirnames:
            if not os.path.abspath(outpath) in os.path.abspath(os.path.join(dirpath, dname)):
                if not fnmatch.fnmatch(dname, site.config['exclude']):
                    #make directory
                    #print("create dir ", os.path.join(targetdir, dname))
                    os.makedirs(os.path.join(targetdir, dname), exist_ok=True)
    #print(site.pages)

    # now we go through all pages and render them
    # prepare templates
    my_template_lookup = TemplateLookup(directories=[os.path.join(sitepath,'_templates')])
    for key in site.pages:
        page = site.pages[key]
        content = ""
        with open(page['filepath']) as infile:
            # remove frontmatter
            count = 0
            while count < 2:
                if infile.readline().strip() == '---':
                    count += 1
            # load content
            lastline = infile.readline()
            while lastline:
                content += lastline
                lastline = infile.readline()
            infile.close()
        if page['filetype'] == 'markdown':
            page_body = markdown.markdown(content)
        else:  #html
            page_body = content
        #print('input', content)
        #print('output', page_body)
        filepath = os.path.join(outpath, *page['permalink'].split(SITE_DIR_SEPARATOR))
        os.makedirs(os.path.split(filepath)[0], exist_ok=True)
        #print("render file: ", filepath)
        mytemplate = my_template_lookup.get_template(template_dict[page['template']])
        result = mytemplate.render(site=site.config, page=page, body=page_body)
        with open(filepath, "w") as outfile:
            outfile.write(result)
            outfile.close()
    return True


def main(arglist):
    """Main routine"""
    # parse arguments
    parser = argparse.ArgumentParser(description='Edward simple CMS system.')
    parser.add_argument('command', metavar='command', type=str, choices=['new', 'render', 'serve'],
                        help="""Can be "new", "render" or "serve".
                        "new" will create a new edward site.
                        "render" will render the existing edward site.
                        """ )
    parser.add_argument('path', action='store', type=str, default='', nargs='?',
                        help='Path to edward directory. If empty the current directory will be used.')
    parser.add_argument('-o', action='store', type=str, dest='outpath', default='',
                        help='Path for rendering the site. If empty, the "build" directory for '+
                             'rendering the existing site.')
    parser.add_argument('-n', action='store', type=str, dest='sitetemplate', default='',
                        help='template for the new site (use only for command "new"). Can be "simple" or "blog"')
    args = parser.parse_args(args=arglist)
    if args.command == 'new':
        if VERBOSE:
            print('Selected command: new')
        if not args.path: # if path is emtpy, use current directory
            args.path = os.getcwd()
        result = new_site(sitepath=args.path, sitetemplate=args.sitetemplate)
        return result
    elif args.command == 'render':
        if VERBOSE:
            print('Selected command: render')
        if not args.path: # if path is emtpy, use current directory
            args.path = os.getcwd()
        if not args.outpath:
            args.outpath = os.path.join(args.path, 'build')
        render_site(sitepath=args.path, outpath=args.outpath)
    elif args.command == 'serve':
        if VERBOSE:
            print('Selected command: serve')
        if not args.path: # if path is emtpy, use current directory
            args.path = os.getcwd()
    else:
        raise 'unkown command'
    #print(args)
    return(True)

if __name__ == '__main__':
    main(sys.argv)


