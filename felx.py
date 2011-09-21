import argparse
import os
import sys
import shutil
from abc import ABCMeta, abstractmethod
from zipfile import ZipFile, is_zipfile
from tarfile import TarFile, is_tarfile


def CompressedFile(object):
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

def Felx(object):
    """Safely extract a CompressedFile
    """

    def __init__(self, fname, Adapter=None):
        """Initialize a Felx bot.

        fname should be the (relative or absolute) path to a tarfile.

        Adapter is any class that satisfies the CompresedFile api.
        """

        if Adapter is not None:
            self.cfile = Adapter(fname)
        elif is_tarfile(fname):
            self.cfile = TarFile(fname)
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

    def sploded(self, root=None):
        sploded = False

        # we can't shorten things below 1 or 2
        if len(self.names) <2:
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

    def clean(self):
        """Cleans up the directory

        Does this by moving all 'sploded files into a dir with the
        basename of the cfile

        Assumes that sploded() is True
        """

        dest, ext = os.path.splitext(self.name)
        dest = os.path.join(self.root, self.name)

        if not os.path.exists(dest, 0755):
            os.mkdir(dest)

        p_join = os.path.join
        for name in self.names:
            shutil.move(p_join(self.root, name), p_join(dest, name))

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

def clean_bomb_site(archive, destination):
    """ Takes the files that exploded from archive and moves them to a new
    directory in destination.

    archive is a filename and source and destination are both directory names.

    """
    print("Cleaning up after", archive, "moving debris to", destination)
    raise NotImplementedError

def extract(filename, dest):
    print("Extracting", filename, "to", dest)
    raise NotImplementedError

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    dest = os.getcwd()
    if args.destination:
        dest = args.destination
    if args.extract:
        extract(args.archive, dest)
    elif args.clean:
        clean_bomb_site(args.archive, dest)
