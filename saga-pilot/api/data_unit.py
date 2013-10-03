

from unit import Unit


# ------------------------------------------------------------------------------
#
class DataUnit (Unit) :
    """ 
    DataUnit class.
    """

    # --------------------------------------------------------------------------
    #
    def __init__ (self, uid=None) : 

        Unit.__init__ (self, uid)


    # --------------------------------------------------------------------------
    #
    def import_data (self, src, ttype=SYNC) :
        """
        For a data unit which does not point to PFNs yet, create a first PFN as
        copy from the given src URL.

        FIXME: what happens if we already have PFNs?
        """
        # FIXME
        pass


    # --------------------------------------------------------------------------
    #
    def export_data (self, tgt, ttype=SYNC) :
        """
        Copy any of the data_unit's PFNs to the tgt URL.
        """
        # FIXME
        pass


    # --------------------------------------------------------------------------
    #
    def remove_data (self, ttype=SYNC) :
        """
        Removes the data.  Implies cancel ()
        """
        # FIXME
        pass


# ------------------------------------------------------------------------------
#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

