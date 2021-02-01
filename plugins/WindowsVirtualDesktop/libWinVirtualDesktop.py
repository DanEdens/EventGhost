def __bootstrap__():
    global __bootstrap__
    global __loader__
    global __file__
    import sys
    import imp
    __file__ += 'd'
    
    del __bootstrap__
    del __loader__
    
    mod = imp.load_dynamic(__name__, __file__)
    
    sys.modules[__name__] = mod
    
__bootstrap__()