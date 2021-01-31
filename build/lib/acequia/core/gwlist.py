

"""

Base object for maintaining a groundwater series iterator

T.J. de Meij october 2019

""" 


class GwList():
    """
        Groundwater series list container for iterating groundwate rseries
    """

    def __repr__(self):
        return (f'{self.__class__.__name__}()')

    def __init__(self):
        pass

    @classmethod
    def from_dinofiles(cls,filedir=None,fileplist=None):
        """ 
        read tno dinoloket csvfiles

        parameters
        ----------
        filedir : str
        filelist : list


        returns
        -------
        result : dinofiles iterator

        """

        return cls()
