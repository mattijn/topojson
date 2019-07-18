__version__ = "1.0rc2"
__doc__ = "Encode geographic data as topology in Python! 🌍"


from .core.topology import Topology


def topology(data):
    # import warnings

    # warnings.warn(
    #     (
    #         "\nThe function topojson.topology() is deprecated.\n\n"
    #         "You have to use topojson.Topology() since v1.0rc3."
    #     ),
    #     DeprecationWarning,
    #     stacklevel=2,
    # )
    return Topology(data).to_dict()

