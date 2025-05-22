# dump entire dicom ouput to stdout
import sys
import pydicom as pd

ifn = sys.argv[1]

d = pd.dcmread(ifn)

print(d)
