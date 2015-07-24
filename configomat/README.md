.. image:: orapig.png

OraPIG Configomat -- Configuration Generator
==============================================

OraPIG Configomat takes configuration data stored in a
database file and converts it into Python or C/C++
data structures.  This data can be included in application
programs to allow access to the global configuration
without having to connect to the database.
This provides the best of both worlds:

- Configuration data can be stored in the database

    - centralized location makes it easy to find
    - it's easy to edit using your database tools
    - language-independent configuration format
    - configuration information accessible within the database

- The data is also easily accessible by programs which do not
  access the database.  This has several potential advantages:

    - speed. a small program might spend more time connecting to the
      database than actually doing its work.

    - independence.  the program does not need to be able to connect
      to the database in order to run nor include a database interface
      if it is not needed for any other purpose.

    - bootstrapability.  a common configuration parameter is the
      database connection string, which you want to be able to
      get without having to connect to the database.

diagram::

    .       database table --> python module --> python applications
    .                      --> C/C++  module --> C/C++  applications

Specifying the Configuration Table
==================================

Just about any table can be converted by the configomat.

- The table must have a primary consisting of a single column.
- Table and column comments will be carried forward into the generated
  code.  Document your work!

Let's look at an example table called "netservices".  It's a
configuration table for some hypothetical network service
and has these columns::

        name : service name.  this is the primary key.
        host : hostname.
        port : ip port.
       admin : email of administrative contact.
 description : description of the service.

and four rows of data::

     table:  netservices

     name     | host   | port | admin | description
    ----------+--------+------+-------+-----------------------------
     xmap     | ajax   | 2305 | steve | shared xmap validator
     qman     | ajax   | 1999 | bob   | queue manager
     thumbs01 | xerxes | 1022 | bob   | primary thumbnail server
     thumbs02 | ajax   | 1022 | bob   | secondary thumbnail server

Generating the Interfaces
=========================

The simplest commands to generate the Python and C/C++ interfaces are::

    configomat --conn=orapig/orapig --table=netservices --lang=python
    configomat --conn=orapig/orapig --table=netservices --lang=gperf

The only required parameters are the database connection string
and the table name.  Full command line detail appear below.

Contents of the Python Module
=============================

There are three things in the generated python module:

- generated documentation on the module, extracted from the oracle
  table and column comments.

- **keys**, a list of all the primary key data in the table

- **data**, a dictionary of dictionaries representing the data in the
  table.  Access the data as data[keyname][columname].

All data from the table is represented as strings, regardless of
the column type in the table.

Using the Python Interface
==========================

To use the file, just import it in the usual manner::

    >>> import netservices

**keys** is a list of all the keys.  This is the data in the table's
primary key::

    >>> netservices.keys
    ['qman', 'thumbs01', 'thumbs02', 'xmap']

**data** is a dictonary indexed by the elements in keys::

    >>> from pprint import pprint
    >>> pprint(netservices.data)
    {'qman': {'admin': 'bob',
              'description': 'queue manager',
              'host': 'ajax',
              'port': '1999'},
     'thumbs01': {'admin': 'bob',
                  'description': 'primary thumbnail server',
                  'host': 'xerxes',
                  'port': '1022'},
     'thumbs02': {'admin': 'bob',
                  'description': 'secondary thumbnail server',
                  'host': 'ajax',
                  'port': '1022'},
     'xmap': {'admin': 'steve',
              'description': 'shared xmap validator',
              'host': 'ajax',
              'port': '2305'}}

You can access a particular configuration record by subscripting with
one the key names::

    >>> pprint(netservices.data['xmap'])
    {'admin': 'steve',
     'description': 'shared xmap validator',
     'host': 'ajax',
     'port': '2305'}

and access a particular field by subscripting again with the column name::

    >>> netservices.data['xmap']['port']
    '2305'

Contents of the C/C++ Module
============================

- A struct called *table*\ _tbl.  It has a char* member for every
  column in the table.

- A statically initalized array of strings called *tablename*\ _keys which
  contains the key data.

- A perfect hash function *tablename*\ _lookup() that maps the keys to
  struct *table*\ _tbl pointers.

- A set of generated functions *tablename*\ _get\ *colname* () that will
  return that column's data for the specified key.

- A test main() to verify correct operation and serve as an example
  of how to access the data.

All data from the table is represented as strings, regardless of
the column type in the table.

The configomat uses gnu gperf program, details below.

Using the C/C++ Interface
=========================

Include the generated header file::

    #include "netservices.h"

netservices_keys is an array of all the keys::

    int i;
    int nkeys = sizeof(netservices_keys[0]) / sizeof(netservices_keys);
    for (i = 0; i < nkeys; ++i)
        printf("%d. %s\n", i, netservices_keys[i]);

output::

   1. qman
   2. thumbs01
   3. thumbs02
   4. xmap

The functions netservices_gethost() and netservices_getport() will
return the host and port parameters for the given key.  Similar
functions exist for each of the columns.  They take one parameter
which is the key, and return either a string or NULL if the key
does not exist::

    char *host = netservices_gethost("qman");
    char *port = netservices_getport("arglebarg"); /*does not exist*/
    if (host != NULL)
        printf("host: %s\n", host);
    printf("port: %p\n", port);

output::

   host: ajax
   port: (nil)

To compile the test program, pass -DTEST to the compiler.

Running Configomat
==================

The usage of OraPIG Configomat is::

    configomat [options]

The command line options are::

    --help, -h                   show this help message and exit
    --conn=CONN, -C CONN         database connection string (required)
    --table=TABLENAME            generate bindings for this table (required)
    --lang=LANG                  language binding (currently gperf or python)
    --output=OUTPUT, -O OUTPUT   output file, defaults to stdout
    --pass=PASS, -P PASS         database password (not implemented)
    --header=file, -H file       generate C/C++ header file
    --dump                       dump parsed data and exit (for debugging)

Example Makefile
================

Here are some example Makefile entries::

    config: netservices.py netservices.o

    netservices.py:
      configomat.py --conn=orapig/orapig --table=netservices -O netservices.py

    netservices.o:
      configomat.py --conn=orapig/orapig --table=netservices --lang=gperf -O netservices.gperf -H netservices.h
      gperf -t --ignore-case --output=netservices.c netservices.gperf
      $(CC) $(CFLAGS) -c netservices.c

    test:
      configomat.py --conn=orapig/orapig --table=netservices --lang=gperf -O netservices.gperf -H netservices.h
      gperf -t --ignore-case --output=netservices.c netservices.gperf
      $(CC) $(CFLAGS) -DTEST netservices.c -o netservices-test
      ./netservices-test

    clean:
      rm -f netservices.py netservices.pyc
      rm -f netservices.gperf netservices.h netservices.c netservices.o netservices-test

Gperf Note
==========

The C/C++ bindingings use the Gnu perfect hash function generator gperf.
Details, docs and downloads available here:

-    http://www.gnu.org/software/gperf

Administrivia
=============

Configomat is part of OraPIG, the Oracle Python Interface Generator.

    :Version:
        1.0
    :Download:
        http://code.google.com/p/orapig
    :Documentation:
        http://markharrison.net/orapig
    :Author:
        Mark Harrison (mh@pixar.com)
    :License:
        Copyright 2008 Pixar, available under a BSD license.
    :Support:
        Send questions to the cx_Oracle mailing list.  There's a
        link at: http://python.net/crew/atuining/cx_Oracle
    :Dependencies:
        cx_Oracle, the Python interface for Oracle:
        http://python.net/crew/atuining/cx_Oracle
        The C/C++ language binding uses gperf, the gnu perfect hash generator:
        http://www.gnu.org/software/gperf
    :Installation:
        Configomat is a standalone script.  Edit the #! line and put in
        an appropriate path.
    :OraPIG Motto:
        "There's a Snake in my Oracle!"

This has been tested with Python 2.3-2.7 and Oracle 10-11.

Thanks
======

- to Anthony Tuininga (Mr. cx_Oracle) for doing such a fine job on cx_Oracle.
- to the smart and ever-helpful denizens of cx-oracle-users
  and comp.databases.oracle.misc.
- to colleague Mike Sundy who inspired the need for this program.
- Douglas C. Schmidt and the rest of the gperf contributors.
- Joy Sikorski, who taught me how to draw a cute pig.  Visit her
  site and unlock your creativity! http://www.joysikorski.com

TODO
====

- allow overriding of column names to avoid reserved words
  in the target language.
