import argparse
import os
import sys
import shutil
import tarfile
from abc import ABCMeta, abstractmethod
from zipfile import ZipFile, is_zipfile
from tarfile import TarFile, is_tarfile


class CompressedFile(object):
    """Provide a uniform interface for all kinds of compressed files.

    It normalizes all zip interfaces to the TarFile interface, via
    adapter classes. An adapter should take a filename as its first
    argument and implement the full tarfile interface.

    This abstract class exists mostly as documentation so that you
    know what interface to create, we never actually check that your
    CompressedFile is a subclass of this one.
    """

    __metaclass__= ABCMeta

    @abstractmethod
    def __init__(self, fname):
        self.adaptee = CompressedFile(fname)

    @abstractmethod
    def getnames(self):
        """Return a list of top-level names in the compressed file
        """
        return self.adaptee.getnames()

    @abstractmethod
    def extractall(self):
        """Extract all files, with full paths, into dest
        """
        return self.adaptee.extractall()

    @abstractmethod
    def close(self):
        self.adaptee.close()

CompressedFile.register(TarFile)

class ZipFileAdapter(CompressedFile):

    def __init__(self, fname):
        self.adaptee = ZipFile(fname)

    def getnames(self):
        return self.adaptee.namelist()

    def extractall(self, dest='.'):
        return self.adaptee.extractall(dest)

    def close(self):
        self.adaptee.close()

class Debomber(object):
    """ Safely extract a compressed file, or clean up after one that's exploded.
    """

    def __init__(self, fname, Adapter=None):
        """Initialize an Debomber

        fname should be the (relative or absolute) path to a tarfile.

        Adapter is any class that satisfies the CompresedFile api.
        """

        if Adapter is not None:
            self.cfile = Adapter(fname)
        elif is_tarfile(fname):
            self.cfile = tarfile.open(fname)
        elif is_zipfile(fname):
            self.cfile = ZipFileAdapter(fname)
        else:
            root, ext = os.path.splitext(fname)
            raise ValueError(
                "CompressedFile does not know how to deal with {0} files"
                .format(ext)
                )

        self.root = os.path.abspath(os.path.dirname(fname))
        self.name = os.path.basename(fname)
        self.names = self.cfile.getnames()

    def __del__(self):
        self.cfile.close()

    def extract(self, path=".", warn=True):
        """ Extracts archive into path, defaulting to curdir.

        If warn is true, ask the user to confirm before extracting files with
        path components that would put it outside of path.
        """

        if warn:
            badfiles = []
            for name in self.names:
                dest = os.path.join(path, name)  # returns name if name is
                                                 # absolute path
                dest = os.path.abspath(dest)
                if os.path.commonprefix([path, dest]) != path:
                    badfiles.append(name)
            if badfiles:
                print "The following files in the archive have scary paths"
                for name in badfiles:
                    print "-", name
                choice = ''
                while choice not in ['y', 'n']:
                    choice = raw_input("Extract this archive? (y/n) ")
                if choice == 'n':
                    print "Extraction aborted"
                    return
        self.cfile.extractall(path)

    def extract_bomb(self, path=None):
        """ Extracts an archive bomb.

        Extracts files into a directory named after the archive file. This new
        directory will be created in the cwd unless path arg is supplied.

        Assumes is_bomb() is True.
        """

        dest = self._make_extraction_dir(path)
        self.extract(dest)

    def is_bomb(self):
        " Returns true if archive is a bomb. "
        if len(self.names) > 1 and os.path.commonprefix(self.names) == '':
            return True
        return False

    def has_exploded(self, root=None):
        """ Returns true if archive appears to have exploded in root.

        Defaults to checking in same directory as archive.
        """

        sploded = False

        if not self.is_bomb():
            return sploded

        if root is None:
            root = self.root

        # Check if the dir of the tarbomb has all its files
        dir_names = os.listdir(root)
        if len(dir_names) >= len(self.names):
            sploded_names = []
            for name in self.names:
                if name in dir_names:
                    sploded_names.append(name)
                else:
                    break

            if len(sploded_names) == len(self.names):
                sploded = True

        return sploded


    def clean(self, path=None):
        """Cleans up the directory.

        Does this by moving all 'sploded files into a dir with the basename of
        the cfile. This new directory will be created in the cwd unless path arg
        is supplied.

        Assumes that has_exploded() is True.
        """

        dest = self._make_extraction_dir(path)
        p_join = os.path.join
        for name in self.names:
            shutil.move(p_join(self.root, name), p_join(dest, name))

    def _make_extraction_dir(self, path=None):
        """ Creates and returns a directory named after the archive file

        If directory already exists then it's just returned.
        """

        dest, ext = os.path.splitext(self.name)
        if path:
            dest = os.path.join(path, dest)
        else:
            dest = os.path.join(self.root, dest)

        if not os.path.exists(dest):
            os.mkdir(dest)
        return dest


def parse_args(arg_list):
    parser = argparse.ArgumentParser(description=""" An archive extractor that
    can sensibly extract zip/tar bombs, and can clean up bomb sites from less
    sensible extraction endeavors.""")

    parser.add_argument('archive', metavar="ARCHIVE",
                        help="A zip or tar file to target.")

    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('-x', '--extract', action='store_true', help="""
    Extracts ARCHIVE. Extracts to a new directory if the archive is a bomb. The
    new directory is named after ARCHIVE.""")  # by removing the file extension,
                                               # but what is there is none?
    action.add_argument('-c', '--clean', action='store_true', help=""" Cleans up
    from an explosion of ARCHIVE. Moves all debris files to a new dir named
    after ARCHIVE.""")

    directory = parser.add_mutually_exclusive_group()
    directory.add_argument('-d', '--destination',
                       help="Put files in DESTINATION instead of cwd")

    return parser.parse_args(arg_list)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    dest = os.getcwd()
    debomb = Debomber(args.archive)
    if args.destination:
        dest = args.destination
    if args.extract:
        if debomb.is_bomb():
            debomb.extract_bomb(dest)
        else:
            debomb.extract(dest)
    elif args.clean:
        if debomb.has_exploded():
            debomb.clean()
        else:
            print "No bomb appears to have exploded here"
