#!/pixar/bin/python
# Test program for tinysample

import cx_Oracle
import tinysample

# Connect to Oracle
db = cx_Oracle.connect('apidemo_adm/oracle@templar')
cursor = db.cursor()

# Create an instance of Tinysample
mytiny = tinysample.Tinysample(cursor)

# Execute a function
result = mytiny.f1(1)
print "The return value of f1 was", result
