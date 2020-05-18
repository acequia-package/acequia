""" Funtions for working with files and directories """
import warnings
import os.path
import errno
import os

def cleardir(dirpath,filetype=None):
    """ delete all existing files in directory 

    Parameters
    ----------
    dirpath : str
        path to directory with files

    filetype : str, optional
        type of files to delete

    """
    for filename in os.listdir(dirpath):

        fpath = os.path.join(dirpath, filename)
        try:
            if os.path.isfile(fpath) or os.path.islink(fpath):
                if filetype is None:
                    os.unlink(fpath)
                elif filetype in os.path.splitext(filename)[1]:
                    os.unlink(fpath)
            #elif os.path.isdir(fpath):
            #    shutil.rmtree(fpath)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
