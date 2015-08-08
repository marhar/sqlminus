"""
sqlminus -- sqlplus minus. the features? the suck? you be the judge!

usage:
    sqlminus [--sysdba] connstr          - interactive shell
    sqlminus [--sysdba] connstr  cmds... - execute cmds
    sqlminus [--sysdba] connstr  @file   - execute cmds in file.sql
    sqlminus [--sysdba] connstr
    (note: @ and --file stuff in flux and subject to change)

configuration:
    ~/.sqlminus holds connstr aliases.  format:   foo = 'foo/bar@baz'

features:
    readline editing
    smart tab completion for tables, columns
    nice table formatting
    single file, easy to install

author:
    Mark Harrison, marhar@gmail.com
    https://github.com/marhar/sqlminus

license and download:
    bsd-ish.  see orapig package for complete text.
"""

import sys,os,re,time,cmd,collections,readline,signal,argparse,socket
import traceback,getpass,shlex,subprocess,cx_Oracle

#-----------------------------------------------------------------------
def P(s):
    """print and flush, with newline"""
    P0(str(s)+'\n')

#-----------------------------------------------------------------------
def P0(s):
    """print and flush, no newline"""
    sys.stdout.write(str(s))
    sys.stdout.flush()

#-----------------------------------------------------------------------
dbgfd=None
def D0(s):
    """debug output, no newline"""
    global dbgfd
    if dbgfd is None:
        dbgfd=open('/tmp/sqlminus.dbg','a')
        D('================================================== DBGFD')
    dbgfd.write(str(s))
    dbgfd.flush()

#-----------------------------------------------------------------------
def D(s):
    """debug output with newline."""
    D0(str(s)+'\n')

#-----------------------------------------------------------------------
print_is_quiet = False
def V0(s):
    """verbose print and flush, no newline. --quiet to supress"""
    if print_is_quiet is False:
        sys.stdout.write(str(s))
        sys.stdout.flush()

#-----------------------------------------------------------------------
def V(s):
    """verbose print and flush, with newline. --quiet to supress"""
    V0(str(s)+'\n')

#-----------------------------------------------------------------------
def termRowsCols():
    """how many rows, cols on our screen?"""
    rows,cols=os.popen('stty size', 'r').read().split()
    return [int(rows),int(cols)]

#-----------------------------------------------------------------------
def termCols():
    """how many columns on our screen?"""
    return termRowsCols()[1]

#-----------------------------------------------------------------------
def termRows():
    """how many rows on our screen?"""
    return termRowsCols()[0]

#-------------------------------------------------------------------
experimental_resize=False
def resize_terminal(xlen,force=False):
    """EXPERIMENTAL set the terminal width"""
    if experimental_resize:
        if force or xlen > termCols():
            P0('\033[8;25;%dt'%(xlen))

def resize_font(sz):
    """EXPERIMENTAL MAC-ONLY resize the font of our window"""
    weird_applescript="""
        tell application "System Events" to tell application "Finder"
            tell process "Terminal"
                set frontmost to true
            end tell
        end tell

        tell application "Terminal"
            set font size of first window to "%d"
        end tell
    """
    fd=os.popen('osascript','w')
    fd.write(weird_applescript%(sz))

class OracleCmd(cmd.Cmd):
    #-------------------------------------------------------------------
    def __init__(self,connstr,sysdba):
        """OracleCmd init"""
        cmd.Cmd.__init__(self)
        if sysdba is True:
            self.conn = cx_Oracle.connect(connstr,mode=cx_Oracle.SYSDBA)
            P('----------------------------------------------------------')
            P('| DUMBASS ALERT: logged in as sysdba, dont be a DUMBASS! |')
            P('----------------------------------------------------------')
        else:
            self.conn = cx_Oracle.connect(connstr)
        self.conn.client_identifier='sqlminus'
        self.conn.clientinfo='hello'
        self.conn.module='hello2'
        self.curs = self.conn.cursor()
        self.nullstr = '-';
        self.cmds=[]
        self.cmd=''
        self.do_mono()
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    #-------------------------------------------------------------------
    def clearinput(self):
        """clear the input state"""
        self.cmd=''

    #-------------------------------------------------------------------
    def do_resize(self,s):
        """screen: turn resize on or off EXPERIMENTAL"""
        s=s.strip(';')
        global experimental_resize
        if s == 'on':
            experimental_resize=True
            P('resize on')
        else:
            experimental_resize=False
            P('resize off')

    #-------------------------------------------------------------------
    def do_sane(self,s):
        """screen: set the terminal width to a sane value EXPERIMENTAL"""
        s=s.strip(';')
        if s is None or s == '':
            s="80"
        resize_terminal(int(s),force=True)

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
        resize_terminal(len(line))
        P(line)
        P(re.sub('[^ ]','-',line))

        # rows
        x=0
        for r in rows:
            r2=[self.nullstr if i is None else i for i in r]
            line=fmt1%tuple(r2)
            P('%s%s'%(self.colors[x],line))
        P(self.colors[2])

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
                    P('(%d rows, %.3f sec)'%(self.curs.rowcount, elapsed))
                else:
                    P('(%.3f sec)'%(elapsed))
                self._dump_dbms_output()
        except cx_Oracle.DatabaseError,e:
            elapsed=time.time()-t0
            P(str(e).strip())
            P('(%.3f sec)'%(elapsed))
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
                P('%s: %s'%(fn, str(e)))
                ll=['']
        else:
            ll=[s]
        for line in ll:
            self.default0(line)

    #-----------------------------------------------------------------------
    def do_x(self,s):
        """INTERNAL: for internal testing"""
        pass
        examples="""
        self.cmd='select 2+2 four from dual;'
        self.run()
        """
        D('X s=<%s>'%(s))
        D(self.lcols(s))
        D(self.lcols(s))
        resize_font(5)
        time.sleep(2)
        resize_font(25)
        time.sleep(2)
        resize_font(12)

    #-------------------------------------------------------------------
    ltabCache={}
    ltabCacheTm={}
    def ltabs(self,prefix0=None):
        """tmp test of local tables"""
        #---------------------------------------------------------------
        # - also need to handle views?
        # - also needs to aliases?
        #---------------------------------------------------------------

        CACHE_TIMEOUT = 30

        if prefix0 is None:
            prefix0=''

        if self.ltabCacheTm.has_key(prefix0):
            dt=time.time()-self.ltabCacheTm[prefix0]
            if dt < CACHE_TIMEOUT:
                return self.ltabCache[prefix0]

        pa=prefix0.split('.')
        if len(pa) == 1:
            user=self.conn.username.upper()
            prefix=pa[0]
        else:
            user=pa[0].upper()
            prefix=pa[1]

        mcurs=self.conn.cursor()

        if prefix == '':
            mcurs.execute("""select unique table_name
                               from all_tab_cols
                              where owner = :1
                             order by table_name""",[user])
        else:
            prefix=prefix.upper()+'%'
            mcurs.execute("""select unique table_name
                               from all_tab_cols
                              where owner = :1
                                and upper(table_name) like :2
                             order by table_name""", [user,prefix])

        rr=mcurs.fetchall()
        rv=[x[0] for x in rr]
        self.ltabCache[prefix0]=rv
        self.ltabCacheTm[prefix0]=time.time()
        return rv

    #-------------------------------------------------------------------
    lcolCache={}
    lcolCacheTm={}
    def lcols(self,prefix=None):
        """"column names"""

        CACHE_TIMEOUT = 30

        # TODO: lcolCache not yet working
        if self.lcolCacheTm.has_key(prefix):
            dt=time.time()-self.lcolCacheTm[prefix]
            if dt < CACHE_TIMEOUT:
                D('cached '+str(dt))
                return self.lcolCache[prefix]

        user=self.conn.username
        user=user.upper()

        prefix=prefix.upper()+'%'

        mcurs=self.conn.cursor()
        # TODO: can these executes be made into one?
        if prefix is None or prefix == '':
            mcurs.execute("""select unique column_name
                               from all_tab_cols
                              where owner = :1
                             order by column_name""",[user])
        else:
            mcurs.execute("""select unique column_name
                               from all_tab_cols
                              where owner = :1
                                and column_name like :2
                             order by column_name""",[user,prefix])
        rr=mcurs.fetchall()
        rv=[x[0] for x in rr]
        self.lcolCache[prefix]=rv
        self.lcolCacheTm[prefix]=time.time()
        return rv

    #-------------------------------------------------------------------
    def emptyline(self):
        """ignore empty lines"""
        pass

    #-------------------------------------------------------------------
    def complete(self, text, state):
        """cmd line completion.  overrides default completer
           entirely so we can handle tables and columns by context.
        """
        if state == 0:
            buf=readline.get_line_buffer()
            buf=buf[:readline.get_begidx()]
            fullcmd=self.cmd+buf
            if re.search(r'^\s*$',fullcmd,re.I|re.S):
                # "word" no spaces
                # cmds
                self.tmpcomp=[i for i in self.cmds if i.startswith(text)]
            elif re.search(r'^.*\s+from\s+$',fullcmd,re.I|re.S):
                # word, spaces "from" spaces
                # tables
                self.tmpcomp=[i for i in self.ltabs(text)]
            elif re.search(r'^\s*desc\s+$',fullcmd,re.I|re.S):
                # word "desc" spaces
                # tables
                self.tmpcomp=[i for i in self.ltabs(text)]
            else:
                # anything else
                # columns
                self.tmpcomp=[i for i in self.lcols(text)]
        # added the if True, which is incorrect but eliminates a tabpress
        if True or state < len(self.tmpcomp):
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
    def do_nullstr(self,s):
        """query: set the null string"""
        self.nullstr=s;
        P('null string set to "%s"'%(self.nullstr))

    #-----------------------------------------------------------------------
    def do_du(self,s):
        """admin: print disk usage"""
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
        """devel: print text for sql id"""

        #TODO: fix split returns != 2 len
        try:
            inst,tid=s.split()
        except IndexError,e:
            P('usage: sqlid instance_no sql_id')
            return
        q="""select sql_text
               from gv$sqltext_with_newlines
              where inst_id=:1 and sql_id=:2
               order by piece"""
        self.curs.execute(q,[inst,tid])
        P(''.join([a[0] for a in self.curs.fetchall()]))
        P('')

    #-------------------------------------------------------------------
    def do_help(self,s):
        """sqlminus: print some help stuff"""

        import types,collections
        funclist=[x[3:] for x,y in OracleCmd.__dict__.items()
                  if type(y) == types.FunctionType
                   and x.startswith('do_')]
        mxlen=max([len(f) for f in funclist])
        
        helptext={}
        categories=collections.defaultdict(list)

        for f in funclist:
            hh=OracleCmd.__dict__['do_'+f].__doc__.split(':')
            categories[hh[0]].append(f)
            helptext[f]=hh[1].strip()
            
        del(categories['INTERNAL'])
        P(__doc__)
        P('commands:')
        for k in sorted(categories.keys()):
            P('  %s'%(k))
            for f in sorted(categories[k]):
                P('    %*s : %s'%(mxlen,f,helptext[f]))

    #-------------------------------------------------------------------
    def do_tables(self,s):
        """query: print a list of the tables"""
        t=self.ltabs()
        n=len(t)
        mx=0
        for i in t:
            if len(i) > mx:
                mx=len(i)
        ncols=max(1,termCols()/(mx+1))
        nrows=n/ncols
        rem=n-(nrows*ncols)
        fmt='%%-%ds'%(mx)
        for r in range(nrows):
            for c in range(ncols):
                P0(fmt%(t[r*ncols+c]))
                if c != ncols:
                    P0(' ')
            P('')
        r+=1
        for c in range(rem):
            P0(fmt%(t[r*ncols+c]))
        P('')

    #-------------------------------------------------------------------
    def do_blockers(self,s):
        """admin: show any blockers (on a RAC)"""
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
        """sqlminus: print some info about the connection"""
        cv='.'.join([str(x) for x in cx_Oracle.clientversion()])
        P('client:')
        P('                 pid : %s'%(os.getpid()))
        P('            hostname : %s'%(socket.gethostname()))
        P('                user : %s'%(getpass.getuser()))
        P('cx_Oracle:')
        P('             version : %s'%(cx_Oracle.version))
        P('       clientversion : %s'%(cv))
        P('            apilevel : %s'%(cx_Oracle.apilevel))
        P('           buildtime : %s'%(cx_Oracle.buildtime))
        P('connection:')
        P('             version : %s'%(self.conn.version))
        P('            username : %s'%(self.conn.username))
        P('            tnsentry : %s'%(self.conn.tnsentry))
        P('                 dsn : %s'%(self.conn.dsn))
        P('            encoding : %s'%(self.conn.encoding))
        P('           nencoding : %s'%(self.conn.nencoding))
        P('maxBytesPerCharacter : %s'%(self.conn.maxBytesPerCharacter))
        P('       stmtcachesize : %s'%(self.conn.stmtcachesize))
        P('          autocommit : %s'%(self.conn.autocommit))
        P('      current_schema : %s'%(self.conn.current_schema))
        P('cursor:')
        P('           arraysize : %s'%(self.curs.arraysize))
        P('    numbersAsStrings : %s'%(self.curs.numbersAsStrings))
        #P('other:')
        #P('      clientinfo : %s'%(self.my_clientinfo))
        #P('          module : %s'%(self.my_module))
        #P('client_identifier : %s'%(self.my_client_identifier))

    #-------------------------------------------------------------------
    def do_desc(self,s):
        """devel: describe an object"""
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
            P('unknown object:'+str(s))
            return
        otype=r[0].lower()
        P(otype)
       
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
            P('need to add desc support for type: '+otype)
        else:
            P('need to add desc support for type: '+otype)

    #-------------------------------------------------------------------
    def do_fkeys(self,s):
        """devel: show foreign key children of a table"""
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
            P('unknown object: '+s)
        else:
            self.oraprint(c.description,x)

    #-------------------------------------------------------------------
    def do_ddl(self,s):
        """devel: show ddl for an object"""

        s=s.strip(';')
        if len(s.split()) != 1:
            P('usage: ddl object-name')
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
            P('unknown object: '+s)
            return
        objtype=x[0][0]
        try:
            c.execute("""select to_char(dbms_metadata.get_ddl(:1,:2))
                           from dual""", [objtype,s.upper()])
            code=''
            for rr in c:
                code += rr[0]+'\n'
            P(code)
        except cx_Oracle.DatabaseError,e:
            err,=e
            msg=err.message.strip()
            if err.code == 31603:
                msg=msg.split('\n')[0]
            P(msg)

    #-------------------------------------------------------------------
    def do_EOF(self,s):
        """INTERNAL: surely there's a better way to catch eof??"""
        P('')
        sys.exit(0);

    #-------------------------------------------------------------------
    def do_ctls(self,s):
        """devel: list context indices"""
        P('    NOT IMPLEMENTED YET...')

    #-------------------------------------------------------------------
    def do_ctexplain(self,s):
        """devel: explain a ctx search"""
        x=shlex.split(s)
        if len(x) != 2:
            P('usage: ctexplain index query')
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
    def do_jobs(self,s):
        """devel: list jobs for this user"""
        self.curs.execute("""
            select job_name job,job_type type,
                state,enabled,failure_count fails,
                substr(trunc(next_run_date,'MI'),1,15) as last,
                nvl(instance_id, 0) as inst,
                repeat_interval,
                case when length(job_action) < 300 or job_action is null
                    then job_action
                    else '*** Too long to display here ***' end as text
            from dba_scheduler_jobs
            where owner=sys_context('USERENV','CURRENT_SCHEMA')
            order by job_name
        """)
        self.oraprint(self.curs.description,self.curs.fetchall())

    #-------------------------------------------------------------------
    def do_jobhist(self,s):
        """devel: list history for the job"""
        s=s.strip(';')
        av=s.split()
        if len(av) != 1:
            P('usage: jobhist jobname')
            return

        self.curs.execute("""
            select log_date,status,error#,instance_id
              from dba_SCHEDULER_JOB_run_details
             where job_name = upper(:1)
          order by log_date""",[av[0]])
        self.oraprint(self.curs.description,self.curs.fetchall())

    #-------------------------------------------------------------------
    def do_exec(self,s):
        """query: execute a procedure"""
        self.cmd = 'begin %s; end;;'%(s.rstrip('; '))
        self.run()

    #-------------------------------------------------------------------
    def do_tron(self,s):
        """devel: turn on dbms_output"""
        self.curs.execute("""begin dbms_output.enable; end;""")
        P('dbms_output enabled')

    #-------------------------------------------------------------------
    def do_troff(self,s):
        """devel: turn off dbms_output"""
        self.curs.execute("""begin dbms_output.disable; end;""")
        P('dbms_output disabled')

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
                P(ll)

    #-------------------------------------------------------------------
    def _call(self,rv,s):
        """guts for do_callX"""
        t0=time.time()
        try:
            self.curs.execute("begin :rv := %s end;" % (s), rv=rv)
            P(rv.getvalue())
        except cx_Oracle.DatabaseError,e:
            P(str(e))
        elapsed=time.time()-t0
        self._dump_dbms_output()
        P('(%.3f sec)'%(elapsed))

    #-------------------------------------------------------------------
    def do_calln(self,s):
        """query: call a function returning a number"""
        # TODO: get precision?
        self._call(self.curs.var(cx_Oracle.NUMBER), s)

    #-------------------------------------------------------------------
    def do_callv(self,s):
        """query: call a function returning a varchar2"""
        self._call(self.curs.var(cx_Oracle.STRING), s)

    #-------------------------------------------------------------------
    def do_callc(self,s):
        """query: call a function returning a clob"""
        self._call(self.curs.var(cx_Oracle.CLOB), s)

    #-------------------------------------------------------------------
    def do_mono(self,s=None):
        """screen: set monochrome output"""
        self.colors=['','','']

    #-------------------------------------------------------------------
    def do_color(self,s=None):
        """screen: set color output"""
        self.colors=['\033[0m','\033[36m','\033[0m']

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
def fixpassword(connstr):
    """if this connect string doesn't have a passwd, add one to it"""
    # if there's no '/', we need to get a password
    if connstr.find('/') == -1:
        import getpass
        passwd=getpass.getpass('password: ')
        ix=connstr.find('@')
        if ix == -1:
            connstr=connstr+'/'+passwd
        else:
            connstr=connstr[:ix]+'/'+passwd+connstr[ix:]
    return connstr

#-----------------------------------------------------------------------
def main():
    """The MAIN thing that you have to remember on this journey is,
       just be nice to everyone and always smile.
         -- Ed Sheeran
    """
    P('--------------------------------------------------')
    P('| Welcome to sqlminus v2.3                       |')
    P('| docs at: https://github.com/marhar/sqlminus    |')
    P('| type "help" for help                           |')
    P('--------------------------------------------------')
    parser=argparse.ArgumentParser()
    #parser.add_argument('-f',"--file",help="input sql file")
    parser.add_argument('--sysdba',action='store_true',help="login as sysdba")
    parser.add_argument('--quiet','-q',action='store_true',help="quiet output")
    args,items=parser.parse_known_args()
    global print_is_quiet; print_is_quiet = args.quiet

    if len(items) < 1:
        P('usage: sqlminus connstr')
        sys.exit(1)

    connstr=lookupAlias(items[0])
    connstr2=re.sub('/.*@','@',connstr)

    # does the user need to type a password?  maybe or maybe not,
    # since there might be an oracle wallet.  So, instead of trying
    # to intelligently figure things out, we try connecting and if
    # we get an ORA-1017 or ORA-1262 (both of which could indicate
    # a bad password we'll prompt for the password and try again.

    P('connecting to %s...'%(connstr2))
    try:
        cc=OracleCmd(connstr,args.sysdba)
    except cx_Oracle.DatabaseError,e:
        err,=e
        if err.code in (1017,12162):
            connstr=fixpassword(connstr)
            connstr2=re.sub('/.*@','@',connstr)
            try:
                cc=OracleCmd(connstr,args.sysdba)
            except cx_Oracle.DatabaseError,e:
                P(str(e))
                sys.exit(1)
        else:
                P(str(e))
                sys.exit(1)

    if os.isatty(sys.stdin.fileno()):
        cc.connstr2=connstr2
        cc.prompt=cc.connstr2+'> '
        cc.do_color()
    if len(items) >= 2:
        for aa in items[1:]:
            if aa.startswith('=') or aa.startswith('@'):
                # @foo or =foo means foo is a file with sql commands
                # @foo is compatible with sqlplus, but
                # =foo allows completion
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
                P('^C (input cleared)')
            except cx_Oracle.DatabaseError,e:
                P('')
                P('*************************************************')
                P('')
                P('Unexpected Database Error:')
                P('')
                traceback.print_exc()
                P('please file a bug report here:')
                P('    https://github.com/marhar/sqlminus/issues/new')
                P('')
                P('*************************************************')

            except Exception,e:
                P('')
                P('*************************************************')
                P('')
                P('Unexpected Error:')
                P('')
                traceback.print_exc()
                P('')
                P('please file a bug report here:')
                P('    https://github.com/marhar/sqlminus/issues/new')
                P('')
                P('*************************************************')

if __name__=='__main__':
    main()

