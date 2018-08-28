from functools import singledispatch, update_wrapper

def methdispatch(func):
    """
    create wrapper around singledispatch to be used for 
    class instances
    """
    dispatcher = singledispatch(func)
    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)
    wrapper.register = dispatcher.register
    update_wrapper(wrapper, dispatcher)
    return wrapper