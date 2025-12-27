import sys
print(sys.path)
import google
print(google.__file__)
try:
    import google.auth
    print(google.auth.__file__)
except ImportError as e:
    print(e)
