Installing cx_Oracle and sqlminus on MacOS
==========================================

- This documents how I got Oracle and Python working together on my Mac.
- I had problems using pip to install pre-built packages, so this is a
  source build.  Download the free xcode package from Apple to get the compiler.
- Version numbers may drift; adust accordingly.

Set Up a Build Area
===================

As per typical Unix builds, everything will be installed under one top-level
directory.  In addition we'll store the distribution files and build the
source there as well.


    export TOP=/usr/local/sqlminus  # where I built and installed
    mkdir -p $TOP/dist              # collect the install files here
    mkdir -p $TOP/src               # build things here
    export PATH=$TOP/bin:$PATH      # not necessary, but convenient for testing

Downloads
=========

Put these all in $TOP/dist

Oracle Instantclient 11
-----------------------

You need a free Oracle account to download these.

    http://www.oracle.com/technetwork/database/features/instant-client/index-097480.html
    instantclient-basic-macos.x64-11.2.0.4.0.zip
    instantclient-sdk-macos.x64-11.2.0.4.0.zip

Python 2.7
----------

    https://www.python.org/downloads/source/
    Python-2.7.9.tgz

Gnu Readline 6.3
----------------

For licensing reasons, the Mac doesn't come with GNU readline.   sqlminus
will run without GNU readline, but is a much happier experience with it.

    http://ftp.gnu.org/gnu/readline/
    readline-6.3.tar.gz

cx_Oracle 5.2
-------------

This is the most excellent Oracle interface package by the most excellent
Anthony Tuininga.

    https://pypi.python.org/pypi/cx_Oracle/5.2
    cx_Oracle-5.2.tar.gz

sqlminus
--------

It's nicest just to grab the entire sqlminus package from github, but
you actually only need two files.

    https://github.com/marhar/sqlminus/tree/master/sqlminus
    sqlminus.py
    sqlminus

Prep for Build
==============

Verify downloaded files
-----------------------

After downloading this is what you should have, modulo version changing.

    ls $TOP/dist
        Python-2.7.9.tgz
        cx_Oracle-5.2.tar.gz
        instantclient-basic-macos.x64-11.2.0.4.0.zip
        instantclient-sdk-macos.x64-11.2.0.4.0.zip
        readline-6.3.tar.gz
        sqlminus.py
        sqlminus

Untar source packages
---------------------

Put all these in src/.

    cd $TOP/src
    tar xzf ../dist/Python-2.7.9.tgz
    tar xzf ../dist/cx_Oracle-5.2.tar.gz
    tar xzf ../dist/readline-6.3.tar.gz

Set up Instantclient
====================

These will go into $TOP/intantclient_11_2.  You need to make one symlink
and set a couple of environment variables.

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
from the Mac App store.  If you download and install xcode, be sure and
run gcc once from the command line before you build.  It will ask you
to agree to the license.

readline
--------

    cd $TOP/src/readline-6.3
    ./configure --prefix=$TOP
    make
    make install
    (you can ignore any comments about ldconfig)

python
------

    cd $TOP/src/Python-2.7.9
    ./configure --prefix=$TOP
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

There's two files: sqlminus.py and sqlminus, a wrapper script
where you can set the necessary environment variables.  Copy
these to $TOP/bin

The only necessary change is to edit sqlminus to properly
set $TOP to your build area.  

Test
----

    $TOP/bin/sqlminus scott/tiger@orcl
    --------------------------------------------------
    | Welcome to sqlminus v2.1                       |
    | docs at: https://github.com/marhar/sqlminus    |
    | type "help" for help                           |
    --------------------------------------------------
    connecting to scott/tiger@orcl...
    scott@orcl> select 2+2 from dual;
    2+2 
    --- 
      4 
    (1 row, 0.031 sec)
