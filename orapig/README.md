.. image:: orapig.png

OraPIG -- Oracle Python Interface Generator
===========================================

.. TODO: for this doc, rearrange sections, label as beta version, note TODO items.

OraPIG creates Python interfaces for PL/SQL packages.
You can generate interfaces for your own packages or for the
Oracle system packages.

Quick Start
-----------

Suppose you have a package called *tiny* with a single procedure *p*::

  create or replace package tiny
  as
      procedure p(x in number);
  end tiny;

OraPIG will generate a wrapper class that will allow you to
use the package without having to use the various database
calls.  Instead, the wrapper class will be instantiated and
called just like any other Python class::

    class Tiny:
        def __init__(self,curs):  # instantiate class with a cursor
            ...
        def p(self,x):            # call procedure p(x)
            ...

Here's how it's used::

    import cx_Oracle
    import tiny
    conn = cx_Oracle.connect('scott/tiger')
    curs = conn.cursor()

    mytiny = tiny.Tiny(curs)
    mytiny.p(2)           # call a procedure
    curs.commit()         # not done automatically

Docstring Comments
------------------

Any comment lines in the package declaration that begin
with "--+ "will be copied into the docstrings in the
generated class.  Each procedure and function has its
own documentation, and there is a docstring comment
for the class as well.  There is not predefined format
for the docstrings -- text is copied "as is".
We're looking at perhaps using reStructured Text (reST) in
the docstring comments, but for now it's free-form.

Put the package docstring comment between the "create"
and "as" lines.  Put each procedure's or function's docstring
comments immediately preceding the declaration::

  create or replace package tiny
  --+ tiny : tiny example package
  --+ it's a really tiny package
  as
      --+ p(x) - some random procedure
      --+ parms:
      --+  x : some number
      procedure p(x in number);
  end tiny;

Committing Transactions
-----------------------

OraPIG does not commit any transaction.  There is an experimental
autocommit mode for use in writing application servers that
do not keep state across invocations.  Don't use it.

Vectorized Procedure Calls
--------------------------

Frequently you will need to repeatedly call a stored procedure
with different values.::

    for valuex in propertyList:          # call setproperty for all items
        mypkg.setproperty(name, value)   # in the list

This can be slow, since you are making a round trip call
to the database for every item in the list.

Instead, you can build up a list of parameters and call
the stored procedure with a that list of parameters.  Oracle
will iterate over the list on the server side, eliminating
a lot of network and procedure invocation overhead.

OraPIG generates a procedure which will do this for you
automatically.  If you have some code which repeatedly
calls a procedure::

    mypkg.setproperty('color', 'blue')
    mypkg.setproperty('flavor', 'sweet')
    mypkg.setproperty('hair', 'blonde')

you can replace it with a single call to the vectorized
function with "_V" appended to the name::

    mypkg.setproperty_V([['color','blue'],['flavor','sweet'],['hair','blonde']])

This will set the three properties with a single call to the database.

Note that you can't do this for functions, since there isn't
a way to get a list of return values back.

Reference Cursors
-----------------

Oracle has a "reference cursor" type which acts an an iterator
over a data set returned by a SQL query::

  open mycursor for select * from people;

The reference cursor can be returned from a PL/SQL function::

  return mycursor;

In your Python program, you can then use this returned reference
cursor to iterate over the rows returned from the query.  Suppose
you have a function which executes a query and returns its
associated reference cursor.  You can then use the returned cursor
like this::

    curs = mypkg.myfunc(x)
    for row in curs:
        print row

This can be much more efficient than executing a query and
returning the entire data set.

Function Restrictions
---------------------

There are several restrictions on functions.

- Functions cannot have side effects.  They cannot modify
  tables or have OUT or INOUT parameters.
- Functions cannot be invoked with the vectorized "_V" mechanism
  noted below.  This is because there is no syntax for returning
  a vector of return values.

Parameter Types
---------------

For functions and vectorized (_V) procedures,
all parameters must be IN parameters.

For procedures, IN, OUT, and IN OUT parameters are supported.

Data Types
----------

Here is a summary of supported PL/SQL data types and their
associated Python data types.

Note that cx_Oracle provides appropriate classes to represent most
Oracle data types.  OraPIG generates the appropriate code when
necessary to convert between the cx_Oracle types and the standard
Python types, reducing dependencies between your software and the
cx_Oracle package.

Here are the type mappings::

    Oracle        cx_Oracle        Python
    DATE          DATETIME
    NUMBER        NUMBER
    FLOAT         NUMBER
    REF CURSOR    CURSOR
    CURSOR        CURSOR
    VARCHAR2      STRING
    TIMESTAMP     TIMESTAMP

(datatype mapping is an ongoing project... please let us know if
you have any problems, ideas, suggestions, questions, etc.)

.. TODO: types in src, let's confirm these and make sure they are covered
   in test cases::

        'RAW'                   :'BINARY',
        'BFILE'                 :'BFILE',
        'BLOB'                  :'BLOB',
        'CLOB'                  :'CLOB',
        'CHAR'                  :'FIXED_CHAR',
        'unhandled_LONG_BINARY' :'LONG_BINARY',
        'unhandled_LONG_STRING' :'LONG_STRING',
        'unhandled_NCLOB'       :'NCLOB',
        'unhandled_OBJECT'      :'OBJECT',

.. TODO: these are the errors from running on sys pkgs. let's test
   and either fix or document that they don't work::

    KeyError: 'argtype'
    KeyError: 'BINARY_DOUBLE'
    KeyError: 'BINARY_FLOAT'
    KeyError: 'BINARY_INTEGER'
    KeyError: 'canon_sname'
    KeyError: 'col_cnt'
    KeyError: 'INTERVAL DAY TO SECOND'
    KeyError: 'line'
    KeyError: 'LONG RAW'
    KeyError: 'mline'
    KeyError: 'NVARCHAR2'
    KeyError: 'OBJECT'
    KeyError: 'object_type'
    KeyError: 'PL/SQL BOOLEAN'
    KeyError: 'PL/SQL RECORD'
    KeyError: 'ROWID'
    KeyError: 'TIMESTAMP WITH TIME ZONE'
    KeyError: 'UNDEFINED'

Arrays
------

PL/SQL supports an array data type.  This can be used to enhance
efficiency or better reflect your application's logical interface.

.. TODO: more verbiage on arrays

Example: keywords

Suppose you have a package that manipulates keywords that has a *set_keyword*
procedure.

.. TODO: show procedure body

To set a number of keywords on an identifier, you could
repeatedly call the procedure::

    k.set_keyword(id, 'blue')
    k.set_keyword(id, 'cold')
    k.set_keyword(id, 'spooky')

You could increase the efficiency of this multiple invocation by
using the vectorized form of the procedure::

    k.set_keyword_V([[id,'blue'],[id,'cold'],[id,'spooky']])

which would result in multiple invocations of the procedure in
a single call to the database.

..    TODO: show procedure body following nex para

Finally, you could receive the keywords as a PL/SQL array
and pass the procedure a list of the keywords you wish to set::

    k.set_keywords(id, ['blue','cold','spooky'])


Extending OraPIG
----------------

OraPIG has been implemented to be easily extensible to generating
interfaces for other languages.  I'm especially interested in C++
and PHP... please contact me if you know something about those
interfaces and are interested in working on them.

Running OraPIG
--------------

The usage of OraPIG is::

    orapig [options] packages...

You can generate interfaces for multiple packages.  They will
all be placed in the same output file.

The command line options are::

--help, -h                   show this help message and exit
--conn=CONN, -C CONN         database connection string (required)
--output=OUTPUT, -O OUTPUT   output file, defaults to stdout
--doc=DOCFILE                output document to this file (not implemented)
--lang=LANG                  language binding (currently wishful thinking)
--pass=PASS, -P PASS         database password (not implemented)
--dump                       dump parsed data (for debugging)
--sys                        the connection is a sys account

Platform Considerations
-----------------------

We've run this primarily on Linux.  There's no reason it
shouldn't run in any other environment (e.g. Windows, Mac) where cx_Oracle
is supported.  If you can verify a platform, please let us know and
we'll update it here.

Administrivia
-------------
:Version:
    1.0
:Download:
    http://code.google.com/p/orapig
:Documentation:
    http://markharrison.net/orapig
:Authors:
    Mark Harrison (mh@pixar.com)

    Bjorn Leffler (bjorn@pixar.com)
:License:
    Copyright 2008 Pixar, available under a BSD license.
:Support:
    Send questions to the cx_Oracle mailing list.  There's a
    link at: http://python.net/crew/atuining/cx_Oracle
:Dependencies:
    cx_Oracle, the Python interface for Oracle:
    http://python.net/crew/atuining/cx_Oracle/
:Installation:
    OraPIG is a standalone script.  Edit the #! line and put in
    an appropriate directory.
:Motto:
    "There's a Snake in my Oracle!"

This has been tested with Python 2.3 and 2.4, and Oracle 10.2.1.

Thanks
------

- to Anthony Tuininga (Mr. cx_Oracle) for doing such a fine job on cx_Oracle.
- to colleagues and early adopters (victims) Stas Bondarenko, Josh
  Minor, and Ralph Hill.
- to Mark Roddy for beta testing, patches, and password handling.
- to the smart and ever-helpful denizens of cx-oracle-users
  and comp.databases.oracle.misc.

TODO
----

- It would be nice to support other languages.  The code is
  written to be easily extensible.
- Generate reST documentation for the package.
- Ability to generate system package interfaces without logging
  in as sys.
- gen and distribute?:  import orapig.10g.db_output

Generating Package Documentation
--------------------------------

If you specify the --doc= option on the command line, the collected
doc strings will be written to this file in reST format.

Note: this is not done yet.

System Packages
---------------

You can generate a wrapper for a system package by using
the --sys command parameter and a connection to a system
account.  For example, to generate and interface to
DBMS_OUTPUT, do something like the following::

    orapig --sys --conn=sys/tiger -o dbms_output.py dbms_output

.. TODO: put some sample code here.

.. TODO: need to test dbms_output OUT parms.  They may not be passed
   back as expected to the calling routine.

.. TODO: pre-generate and ship as part of the distribution?

Examples
--------

The samples subdirectory contains some example packages and some
Python code which uses them.  Each of the samples has a SQL file
with the stored procedure and a test driver.  There are also
regression files for testing purposes.

:alltypes:
  tests all datatypes.

:tiny:
  the tiny example in the quick start.

:keyword:
  an asset keyword example.

FAQs
====

1.  Do you support standalone procedures and functions?

    No, read Ask Tom as to why you should put everything
    into packages.  Additionally, a package maps nicely
    to a class in most languages.

2.  Why do I get a PLS-00323 when compiling my PL/SQL package?

    You have different parameter names in your package and package
    body.  Use the same parameter names in both.

3.  Why is the docstring comment for the package below the
    declaration line when the procedure docstring comments
    are above the line?

    If the docstring comments are outside of the package definition
    they are not stored as part of the package definition.

4.  I can't get INOUT to work!

    Oracle spells INOUT as "IN OUT", two words.
