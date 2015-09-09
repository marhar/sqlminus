Mac Binaries for sqlminus
=========================

I've put together an experimental binary installation for sqlminus.

download
--------

- small version

  If you have previously downloaded sqlminus before, you just need
  this tiny file.

  http://markharrison.net/sqlminus/sqlminus.current-macos-small.tgz

- big version

  If you haven't downloaded sqlminus before, you need this version
  which included the necessary Oracle runtimes.

   http://markharrison.net/sqlminus/sqlminus.current-macos-full.tgz


install
-------

Depending on which tarball you downloaded, do one of these:

    cd /
    sudo tar xzf ~/Downloads/sqlminus.current-macos-small.tgz

    cd /
    sudo tar xzf ~/Downloads/sqlminus.current-macos-full.tgz

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
