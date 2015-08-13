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

    --------------------------------------------------
    | Welcome to sqlminus                  build<18> |
    | docs: https://github.com/marhar/sqlminus       |
    | type "help" for help                           |
    --------------------------------------------------
    connecting to marhar@orcl...
    marhar@orcl> help
    
    sqlminus -- sqlplus minus. the features? minus the suck? you be the judge!
    
        https://github.com/marhar/sqlminus  :  share and enjoy!
        Mark Harrison, marhar@gmail.com     :
    
    commands:
      admin
         blockers : show any blockers (on a RAC)
               du : print disk usage
      devel
        ctexplain : explain a ctx search
             ctls : list context indices
              ddl : show ddl for an object
             desc : describe an object, e.g. desc mytable
            fkeys : show foreign key children of a table
          jobhist : list history for the job
             jobs : list jobs for this user
            sqlid : print text for sql id
            troff : turn off dbms_output
             tron : turn on dbms_output
          userenv : print SYS_CONTEXT('USERENV',...)
      query
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
      sqlminus
             help : print some help stuff
             info : print some info about the connection
             quit : quit the program
      terminal
            color : set color output
             mono : set monochrome output
           resize : turn resize on or off EXPERIMENTAL
             sane : set the terminal width to a sane value EXPERIMENTAL
    marhar@orcl> 
