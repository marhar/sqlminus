#!/usr/bin/env python
"""
sqlminus -- sqlplus minus. the features? the suck? you be the judge!

usage:
    sqlminus [--sysdba] connstr          - interactive shell
    sqlminus [--sysdba] connstr  cmds... - execute cmds
    sqlminus [--sysdba] connstr  @file   - execute cmd in file.sql
    sqlminus [--sysdba] connstr
    (note: @ and --file stuff in flux and subject to change)

configuration:
    ~/.sqlminus holds connstr aliases.  format:   foo = 'foo/bar@baz'

special commands:
  display:
    color     : color display mode
    mono      : monochrome display mode
  execution:
    exec      : execute a procedure
    calls     : call a function returning a varchar2
    callc     : call a function returning a clob
    calln     : call a function returning a number
  sysinfo:
    blockers  : show blocking sessions (works on RAC)
    info      : print random information about the connection
    du        : print disk usage
  performance:
    explain   : display an execution plan
  context full text:
    ctexplain : display a ctx execution plan
    ctls      : display context indices
  development:
    ddl       : show ddl for object
    desc      : describe an object
    fkeys     : show nested child foreign key dependencies for a table
    tables    : list all user tables
    sqlid     : given sqlid, print sql statement (works on RAC)
    jobs      : list all jobs
    tron      : turn on dbms_output
    troff     : turn off dbms_output
  misc:
    nullstr   : set the value displayed for the null string
    rehash    : refresh table/column
    help      : print this help text

features:
    readline editing
    saves readline data across sessions
    (semi)intelligent tab completion for tables, columns
    nice table formatting
    single file, easy to install

author:
    Mark Harrison, mh@pixar.com

license and download:
    bsd-ish.  see orapig package for complete text.
    sqlminus is part of the orapig package.  It has eclipsed its
    siblings so now orapig is part of the sqlminus package.
    https://github.com/marhar/sqlminus
"""

import sys,os,re,time,cmd,collections,readline,signal,argparse,socket
import getpass,shlex,cx_Oracle

class OracleCmd(cmd.Cmd):

    #-------------------------------------------------------------------
    def __init__(self,connstr,sysdba):
        """OracleCmd init"""
        cmd.Cmd.__init__(self)
        if sysdba is True:
            self.conn = cx_Oracle.connect(connstr,mode=cx_Oracle.SYSDBA)
            print '----------------------------------------------------------'
            print '| DUMBASS ALERT: logged in as sysdba, dont be a DUMBASS! |'
            print '----------------------------------------------------------'
        else:
            self.conn = cx_Oracle.connect(connstr)
        self.conn.client_identifier='sqlminus'
        self.conn.clientinfo='hello'
        self.conn.module='hello2'
        self.curs = self.conn.cursor()
        self.nullstr = '-';
        self.cmds=[]
        self.helptext=''
        for line in __doc__.split('\n'):
            words=line.split()
            if len(words) > 1 and words[1]==':':
                self.cmds.append(words[0])
                self.helptext += line+'\n'

        self.cmd=''
        self.do_rehash()
        self.do_mono()
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    #-------------------------------------------------------------------
    def clearinput(self):
        """clear the input state"""
        self.cmd=''

    #-------------------------------------------------------------------
    def oraprint(self,desc,rows):
        """nicely print a query result set"""
        # get the max width and type of each column,
        # use that to build fmt strings to print the header and rows

        maxlen=[len(i[0]) for i in desc]
        types=[i[1] for i in desc]
        for r in rows:
            r2=[self.nullstr if i is None else i for i in r]
            for i in range(len(desc)):
                ts=str(r2[i])
                tmpl=len(ts)
                if maxlen[i]<tmpl:
                    maxlen[i]=tmpl
        fmt0=''
        fmt1=''
        for (tt,mm) in zip(types,maxlen):
            if tt==cx_Oracle.NUMBER:
                minus=''
            else:
                minus='-'
            fmt0+='%%-%ds '%(mm)
            fmt1+='%%%s%ds '%(minus,mm)

        # header
        line=fmt0%tuple([i[0].lower() for i in desc])
        print line
        print re.sub('[^ ]','-',line)

        # rows
        x=0
        for r in rows:
            r2=[self.nullstr if i is None else i for i in r]
            line=fmt1%tuple(r2)
            print '%s%s'%(self.colors[x],line)
        print self.colors[2]

    #-------------------------------------------------------------------
    def run(self):
        """execute a command and display results"""
        try:
            self.cmd=re.sub('; *$','',self.cmd)
            cmdw=self.cmd.split()
            t0=time.time()
            rc=self.curs.execute(self.cmd)

            if len(cmdw) >=2 and cmdw[0]=='explain' and cmdw[1]=='plan':
                c2=self.conn.cursor()
                c2.execute("select * from table(dbms_xplan.display)")
                self.oraprint(c2.description,c2.fetchall())
            else:
                elapsed=time.time()-t0
                if rc!=None:
                    results=self.curs.fetchall()
                    self.oraprint(self.curs.description,results)
                if self.curs.rowcount >= 0:
                    print '(%d rows, %.3f sec)'%(self.curs.rowcount, elapsed)
                else:
                    print '(%.3f sec)'%(elapsed)
                self._dump_dbms_output()
        except cx_Oracle.DatabaseError,e:
            elapsed=time.time()-t0
            print str(e).strip()
            print '(%.3f sec)'%(elapsed)
        finally:
            signal.signal(signal.SIGTSTP, signal.SIG_DFL)
        self.cmd=''

    #-------------------------------------------------------------------
    def default0(self,s):
        """process a line of input"""
        if self.cmd=='':   # first line, assigns
            self.cmd=s
        else:
            self.cmd+='\n' # remaining lines, append
            self.cmd+=s
        if re.search('.*; *$',self.cmd):
            self.run()

    #-------------------------------------------------------------------
    def default(self,s):
        """preprocess a line of input"""
        ########################################## add to history here
        if re.search('^ *@',s):
            fn=s.split()[0] # get fn
            fn=fn[1:]        # chop @
            try:
                fd=open(fn)
                ll=[x.strip() for x in fd]
                fd.close()
            except IOError,e:
                print '%s: %s'%(fn, str(e))
                ll=['']
        else:
            ll=[s]
        for line in ll:
            self.default0(line)

    #-------------------------------------------------------------------
    def emptyline(self):
        """ignore empty lines"""
        pass

    #-------------------------------------------------------------------
    def complete(self, text, state):
        """cmd line completion.  couldn't get completedefault() to
           work, so just overwrite the entire completer.  by context,
           it tries to figure out when your typing sql, columns,
           and tables.
        """
        if state == 0:
            buf=readline.get_line_buffer()
            buf=buf[:readline.get_begidx()]
            fullcmd=self.cmd+buf
            #print '<%s>'%(fullcmd)
            if re.search(r'^\s*$',fullcmd,re.I|re.S):
                #cmds
                self.tmpcomp=[i for i in self.cmds if i.startswith(text)]
            elif re.search(r'^.*\s+from\s+$',fullcmd,re.I|re.S):
                #tables
                #add order by, where
                self.tmpcomp=[i for i in self.ltabs if i.startswith(text)]
            elif re.search(r'^\s*desc\s+$',fullcmd,re.I|re.S):
                #tables
                #add order by, where
                self.tmpcomp=[i for i in self.ltabs if i.startswith(text)]
            else:
                #columns
                #add from
                self.tmpcomp=[i for i in self.lcols if i.startswith(text)]
        if state < len(self.tmpcomp):
            rv=self.tmpcomp[state]
        else:
            rv=None
        return rv

    #-----------------------------------------------------------------------
    def oneshot(self,cmds):
        """execute a set of commands one time each"""
        for cmd in cmds:
            self.curs.execute(cmd)
            self.oraprint(self.curs.description,self.curs.fetchall())

    #-----------------------------------------------------------------------
    def do_jobs(self,s):
        """print all oracle jobs"""
        q="""select job,what,last_date,next_date from dba_jobs"""
        self.curs.execute(q)
        self.oraprint(self.curs.description,self.curs.fetchall())

    #-----------------------------------------------------------------------
    def do_nullstr(self,s):
        self.nullstr=s;
        print 'null string set to "%s"'%(self.nullstr)

    #-----------------------------------------------------------------------
    def do_du(self,s):
        """print disk usage"""
        q="""select owner,tablespace_name,sum(bytes)/(1024*1024) mbytes
               from dba_segments
                group by owner, tablespace_name
                order by 2, 3"""
        q="""select owner,tablespace_name,sum(bytes)/(1024*1024*1024) gbytes
               from dba_segments
                group by owner, tablespace_name
                order by 2, 3"""
        self.curs.execute(q)
        self.oraprint(self.curs.description,self.curs.fetchall())

    #-----------------------------------------------------------------------
    def do_sqlid(self,s):
        """print text for sql id"""

        try:
            inst,tid=s.split()
        except IndexError,e:
            print 'usage: sqlid instance_no sql_id'
            return
        q="""select sql_text
               from gv$sqltext_with_newlines
              where inst_id=:1 and sql_id=:2
               order by piece"""
        self.curs.execute(q,[inst,tid])
        print ''.join([a[0] for a in self.curs.fetchall()])
        print ''

    #-------------------------------------------------------------------
    def do_help(self,s):
        """print some help stuff"""
        print self.helptext

    #-------------------------------------------------------------------
    def do_refresh(self,s):
        """refresh cached stuff"""
        print self.ltabs

    #-------------------------------------------------------------------
    def do_tables(self,s):
        """print a list of the tables"""
        print self.ltabs

    #-------------------------------------------------------------------
    def do_blockers(self,s):
        """show any blockers (on a RAC)"""
        q="""
        SELECT /*+ ORDERED USE_NL(l,s) */
          l.inst_id,DECODE(l.request,0,'HOLD','Wait') stat,
          LPAD(p.spid,7) spid, l.sid, s.serial#,
          s.username||'('||s.osuser||')'||
          decode(substr(s.machine,1,25),NULL,decode(substr(s.terminal,1,7),
                                    NULL,'unknown',substr(s.terminal,1,7)),
             substr(s.machine,1,decode(instr(s.machine,'.'),0,16,
                                         instr(s.machine,'.') -1))) source,
          s.program,s.sql_id,
          decode(w.event,'SQL*Net message from client','SQL*Net msg client',
                                                             w.event) event,
          l.id1, l.id2, l.lmode||'>'||
          l.request l_r, l.type ty,SUBSTR(s.status,1,1)||ROUND(l.ctime/60) Act
        FROM gv$lock l, gv$session s, gv$process p, gv$session_wait w
        WHERE (l.id1, l.id2) IN (SELECT id1, id2 FROM gv$lock WHERE request>0)
            and l.sid = s.sid
            and s.sid=w.sid
            and s.paddr = p.addr
            and s.inst_id=p.inst_id
            and l.inst_id=p.inst_id
            and w.inst_id=l.inst_id
        ORDER BY l.id1, l.id2,l.request
        """
        self.curs.execute(q)
        self.oraprint(self.curs.description,self.curs.fetchall())

    #-------------------------------------------------------------------
    def do_info(self,s):
        """print some info about the connection"""
        cv='.'.join([str(x) for x in cx_Oracle.clientversion()])
        print 'client:'
        print '                 pid :',os.getpid()
        print '            hostname :',socket.gethostname()
        print '                user :',getpass.getuser()
        print 'cx_Oracle:'
        print '             version :',cx_Oracle.version
        print '       clientversion :',cv
        print '            apilevel :',cx_Oracle.apilevel
        print '           buildtime :',cx_Oracle.buildtime
        print 'connection:'
        print '             version :',self.conn.version
        print '            username :',self.conn.username
        print '            tnsentry :',self.conn.tnsentry
        print '                 dsn :',self.conn.dsn
        print '            encoding :',self.conn.encoding
        print '           nencoding :',self.conn.nencoding
        print 'maxBytesPerCharacter :',self.conn.maxBytesPerCharacter
        print '       stmtcachesize :',self.conn.stmtcachesize
        print '          autocommit :',self.conn.autocommit
        print '      current_schema :',self.conn.current_schema
        print 'cursor:'
        print '           arraysize :',self.curs.arraysize
        print '    numbersAsStrings :',self.curs.numbersAsStrings
        #print 'other:'
        #print '      clientinfo :',self.my_clientinfo
        #print '          module :',self.my_module
        #print 'client_identifier :',self.my_client_identifier

    #-------------------------------------------------------------------
    def do_desc(self,s):
        """describe an object"""
        # this version depends on all_* views.  should we fall back
        # to user_* if that's not available?
        s=s.strip(';')
        a=s.split('.')
        if len(a) == 2:
            schname=a[0].upper()
            objname=a[1].upper()
        else:
            schname=self.conn.username.upper()
            objname=a[0].upper()

        c=self.conn.cursor()
        c.execute("""
            select object_type
              from all_objects
             where owner=:1 and object_name=:2""",[schname,objname])
        r=c.fetchone()
        if r is None:
            print 'unknown object:',s
            return
        otype=r[0].lower()
        print otype
       
        if otype in ('table','view'):
            c.execute("""
                select column_name col,data_type type,data_length len,nullable
                  from all_tab_cols
                 where owner=:1 and table_name=:2
              order by column_id""",[schname,objname])
            x=c.fetchall()
            self.oraprint(c.description,x)
        elif otype in ('index'):
            self.do_ddl(s)
        elif otype in ('sequence'):
            self.do_ddl(s)
        elif otype in ('package'):
            print 'need to add desc support for type:',otype
        else:
            print 'need to add desc support for type:',otype

    #-------------------------------------------------------------------
    def do_fkeys(self,s):
        """show foreign key children of a table"""
        # thank you stack!!
        # http://dba.stackexchange.com/questions/96858
        # Note that it requires 11.2 due to the use of listagg()
        c=self.conn.cursor()
        s=s.strip(';')
        c.execute("""
            with fk_list as (
              select parent_table.table_name parent,
                     parent_cons.constraint_name as pk_constraint,
                     child_table.table_name child,
                     child_cons.constraint_name as fk_constraint
              from user_tables parent_table
                join user_constraints parent_cons
                  on parent_table.table_name = parent_cons.table_name
                 and parent_cons.constraint_type IN ('P', 'U')
                join user_constraints child_cons
                  on child_cons.r_constraint_name = parent_cons.constraint_name
                 and child_cons.constraint_type   = 'R'
                join user_tables child_table
                  on child_table.table_name = child_cons.table_name
                 and child_table.table_name <> parent_table.table_name
            )
            select level,
                   fl.child,
                   (select listagg(fk.column_name,',')
                       within group (order by fk.position)
                       from user_cons_columns fk
                       where fk.constraint_name = fl.fk_constraint)
                       as fk_columns,
                   fl.parent,
                   (select listagg(pk.column_name,',')
                       within group (order by pk.position)
                       from user_cons_columns pk
                       where pk.constraint_name = fl.pk_constraint)
                       as pk_columns
            from fk_list fl
            where fl.child <> fl.parent
            start with fl.parent = :1
            connect by prior fl.child = fl.parent
            order by level
        """,[s.upper()])
        x=c.fetchall()
        if len(x) == 0:
            print 'unknown object:',s
        else:
            self.oraprint(c.description,x)

    #-------------------------------------------------------------------
    def do_ddl(self,s):
        """show ddl for an object"""

        s=s.strip(';')
        if len(s.split()) != 1:
            print 'usage: ddl object-name'
            return

        c=self.conn.cursor()
        try:
           self.ddlInit
        except AttributeError:
           # only initialize the transform params once
           self.ddlInit=True
           p="dbms_metadata.set_transform_param(dbms_metadata.session_transform"
           c.execute("""
           begin
               ZZZ,'PRETTY',true);
               ZZZ,'SQLTERMINATOR',true);
               ZZZ,'SEGMENT_ATTRIBUTES',false);
               ZZZ,'STORAGE',false);
               ZZZ,'TABLESPACE',false);
           end;
           """.replace("ZZZ",p))

        c.execute("select object_type from user_objects where object_name=:1",
            [s.upper()])
        x=c.fetchall()
        if len(x) == 0:
            print 'unknown object:',s
            return
        objtype=x[0][0]
        try:
            c.execute("""select to_char(dbms_metadata.get_ddl(:1,:2))
                           from dual""", [objtype,s.upper()])
            code=''
            for rr in c:
                code += rr[0]+'\n'
            print code
        except cx_Oracle.DatabaseError,e:
            err,=e
            msg=err.message.strip()
            if err.code == 31603:
                msg=msg.split('\n')[0]
            print msg

    #-------------------------------------------------------------------
    def do_EOF(self,s):
        """goodbye -- surely there's a better way to catch eof??"""
        print ''
        sys.exit(0);

    #-------------------------------------------------------------------
    def do_ctls(self,s):
        """list context indices"""
        print 'TBD'

    #-------------------------------------------------------------------
    def do_ctexplain(self,s):
        """explain a ctx search"""
        x=shlex.split(s)
        if len(x) != 2:
            print 'usage: ctexplain index query'
            return
        (ix,query)=x
        ix=ix.upper()

        self.curs.execute("""select count(*)
                               from user_objects
                              where object_name='SQLMINUS_CTEXPLAIN'
                                    and object_type='TABLE'""")
        count=self.curs.fetchone()[0]
        if count == 0:
            self.curs.execute("""create table sqlminus_ctexplain(
                                     explain_id varchar2(30),
                                     id number,
                                     parent_id number,
                                     operation varchar2(30),
                                     options varchar2(30),
                                     object_name varchar2(64),
                                     position number,
                                     cardinality number)""");

        self.curs.execute("""begin ctx_query.explain(
                                index_name => :1,
                                text_query => :2,
                                explain_table => 'SQLMINUS_CTEXPLAIN',
                                sharelevel => 0,
                                explain_id => 'sqlminus1'); end;""",[ix,query])

        self.curs.execute("""select explain_id, id, parent_id, operation,
                                    options, object_name, position
                               from sqlminus_ctexplain
                               order by id""")
        self.oraprint(self.curs.description,self.curs.fetchall())

    #-------------------------------------------------------------------
    def do_exec(self,s):
        """execute a procedure"""
        self.cmd = 'begin %s; end;;'%(s.rstrip('; '))
        self.run()

    #-------------------------------------------------------------------
    def do_tron(self,s):
        """turn on dbms_output"""
        self.curs.execute("""begin dbms_output.enable; end;""")

    #-------------------------------------------------------------------
    def do_troff(self,s):
        """turn off dbms_output"""
        self.curs.execute("""begin dbms_output.disable; end;""")

    #-------------------------------------------------------------------
    def _dump_dbms_output(self):
        curs=self.conn.cursor()
        line=curs.var(cx_Oracle.STRING)
        status=curs.var(cx_Oracle.NUMBER)
        cmd="begin dbms_output.get_line(:l,:s); end;"
        while True:
            curs.execute(cmd,l=line,s=status)
            ll=line.getvalue()
            if ll is None:
                break
            else:
                print ll

    #-------------------------------------------------------------------
    def _call(self,rv,s):
        """guts for do_callX"""
        t0=time.time()
        try:
            self.curs.execute("begin :rv := %s end;" % (s), rv=rv)
            print rv.getvalue()
        except cx_Oracle.DatabaseError,e:
            print e
        elapsed=time.time()-t0
        self._dump_dbms_output()
        print '(%.3f sec)'%(elapsed)

    #-------------------------------------------------------------------
    def do_calln(self,s):
        """call a function returning a number"""
        # TODO: get precision?
        self._call(self.curs.var(cx_Oracle.NUMBER), s)

    #-------------------------------------------------------------------
    def do_calls(self,s):
        """call a function returning a varchar2"""
        self._call(self.curs.var(cx_Oracle.STRING), s)

    #-------------------------------------------------------------------
    def do_callc(self,s):
        """call a function returning a clob"""
        self._call(self.curs.var(cx_Oracle.CLOB), s)

    #-------------------------------------------------------------------
    def do_mono(self,s=None):
        """set monochrome output"""
        self.colors=['','','']

    #-------------------------------------------------------------------
    def do_color(self,s=None):
        """set color output"""
        self.colors=['\033[0m','\033[36m','\033[0m']

    #-------------------------------------------------------------------
    def do_rehash(self,s=None):
        """(re)populate the user's tables/columns"""
        self.xtabs=collections.defaultdict(list)
        self.xcols=collections.defaultdict(list)

        self.curs.execute("""select lower(table_name),lower(column_name)
                             from user_tab_cols""")
        for (tt,cc) in self.curs:
            self.xtabs[tt].append(cc)
            self.xcols[cc].append(tt)
        self.ltabs=[i for i in self.xtabs.keys()]; self.ltabs.sort()
        self.lcols=[i for i in self.xcols.keys()]; self.lcols.sort()
        #self.desc[tblname]=...

#-----------------------------------------------------------------------
def lookupAlias(s):
    """resolve an alias"""
    gg={}
    ll={}
    try:
        execfile(os.environ['HOME']+'/.sqlminus',gg,ll)
    except IOError:
        pass
    if ll.has_key(s):
        s=ll[s]
    return s

#-----------------------------------------------------------------------

def main():
    """the main thing"""

    print '--------------------------------------------------'
    print 'Welcome to sqlminus'
    print 'docs at: https://github.com/marhar/sqlminus'
    print '--------------------------------------------------'
    parser=argparse.ArgumentParser()
    #parser.add_argument('-f',"--file",help="input sql file")
    parser.add_argument('--sysdba',action='store_true',help="login as sysdba")
    args,items=parser.parse_known_args()

    if len(items) < 1:
        print >>sys.stderr, "usage: sqlminus connstr"
        sys.exit(1)

    connstr=lookupAlias(items[0])
    connstr2=re.sub('/.*@','@',connstr)

    print 'connecting to %s...'%(connstr2)
    try:
        cc=OracleCmd(connstr,args.sysdba)
    except cx_Oracle.DatabaseError,e:
        print e
        sys.exit(1)
    if os.isatty(sys.stdin.fileno()):
        cc.connstr2=connstr2
        cc.prompt=cc.connstr2+'> '
        cc.do_color()
    if len(items) >= 2:
        for aa in items[1:]:
            if aa.startswith('=') or aa.startswith('@'):
                # @foo or =foo means foo is a file with sql commands
                dat=open(aa[1:]).read()
                cc.default(dat)
            else:
                cc.default(aa)
    else:
        import readline, getpass, atexit
        #todo: prompt for passwd if needed
        historyFile = os.getenv("SQLMINUS_HISTORY",
                 os.getenv('HOME')+"/.sqlminus-history")

        if os.path.exists(historyFile):
            # gnu/libedit readline weirdness on macos. see
            # https://docs.python.org/2/library/readline.html
            if readline.__doc__.rfind('libedit') == -1:
                readline.read_history_file(historyFile)

        def writeHistory(historyFile=historyFile):
            import readline
            readline.write_history_file(historyFile)

        atexit.register(writeHistory)

        while True:
            try:
                cc.cmdloop()
                break
            except KeyboardInterrupt:
                cc.clearinput()
                print '^C',
                print '(input cleared)'

if __name__=='__main__':
    main()

