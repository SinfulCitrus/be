import pprint

from django.test import TestCase

# Create your tests here.

# Functions useful for debugging
ddebug = True
def ppdict(d_file):
    """
    Dump the contents of a dictionary file to dictdump.txt for debugging purposes
    """
    if not ddebug:
        return
    print("Dumping " + str(d_file.get('infoType')) + " to dictdump.txt")
    f = open("dictdump.txt","w")
    pprint.PrettyPrinter(indent=4,stream=f).pprint(d_file)
    f.close()