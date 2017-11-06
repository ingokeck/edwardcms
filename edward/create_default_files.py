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

import os, sys, pathlib
import ruamel.yaml as yaml
import unittest, tempfile
import shutil, inspect
from distutils.dir_util import copy_tree

def create_folders(mypath):
    """Create all default folders on mypath for an edward site"""
    folders = ['_templates', '_posts', '_python' ,'css', 'js', 'images'] # the folders to be created
    for f in folders:
        if not os.path.exists(os.path.join(mypath, f)):
            os.makedirs(os.path.join(mypath, f))
    return (True, folders)

def create_conf(mypath):
    """Create the default yaml config file for an edward site"""
    d = dict()
    d["url"]=''
    d["site title"]='My New Edward Website'
    d["filter"]=['markdown']
    d["exclude"] = ['_*']
    d["render"] = []
    d["blogposts"] = ''
    d["blogdir"] = ''
    d["template_blog_index"] = ''
    d["interpret"] = ['*.md', '*.html']
    d["html extention"] = '.html'
    d["language modifier"] = {"de":"_de","es":"_es"}
    d["language default"] = "en"
    with open(mypath, 'w') as outfile:
        yaml.safe_dump(d, outfile)
        outfile.close()
    return (True, d)

def copy_files(mypath, templatename='simple'):
    """
    Copy all default files in the template directory to the new path
    :param mypath: Path of Edward site
    :param templatename: Name of the template to be copied
    :return: True if all worked well
    """
    # get template path
    templatepath = pathlib.PurePath(inspect.getfile(copy_files)).parents[1].joinpath('templates')
    #print(templatepath)
    copy_tree(src=str(templatepath.joinpath(templatename)), dst=mypath)
    return True

class TestFilesCreation(unittest.TestCase):
    """Tests for folder and default file creation"""

    def setUp(self):
        """Create a temporary directory for test"""
        self.temppath = tempfile.mkdtemp()

    def tearDown(self):
        """Remove temporary director for test"""
        os.removedirs(self.temppath)

    def test_configfile(self):
        testfile = os.path.join(self.temppath, 'site.yaml')
        result, d = create_conf(testfile)
        with open(testfile) as infile:
            n = yaml.safe_load(infile)
            infile.close()
        os.remove(testfile)
        self.assertEqual(d,n)  # what we read from the file should be the same we wanted to write in it

    def test_create_folders(self):
        result, folders = create_folders(self.temppath)
        for f in folders:
            self.assertTrue(os.path.exists(os.path.join(self.temppath, f)))  # every folder should exist
            os.rmdir(os.path.join(self.temppath, f))  # clean up after test

if __name__ == '__main__':
    create_conf('temp')
