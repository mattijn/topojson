from functools import singledispatch, update_wrapper


def methdispatch(func):
    """
    The singledispatch function only applies to functions. This function creates a 
    wrapper around the singledispatch so it can be used for class instances.
    
    Returns
    -------
    dispatch
        dispatcher for methods
    """

    dispatcher = singledispatch(func)

    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)

    wrapper.register = dispatcher.register
    update_wrapper(wrapper, dispatcher)
    return wrapper
