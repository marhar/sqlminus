Binary installation of cx_Oracle and sqlminus on MacOS
======================================================

I've put together an experimental binary installation for
cx_Oracle and sqlminus.  No guarantees, but "it works for me".

download the tar file
---------------------

The lastest tarball is here:

   http://markharrison.net/sqlminus

cd to the root directory
------------------------

    cd /

untar the file
--------------

    sudo tar xzf ~/Downloads/sqlminus.current-macos.tgz

test
----

    $ /usr/local/sqlminus/bin/sqlminus scott/tiger@orcl
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

If this works, you can copy /usr/local/sqlminus/bin/sqlminus
to any directory in your path.
