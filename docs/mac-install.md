Installing cx_Oracle and sqlminus on MacOS
==========================================

- This documents how I got Oracle and Python working together on my Mac.
- Version numbers may drift; adust accordingly.

Set Up a Build Area
===================

For example, suppose the top level build/install directory will be
/Users/mh/p/cx.

    export TOP=/Users/mh/p/cx
    mkdir -p $TOP/dist        # collect the install files here
    mkdir -p $TOP/src         # build things here
    export PATH=$TOP/bin:$PATH

Downloads
=========

Put them all in $TOP/dist

Oracle Instantclient 11
-----------------------

    http://www.oracle.com/technetwork/database/features/instant-client/index-097480.html
    instantclient-basic-macos.x64-11.2.0.4.0.zip
    instantclient-sdk-macos.x64-11.2.0.4.0.zip

Python 2.7
----------

    https://www.python.org/downloads/source/
    Python-2.7.9.tgz

Gnu Readline 6.3
----------------

    http://ftp.gnu.org/gnu/readline/
    readline-6.3.tar.gz

cx_Oracle 5.2
-------------

    https://pypi.python.org/pypi/cx_Oracle/5.2
    cx_Oracle-5.2.tar.gz

sqlminus
--------

    https://github.com/marhar/sqlminus/tree/master/sqlminus
    sqlminus

Prep for Build
==============

Verify downloaded files
-----------------------

    ls $TOP/dist
        Python-2.7.9.tgz
        cx_Oracle-5.2.tar.gz
        instantclient-basic-macos.x64-11.2.0.4.0.zip
        instantclient-sdk-macos.x64-11.2.0.4.0.zip
        readline-6.3.tar.gz
        sqlminus

Untar source packages
---------------------

    cd $TOP/src
    tar xzf ../dist/Python-2.7.9.tgz
    tar xzf ../dist/cx_Oracle-5.2.tar.gz
    tar xzf ../dist/readline-6.3.tar.gz

Set up Instantclient
====================

    cd $TOP
    unzip dist/instantclient-basic-macos.x64-11.2.0.4.0.zip 
    unzip dist/instantclient-sdk-macos.x64-11.2.0.4.0.zip 
    cd instantclient_11_2
    ln -s libclntsh.dylib.11.1 libclntsh.dylib

    # add these to .profile
    export ORACLE_HOME=$TOP/instantclient_11_2
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ORACLE_HOME
    export DYLD_LIBRARY_PATH=$ORACLE_HOME

Build/Installation
==================

Make sure you have gcc installed.  It's part of the free xcode package
from the Mac App store.  Run gcc once so you can accept the license.

readline
--------

    cd $TOP/src/readline-6.3
    ./configure --prefix=/Users/mh/p/cx
    make
    make install

python
------

    cd $TOP/src/Python-2.7.9
    ./configure --prefix=/Users/mh/p/cx
    make
    make install

cx_Oracle
---------

    cd $TOP/src/cx_Oracle-5.2
    $TOP/bin/python setup.py build
    # weird thing I don't understand:
    # you may get an error: ld: file not found: crt3.o
    # if so, cut and paste the last line (gcc or clang) and it will work
    gcc -bundle ...
    $TOP/bin/python setup.py install

Test the Installation
=====================

    $ $TOP/bin/python
    Python 2.7.9 (default, Jul 23 2015, 21:38:53) 
    >>> import cx_Oracle
    >>> conn=cx_Oracle.connect('scott/tiger@orcl')
    >>> curs=conn.cursor()
    >>> curs.execute('select 2+2 from dual')
    <cx_Oracle.Cursor on <cx_Oracle.Connection to scott@orcl>>
    >>> curs.fetchall()
    [(4,)]

sqlminus configuration
======================

Edit the first line of sqlminus to point the proper python, and
copy the sqlminus to your path.

    #!/usr/bin/env /Users/mh/p/cx/bin/python

    cp $TOP/dist/sqlminus $TOP/bin
    chmod +x $TOP/bin/sqlminus

Test
----

    $TOP/bin/sqlminus scott/tiger@orcl
    --------------------------------------------------
    Welcome to sqlminus
    docs at: https://github.com/marhar/sqlminus
    --------------------------------------------------
    connecting to scott/tiger@orcl...
    scott@orcl> select 2+2 from dual;
    2+2 
    --- 
      4 
    (1 row, 0.031 sec)
