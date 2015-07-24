.. image:: orapig.png

sqlminus -- a modern oracle command line client
-----------------------------------------------

usage:

    sqlminus [--sysdba] connstr          - interactive shell
    sqlminus [--sysdba] connstr  cmds... - execute cmds
    sqlminus [--sysdba] connstr  @file   - execute cmd in file.sql
    sqlminus [--sysdba] connstr
    (note: @ and --file stuff in flux and subject to change)

configuration:

    ~/.sqlminus holds connstr aliases.  format:   foo = 'foo/bar@baz'

special commands:

display
-------
    color     : color display mode
    mono      : monochrome display mode

execution
---------
    exec      : execute a procedure
    calls     : call a function returning a varchar2
    callc     : call a function returning a clob
    calln     : call a function returning a number

sysinfo
-------
    blockers  : show blocking sessions (works on RAC)
    info      : print random information about the connection
    du        : print disk usage

performance
-----------
    explain plan  : display an execution plan

context full text
-----------------
    ctexplain : display a ctx execution plan
    ctls      : display context indices

development
-----------
    ddl       : show ddl for object
    desc      : describe an object
    fkeys     : show nested child foreign key dependencies for a table
    tables    : list all user tables
    sqlid     : given sqlid, print sql statement (works on RAC)
    jobs      : list all jobs
    tron      : turn on dbms_output
    troff     : turn off dbms_output

misc
----
    nullstr   : set the value displayed for the null string
    rehash    : refresh table/column
    help      : print this help text
