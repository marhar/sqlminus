sqlminus -- a modern oracle command line client
-----------------------------------------------

usage:

    sqlminus [--sysdba] connstr          - interactive shell
    sqlminus [--sysdba] connstr  cmds... - execute cmds
    sqlminus [--sysdba] connstr  @file   - execute cmd in file.sql
    sqlminus [--sysdba] connstr
    (note: @ and --file stuff in flux and subject to change)

commands:

  admin:
       blockers : show any blockers (on a RAC)
             du : print disk usage
     tablestats : show some stats on tables

  devel:
      ctexplain : explain a ctx search
           ctls : list context indices
    dbms_output : turn dbms_output on or off
            ddl : show ddl for an object
           desc : describe an object, e.g. desc mytable
          fkeys : show foreign key children of a table
        jobhist : list history for the job
           jobs : list jobs for this user
          sqlid : print text for sql id
        userenv : print SYS_CONTEXT('USERENV',...)

  query:
          callc : call clob function, e.g. callc clobfunc
          calln : call number function, e.g. calln mod(5,2)
          callv : call varchar2 function, e.g. callv lower('ABC')
         commit : commit ...
         delete : delete ...
           exec : execute a procedure, e.g. exec dbms_lock.sleep(3)
         insert : insert ...
        nullstr : set the null string
       rollback : rollback ...
         select : select ...
         tables : print a list of the tables
         update : update ...

  sqlminus:
           help : print some help stuff
           info : print some info about the connection
              p : print current command buffer
           quit : quit the program
              v : (experimental) load current command buffer into editor

  terminal:
          color : set color output
           mono : set monochrome output
         resize : turn resize on or off EXPERIMENTAL
           sane : set the terminal width to a sane value EXPERIMENTAL
