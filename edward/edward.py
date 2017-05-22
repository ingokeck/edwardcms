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
import markdown, json
from mako.lookup import TemplateLookup
from mako.template import Template
import sys, argparse, fnmatch, os
import copy, shutil
from . import create_default_files
from mako import exceptions
import datetime

DEFAULT_SITE_CONFIG = 'site.yaml'
SITE_DIR_SEPARATOR = '/'
TEMPLATE_EXTENTION = '.mako'
VERBOSE = True

class MySite(object):
    def __init__(self):
        self.config = dict()
        self.pages = dict()
        self.folders = dict()
        self.posts = dict()
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
    elif ext.lower() == '.yaml':
        return "yaml"
    elif ext.lower() == '.json':
        return "json"
    return ""


def parse_yaml_json(filepath):
    with open(filepath) as infile:
        # load frontmatter
        count = 0
        frontmatter = ''
        newline = infile.readline()
        while ((count < 1) & (len(newline)>0)):
            if newline.strip() == '---':
                count += 1
            newline = infile.readline()
        while ((count < 2) & (len(newline)>0)):
            if newline.strip() == '---':
                count += 1
            else:
                frontmatter += newline
            newline = infile.readline()
        if len(frontmatter) == 0:
            return None, None
        # test what works better, json or yaml:

        try:
            result = json.loads(frontmatter)
        except:
            try:
                result = yaml.safe_load(frontmatter)
            except:
                print('problem with frontmatter in file %s' %filepath)
        # load content
        content = newline
        lastline = infile.readline()
        while lastline:
            content += lastline
            lastline = infile.readline()
        infile.close()
    return (result, content)

def new_site(sitepath, sitetemplate=None):
    """
    Create a new Edward site. If the sitetemplate parameter is empty, we will only create
    the usual directories and a DEFAULT_SITE_CONFIG file
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
        if file_type(DEFAULT_SITE_CONFIG) == 'yaml':
            site.config = yaml.safe_load(infile)
        elif file_type(DEFAULT_SITE_CONFIG) == 'json':
            site.config = json.load(infile)
        infile.close()
    if not isinstance(site.config["exclude"], list):
        site.config["exclude"] = [site.config["exclude"]]
    site.pages = dict()
    # get root folders of site
    root_folders = os.scandir(sitepath)
    for folder in root_folders:
        if folder.is_dir():
            exclude_flag = False
            for exclude_expr in site.config['exclude']:
                if fnmatch.fnmatch(folder.name, exclude_expr):
                    exclude_flag = True
                    break
            if not exclude_flag:
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
        if VERBOSE:
            print("Analysis directroy %s" % dirpath)
        if os.path.abspath(outpath) in os.path.abspath(dirpath):
            continue
        # don't analyse subdirectories that are excluded, unless the are also to be rendered
        for dpos, dirn in enumerate(dirnames):
            render_flag = False
            for render_expr in site.config['render']:
                if fnmatch.fnmatch(dirn, render_expr):
                    render_flag = True
            #we also render the blog posts directories
            for blog_dir in site.config['blogposts']:
                if fnmatch.fnmatch(dirn, blog_dir):
                    render_flag = True
            if not render_flag:
                exclude_flag = False
                for exclude_expr in site.config['exclude']:
                    if fnmatch.fnmatch(dirn, exclude_expr):
                        exclude_flag = True
                        break
                if exclude_flag:
                    del dirnames[dpos]
        # see if we are in the blogposts directory
        blogdir_flag = False
        if fnmatch.fnmatch(os.path.split(dirpath)[1], site.config['blogposts']):
            print(os.path.split(dirpath)[1])
            print("blog dir? %s" %dirpath )
            blogdir_flag = True
        #print("path: " , os.path.abspath(dirpath), os.path.abspath(outpath))
        # match all files in the "interpret" list of site.yaml
        matched_files = []
        for pat in site.config['interpret']:
            matched_files += fnmatch.filter(filenames,pat)
        matched_files = list(set(matched_files)) # unique filenames
        # read in frontmatter of all matched files
        for filename in matched_files:
            if VERBOSE:
                print("reading in file %s" % os.path.join(dirpath,filename))
            # remove filename from filenames, because will will simply copy all other files
            filenames.remove(filename)
            # now read in the file
            # we support now json and yaml
            front_matter, content = parse_yaml_json(os.path.join(dirpath, filename))
            if VERBOSE:
                print("Front matter: %s" % front_matter)
            if not front_matter:
                # file has no front matter, just copy it
                filenames.append(filename)
                continue
            front_matter["filepath"] = os.path.join(dirpath, filename)
            # get filetype - mostly markdown or html right now
            front_matter["filetype"] = file_type(filename)
            if blogdir_flag:
                # we treat blogposts special
                if not "time" in front_matter:
                    front_matter["time"] = "9:00"
                if not "date" in front_matter:
                    front_matter["date"] = filename[0:10]
                if not "permalink" in front_matter:
                    htmlpath = "blog" + SITE_DIR_SEPARATOR
                    front_matter['permalink'] = htmlpath + os.path.splitext(filename)[0] + site.config['html extention']
                # the files in your templates must handle blogposts themselves.
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
            front_matter['basepath'] = relpath
            #print(relpath)
            # add folder info
            front_matter['folders'] = dict()
            for folder in site.folders:
                front_matter['folders'][folder] = relpath + site.folders[folder]
            # now copy all that info to the pages dict in the site object
            site.pages[front_matter['permalink']]=copy.deepcopy(front_matter)
            # if it is a blogpost, also add it to the blogposts  dict
            if blogdir_flag:
                if not 'summary' in front_matter:
                    front_matter["summary"] = " ".join(str(x) for x in content.split()[0:10])
                site.posts[front_matter['permalink']]=copy.deepcopy(front_matter)
            #print(front_matter)
        # now all files left in filenames are files we will simply copy
        # unless we are in an ignored directory
        exclude_flag = False
        for exclude_expr in site.config['exclude']:
            if fnmatch.fnmatch(os.path.split(dirpath)[1], exclude_expr):
                exclude_flag = True
                break
        if exclude_flag:
            continue
        # calculate target directory
        targetdir = os.path.join(outpath, dirpath.split(sitepath)[1][1:])
        #print(targetdir)
        for fname in filenames:
            if fname.lower() == DEFAULT_SITE_CONFIG:
                continue
            exclude_flag = False
            for exclude_expr in site.config['exclude']: # dont copy excluded files
                if fnmatch.fnmatch(fname, exclude_expr):
                    exclude_flag = True
                    break
            if exclude_flag:
                if VERBOSE:
                    print ("file %s is ignored" %fname)
                continue
            # copy file
            #print("copy file:", os.path.join(dirpath, fname), os.path.join(targetdir, fname))
            shutil.copyfile(os.path.join(dirpath, fname), os.path.join(targetdir, fname))
        for dname in dirnames:
            print ("looking at directory %s" %dname)
            if not os.path.abspath(outpath) in os.path.abspath(os.path.join(dirpath, dname)):
                exclude_flag = False
                for exclude_expr in site.config['exclude']:
                    if fnmatch.fnmatch(dname, exclude_expr):
                        exclude_flag = True
                        if VERBOSE:
                            print("directory %s is ignored" %dname)
                if not exclude_flag:
                    #make directory
                    if VERBOSE:
                        print("create dir ", os.path.join(targetdir, dname))
                    os.makedirs(os.path.join(targetdir, dname), exist_ok=True)
    #print(site.pages)

    # now we go through all pages and render them
    # prepare templates
    my_template_lookup = TemplateLookup(directories=[os.path.join(sitepath,'_templates')],
                                        input_encoding='utf-8', encoding_errors='replace')
    for key in site.pages:
        page = site.pages[key]
        if VERBOSE:
            print("Rendering page %s" % page['filepath'])
        front_matter, content = parse_yaml_json(page['filepath'])
        if page['filetype'] == 'markdown':
            page_body = markdown.markdown(content)
        else:  #html
            page_body = content
        #print('input', content)
        #print('output', page_body)
        filepath = os.path.join(outpath, *page['permalink'].split(SITE_DIR_SEPARATOR))
        os.makedirs(os.path.split(filepath)[0], exist_ok=True)
        #print("render file: ", filepath)
        # first render the page content
        body_template = Template(page_body)
        body_content = body_template.render(site=site.config, page=page)
        # now render the page using the templates
        mytemplate = my_template_lookup.get_template(template_dict[page['template']])
        result = mytemplate.render(site=site.config, page=page, body=body_content)
        with open(filepath, "w") as outfile:
            outfile.write(result)
            outfile.close()
    # now we render the special blog files if a blog exists
    #print(site.posts)
    if site.config['blogdir']:
        # we have a blog
        # posts per indexpage:
        max_posts = 5
        os.makedirs(os.path.join(outpath, site.config['blogdir']), exist_ok=True)
        # create index pages with pagination
        postlist = list() # key, index
        # sort by date and time, newest on top
        for blogpost in site.posts:
            if VERBOSE:
                print(site.posts[blogpost])
            bp = site.posts[blogpost]
            postdatetime = datetime.datetime.strptime(str(bp['date']) + ', ' + str(bp['time']), "%Y-%m-%d, %H:%M")
            postlist.append((postdatetime, blogpost))
        sorted(postlist, reverse=True)
        # now only if we have a blogindex template:
        if 'template_blog_index' in site.config:
            if site.config['template_blog_index']:
                # we only run this if there is a blog index page template
                mytemplate = my_template_lookup.get_template(template_dict[site.config['template_blog_index']])
                all_posts = list()
                sub_list = list()
                postindex = 0
                pagination = 0
                for post in postlist:
                    postindex += 1
                    sub_list.append(site.posts[post[1]])
                    if postindex > max_posts:
                        pagination += 1
                        postindex = 0
                        all_posts.append(copy.deepcopy(sub_list))
                        sub_list = list()
                # append final sublist
                if pagination == 0:
                    pagination_list = "" # list of all blogindex pages
                else:
                    pagination_list = "index.html"
                    for index in range(pagination):
                        pagination_list.append("index%d.html" %(index+1))
                all_posts.append(copy.deepcopy(sub_list))
                print(all_posts)

                # render templates
                for index, sub_list in enumerate(all_posts):
                    print(sub_list)
                    # create page dict
                    front_matter= dict()
                    # set permalink based on filename and relative path
                    if index == 0:
                        filename = 'index.html'
                    else:
                        filename = "index%d.html" %index
                    filepath = os.path.join(outpath, site.config['blogdir'], filename)
                    # we assume that os.walk always uses "/" as path separator. On the mac it does.
                    htmlpath = dirpath.split(sitepath)[1] + SITE_DIR_SEPARATOR
                    # remove leading separator
                    if htmlpath[:len(SITE_DIR_SEPARATOR)] == SITE_DIR_SEPARATOR:
                        htmlpath = htmlpath[len(SITE_DIR_SEPARATOR):]
                    front_matter['permalink'] = htmlpath + os.path.splitext(filename)[0] + site.config[
                        'html extention']
                    # calculate relative path to root folder
                    relpath = "../" * (dirpath.split(sitepath)[1].count("/"))
                    front_matter['basepath'] = relpath
                    # print(relpath)
                    # add folder info
                    front_matter['folders'] = dict()
                    for folder in site.folders:
                        front_matter['folders'][folder] = relpath + site.folders[folder]
                    # now copy all that info to the pages dict in the site object
                    site.pages[front_matter['permalink']] = copy.deepcopy(front_matter)
                    # render index page
                    result = mytemplate.render(site=site.config, page=front_matter, posts=sub_list, pagination_list=pagination_list)
                    with open(filepath, "w") as outfile:
                        outfile.write(result)
                        outfile.close()
    return True


def main(ed_args=None):
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
    if ed_args:
        args = parser.parse_args(ed_args)
    else:
        # use sys.args
        args = parser.parse_args()
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
        # switch to directory to serve
        os.chdir(args.path)
        # start server
        import http.server
        import socketserver
        PORT = 8000
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", PORT), Handler)
        print("serving at port", PORT)
        httpd.serve_forever()
    else:
        raise 'unkown command'
    print(args)
    return(True)

if __name__ == '__main__':
    main()


