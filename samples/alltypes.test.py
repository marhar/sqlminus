#!/pixar/bin/python

import cx_Oracle
import alltypes

import datetime

date1 = datetime.datetime(2001, 1, 1, 1, 11, 11)
date2 = datetime.datetime(2002, 2, 2, 2, 22, 22)
date3 = datetime.datetime(2003, 3, 3, 3, 33, 33)

db = cx_Oracle.connect('apidemo_adm/oracle@templar')
cursor = db.cursor()

test = alltypes.Alltypes(cursor)

# Functions

result = test.f_float(1.1, 2.2, 3.3)
print "f_float(1.1, 2.2, 3.3) expecting 1.1 result: " + str(result)

result = test.f_number(1, 2, 3)
print "f_number(1, 2, 3) expecting 1.0 result: " + str(result)

result = test.f_varchar2("a", "b", "c")
print 'f_varchar2("a", "b", "c") expecting "a" result: "' + str(result) + '"'

result = test.f_date(date1, date2, date3)
print "f_date(...) expecting 2001... result: " + str(result)

# Procedures

result = test.p3_float(1.1, 2.2, 3.3)
print "p3_float(1.1, 2.2, 3.3) expecting [1.1, 1.1, 1.1] result: " + str(result)

result = test.p3_number(1, 2, 3)
print "p3_number(1, 2, 3) expecting [1, 1, 1] result: " + str(result)

result = test.f_varchar2("a", "b", "c")
print 'f_varchar2("a", "b", "c") expecting "a" result: "' + str(result) + '"'

result = test.p3_date(date1, date2, date3)
print "p3_date(...) expecting 3 times 2001... result: " + str(result)

# Procedures with arrays

result = test.p1_varchar2tbl(["bjorn", "mh"])
print "p1_varchar2tbl(...) result: " + str(result)

result = test.p1_floattbl([1.1, 2.2, 3.3])
print "p1_floattbl(...) result: " + str(result)

result = test.p1_numbertbl([1, 2, 3, 4, 5])
print "p1_numbertbl(...) result: " + str(result)

# Vectorized procedures with arrays

result = test.p1_varchar2tbl_v([[["aaa", "bbb"]], [["ccc", "ddd"]]])
print "p1_varchar2tbl_v(...) result: " + str(result)

result = test.p1_floattbl_v([ [[1.1, 2.2, 3.3]], [[4.4, 5.5, 6.6]] ])
print "p1_floattbl_v(...) result: " + str(result)

result = test.p1_numbertbl_v([ [[1, 1]] , [[2, 2]] , [[3,3]] ])
print "p1_numbertbl_v(...) result: " + str(result)

