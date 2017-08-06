import unittest, tempfile, os, shutil
import hashlib, pathlib, inspect, subprocess
import sys



def hash_bytestr_iter(bytesiter, ashexstr=True):
    hasher = hashlib.sha256()
    for block in bytesiter:
        hasher.update(block)
    return (hasher.hexdigest() if ashexstr else hasher.digest())

def file_as_blockiter(filename, blocksize=4069):
    with open(filename, 'rb') as afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)
        afile.close()


class TestTestSite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a temporary directory for test"""
        cls.temppath = os.path.join(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        print('deleting ', cls.temppath)
        shutil.rmtree(cls.temppath)

    def test_test_site(self):
        import edward
        # create test site
        edward.new_site(self.temppath, 'test') # we use the test template
        # test that all is there
        # get all from source
        # get template path
        print('Test if template files are copied correctly')
        templatepath = os.path.join(str(pathlib.PurePath(inspect.getfile(edward.create_default_files)).\
                                        parents[1].joinpath('templates')), 'test/')
        srcdict = dict()
        for dirpath, dirnames, filenames in os.walk(templatepath):
            for f in filenames:
                # get sha1 for each file
                srcdict[os.path.join(dirpath.split(templatepath)[1],f)] = \
                    hash_bytestr_iter(file_as_blockiter(os.path.join(dirpath,f)))
            for d in dirnames:
                srcdict[os.path.join(dirpath.split(templatepath)[1], d)] = "d"
        #print(srcdict)
        # test all in dest:
        for k in srcdict:
            #print(k)
            #print(os.path.join(self.temppath, k))
            if srcdict[k] == "d":
                # it is a directory
                self.assertEqual(os.path.exists(os.path.join(self.temppath, k)), True)
            else:  # it is a file
                #print("File!")
                self.assertEqual(srcdict[k], hash_bytestr_iter(file_as_blockiter(os.path.join(self.temppath, k))))
                #self.assertEqual(srcdict[k], hash_bytestr_iter(file_as_blockiter(os.path.join(templatepath, k))))
        print('Test rendering')
        sys.argv.append('render')
        sys.argv.append(self.temppath)
        #edward.main([ 'render', self.temppath])
        edward.main()
        print('Test rendering result')
        #srcdict = dict()
        #for dirpath, dirnames, filenames in os.walk(os.path.join(self.temppath,'build')):
        #    for f in filenames:
        #        # get sha1 for each file
        #        srcdict[os.path.join(dirpath.split(self.temppath+'/')[1], f)] = \
        #            hash_bytestr_iter(file_as_blockiter(os.path.join(dirpath, f)))
        #    for d in dirnames:
        #        srcdict[os.path.join(dirpath.split(self.temppath+'/')[1], d)] = "d"
        # import json
        # with open('out.json', 'w') as outfile:
        #    json.dump(srcdict, outfile)
        #    outfile.close()
        srcdict = {"build/deep/down/index.html": "2eef7cbb676c805d0f922d862d865751c384a4f6fb2769add1bb63eb403ab925",
                    "build/css": "d",
                    "build/index.html": "d094be7bd32c337b2c7a0757378835dbb8c65b19764409d72e4d3e9d438a0217",
                    "build/deep/down": "d",
                    "build/deep": "d",
                    "build/images": "d",
                    "build/deep/down/test.html": "bf55dc4804a9690ffb00808e6357fc52b270df0ffc9203a888c6399118573308",
                    "build/css/site.css": "39b6410992aeab5be567f9f493213a8eebeae07072cf2a233773b60bb69858c0",
                    "build/js": "d"}
        for k in srcdict:
            if srcdict[k] == "d":
                # it is a directory
                self.assertEqual(os.path.exists(os.path.join(self.temppath, k)), True)
            else:  # it is a file
                self.assertEqual(srcdict[k], hash_bytestr_iter(file_as_blockiter(os.path.join(self.temppath, k))))

        def test_commandline(self):
            from edward.command_line import main
            main()

if __name__ == '__main__':
    unittest.main()