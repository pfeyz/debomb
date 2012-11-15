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
    """ Cleans up after an archive that's exploded. """

    def __init__(self, fname, rootdir=None, Adapter=None):
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

        if rootdir is None:
            rootdir = os.getcwd()
        self.root = os.path.abspath(rootdir)
        self.names = self.cfile.getnames()
        self.archive_fn = os.path.basename(fname)

    def __del__(self):
        self.cfile.close()

    def has_exploded(self, root=None):
        """ Returns true if archive appears to have exploded in root.

        Defaults to checking in same directory as archive.
        """

        sploded = False

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
        """Cleans up the directory.

        Does this by moving all 'sploded files into a dir with the basename of
        the cfile. This new directory will be created in the cwd unless path arg
        is supplied.

        Assumes that has_exploded() is True.
        """

        dest = self._make_extraction_dir()
        p_join = os.path.join
        for name in self.names:
            shutil.move(p_join(self.root, name), p_join(dest, name))

    def _make_extraction_dir(self):
        """ Creates and returns a directory named after the archive file

        If directory already exists then it's just returned.
        """

        dest, ext = os.path.splitext(self.archive_fn)
        dest = os.path.join(self.root, dest)

        if not os.path.exists(dest):
            os.mkdir(dest)
        return dest


def parse_args(arg_list):
    parser = argparse.ArgumentParser(description=""" An archive extractor that
    can sensibly extract zip/tar bombs, and can clean up bomb sites from less
    sensible extraction endeavors.""")

    parser.add_argument('archive', metavar="ARCHIVE",
                        help="The archive file to target.")

    return parser.parse_args(arg_list)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    dest = os.getcwd()
    debomb = Debomber(args.archive)
    if debomb.has_exploded():
        debomb.clean()
    else:
        print "No bomb appears to have exploded here"
