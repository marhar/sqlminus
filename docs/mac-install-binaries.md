Mac Binaries for sqlminus
=========================

I've put together an experimental binary installation for sqlminus.

download
--------

The files mentioned below are here.  Look here and grab the latest versions of
the files mentioned on this page.

    https://github.com/marhar/sqlminus/tree/master/dist

- small version

  If you have previously downloaded sqlminus before, you just need
  this tiny file.

    https://github.com/marhar/sqlminus/blob/master/dist/sqlminus-build20-small.tgz

- big version

  If you haven't downloaded sqlminus before, you need this version
  which included the necessary Oracle runtimes.

    https://github.com/marhar/sqlminus/blob/master/dist/sqlminus-build20-macos.tgz

install
-------

Depending on which tarball you downloaded, do one of these:

    cd /
    sudo tar xzf ~/Downloads/sqlminus.build20-small.tgz

    cd /
    sudo tar xzf ~/Downloads/sqlminus-build20-macos.tgz

test
----

    $ /usr/local/sqlminus/bin/sqlminus scott/tiger@orcl
    --------------------------------------------------
    | Welcome to sqlminus                            |
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
