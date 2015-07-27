#!/usr/bin/python
"""
#-----------------------------------------------------------------------
orapig -- oracle python interface generator
http://code.google.com/p/orapig/
#-----------------------------------------------------------------------
"""

import sys
import cx_Oracle
import optparse
import re
import getpass

# these are the template fragments necessary
tmplEnums=(
    file0,	# beginning of file
    file1,	# end of file
    class0,	# class
    func0,	# function
    func1,	# function returning unsupported datatype
    proc0,	# procedure
    procv0	# procedure, vectorizing form
    ) = range(1,8)

#-----------------------------------------------------------------------
#  Trans -- translator base class
#-----------------------------------------------------------------------

class Trans:
    templates={}
    def __init__(self,conn,output):
        self.output=output
        self.conn=conn
        self.curs=self.conn.cursor()

    def println (self,line):
        """print a line to the selected output"""
        self.output.write(line+'\n')

    def err (self,line):
        """print a line to stderr"""
        sys.stderr.write(line+'\n')

    def getprocedures(self,owner,package_name):
        """get a list of all public procedures and functions in a package"""
        self.curs.execute("""
            select ap.procedure_name
                from all_procedures ap, all_objects ao
                where ap.object_name = ao.object_name
                  and ao.object_type='PACKAGE'
                  and ap.object_name=:package_name
                  and ap.procedure_name is not NULL
                  and ap.owner = :owner
                  and ao.owner = :owner
                  order by ap.procedure_name
                """,package_name=package_name,owner=owner)
        rv=[i[0] for i in self.curs]
        return rv

    def isfunc(self,owner,objname,package_name):
        """is this object a function?"""
        self.curs.execute("""
            select count(data_type)
              from all_arguments
              where object_name=:objname
              and owner=:owner
              and data_type is not null
              and package_name=:package_name
              and position=0
              and argument_name is null""",
            objname=objname,package_name=package_name,owner=owner)
        return_types=self.curs.fetchone()[0]
        return return_types

    def getparms(self,owner,objname,package_name):
        """get the parameter list for a procedure"""
        rv=[]
        self.curs.execute("""
            select argument_name
              from all_arguments
              where object_name=:objname
                and owner=:owner
                and argument_name is not null
                and package_name=:package_name
              order by position""",objname=objname,package_name=package_name,owner=owner)
        rv=[i[0].lower() for i in self.curs]
        return rv

    def getarrayparms(self,owner,objname,package_name):
        """get the list of parameters of array type"""
        rv={}
        self.curs.execute("""select argument_name, data_type from all_arguments
                             where package_name=:package_name
                             and owner=:owner
                             and object_name=:objname
                             order by sequence""",objname=objname,package_name=package_name,owner=owner)

        current_arg = ""
        pick_next = False
        for row in self.curs:
            if row[1] == "PL/SQL TABLE":
                current_arg = row[0]
                pick_next = True
            if row[0] is None and pick_next:
                rv[current_arg.lower()]=row[1]
                pick_next = False
        return rv

    def getarrayindices(self,owner,objname,package_name):
        """get the list of parameters of array type"""
        rv={}
        self.curs.execute("""select argument_name, data_type, position from all_arguments
                             where package_name=:package_name
                             and owner=:owner
                             and object_name=:objname
                             order by sequence""",objname=objname,package_name=package_name,owner=owner)

        position = 0
        pick_next = False
        for row in self.curs:
            if row[1] == "PL/SQL TABLE":
                position = row[2]
                pick_next = True
            if row[0] is None and pick_next:
                rv[position]=row[1]
                pick_next = False
        return rv

    def hasoutputparms(self,owner,objname,package_name):
        """Tell if a procedure has array out or in out parameters"""
        result = False
        self.curs.execute("""
            select count(argument_name)
            from all_arguments
            where object_name=:objname
               and owner=:owner
               and data_type='PL/SQL TABLE'
               and (in_out='OUT' or in_out='IN/OUT')
               and package_name=:package_name""",objname=objname.upper(),package_name=package_name,owner=owner)
        for row in self.curs:
            if row[0] > 0:
                return True
        return False

    def docbeautify(self,s,lev):
        """beautifully indent a block of text for a doc string"""
        spaces='    '*lev
        s='\n'.join([(spaces + x).rstrip() for x in s.splitlines()])
        return s

    def getdoc(self,synonym, owner, pkgname):
        """build up a doc string for this class and its members"""
        self.memberdocs={}
        decl=re.compile(r'^[\s]+(function|procedure)[\s\+]([^\s(;]+)')
        asline=re.compile(r'^[\s]*(AS|IS)[\s]*$',re.IGNORECASE)
        blab=re.compile(r'^[\s]*[-][-][+][\s](.*)')
        t=''
        t+='class %s -- interface for package %s%s.%s\n'%\
             ((synonym or pkgname).capitalize(),
              synonym and "(synonym) " or "",
              self.conn.username.upper(),synonym or pkgname)
        t+='\n'
        t+='*** This is a generated class. DO NOT MODIFY! ***\n'
        #t+=' '.join(sys.argv)
        #t+='\n'
        t+='\n'
        self.curs.execute("""select text from all_source where name=:name
                             and type='PACKAGE' and owner=:owner order by line""", name=pkgname,owner=owner)

        # first, get the package docs
        for r in self.curs:
            s=r[0]
            m=blab.match(s)
            if m:
                t+=m.group(1)
                t+='\n'
                continue
            m=asline.match(s)
            if m:
                t+='\n'
                break

        # now, get the procedure docs
        blabbage=''
        for r in self.curs:
            s=r[0]
            m=blab.match(s)
            if m:
                blabbage+=m.group(1)
                blabbage+='\n'
                continue
            m=decl.match(s)
            if m:
                decltype=m.group(1)
                declname=m.group(2)
                self.memberdocs[declname]=self.docbeautify(blabbage,2)
                blabbage=''
                continue
        t=self.docbeautify(t,1)
        return t

    def getfunctype(self,owner,objname):
        """get the return type of a function"""
        self.curs.execute("""
            select data_type
              from all_arguments
              where object_name=:objname
                and owner=:owner
                and argument_name is null""",objname=objname,owner=owner)
        dt=self.curs.fetchone()[0]
        return dt

    def getparmtype(self,owner,pkgname,procname,parmname):
        """get a parameter type"""
        parmname=parmname.upper()
        self.curs.execute("""
            select data_type
              from all_arguments
              where package_name=:pkgname and object_name=:procname
                and owner=:owner
                and argument_name=:parmname""",
                pkgname=pkgname,procname=procname,parmname=parmname,owner=owner)

        r=self.curs.fetchone()
        dt=r[0]
        return dt

    def dump(self,pkglist):
        """dump what we know, mainly for debugging"""
        for pkg in pkglist:
           pkg=pkg.upper()
           self.err('package: %s'%(pkg))
           if self.pkgexists(pkg):
               for proc in self.getprocedures(pkg):
                   if self.isfunc(proc,pkg):
                       typ=self.getfunctype(proc)
                       self.err('    func: %s'%(proc))
                       self.err('        type: %s'%(typ))
                   else:
                       self.err('    proc: %s'%(proc))
                   for parm in self.getparms(proc,pkg):
                       typ=self.getparmtype(pkg,proc,parm)
                       self.err('        parm: %s %s'%(parm, typ))
           else:
               self.err('    DOES NOT EXIST IN SCHEMA')

#-----------------------------------------------------------------------
# Python code templates
#-----------------------------------------------------------------------

pytmpl={}
pytmpl[class0]="""\
class %s:
    \"\"\"
%s    \"\"\"

    #------------------------------------------------------
    def __init__(self,curs):
        self.curs=curs
        # do not set autocommit if your are not
        # writing an appserver!
        self.autocommit=False
"""
pytmpl[proc0]="""\
    #------------------------------------------------------
    def %s(self%s):
        \"\"\"
%s
        \"\"\"
%s
        result = self.curs.callproc('%s.%s'%s)
        if self.autocommit:
            conn.commit()
        return result
"""
pytmpl[procv0]="""\
    #------------------------------------------------------
    def %s(self,parmlist):
        \"\"\"
%s
        \"\"\"
%s        arguments = []
        for i in range(len(parmlist)):
            dict = {}
%s
            arguments.append(dict)
        result = self.curs.executemany("begin %s.%s(%s); end;", arguments)
        if self.autocommit:
            conn.commit()
        return result
"""
pytmpl[func0]="""\
    #------------------------------------------------------
    def %s(self%s):
        \"\"\"
%s
        \"\"\"
%s
        rv=self.curs.callfunc('%s.%s',%s%s)
        if self.autocommit:
            conn.commit()
        return rv
"""
pytmpl[func1]="""\
    #------------------------------------------------------
    def %s(self%s):
        \"\"\"
%s
        \"\"\"
%s
        raise TypeError("Unsupported Oracle Data Type: %s") 
"""
pytmpl[file0] = """\
import cx_Oracle
"""
pytmpl[file1] = ""

#-----------------------------------------------------------------------
# PyTrans
#-----------------------------------------------------------------------

class PyTrans(Trans):
    """translate a package to python"""

    # this maps datatypes, pl/sq -> python
    typemap={
        'RAW'			:'BINARY',
        'BFILE'			:'BFILE',
        'BLOB'			:'BLOB',
        'CLOB'			:'CLOB',
        'REF CURSOR'		:'CURSOR',
        'DATE'			:'DATETIME',
        'CHAR'			:'FIXED_CHAR',
        'unhandled_LONG_BINARY'	:'LONG_BINARY',
        'unhandled_LONG_STRING'	:'LONG_STRING',
        'unhandled_NCLOB'	:'NCLOB',
        'NUMBER'		:'NUMBER',
        'FLOAT'			:'NUMBER',
        'unhandled_OBJECT'	:'OBJECT',
        'VARCHAR2'		:'STRING',
        'TIMESTAMP'		:'TIMESTAMP',
        'ROWID'			:'ROWID',
        'CURSOR'		:'CURSOR'
    }

    def __init__(self,conn,output):
        Trans.__init__(self,conn,output)

    def getpyfunctype(self,owner,objname):
        """get the python (cx_Oracle) data type of a parm or rc"""
        dt=self.getfunctype(owner,objname)
        if self.typemap.has_key(dt):
            return (dt, 'cx_Oracle.'+self.typemap[dt])
        else:
            return (dt,None)

    def dofile(self,package_names):
        """process a file"""
        self.println(pytmpl[file0])
        for p in package_names:
            self.doclass(p.upper())
        self.println(pytmpl[file1])

    def doproc1(self,owner,procname,package_name):
        """process one procedure, normal version"""
        lprocname=procname.lower()
        parms=self.getparms(owner,procname, package_name)
        arraytype=self.getarrayparms(owner,procname,package_name)
        if self.memberdocs.has_key(lprocname):
            comment=self.memberdocs[lprocname]
        else:
            comment= "        (No doc string for this procedure)\n"
            comment+="        (orapig --helpfmt for more info )"
        if len(parms)==0:
            plist1=''
            plist2=''
        else:
            plist1=','+','.join(parms)
            plist2=',['+','.join(parms)+']'
        alist=""
        if len(arraytype) > 0:
            for parm in arraytype.keys():
                alist+="        %s=self.curs.arrayvar(cx_Oracle.%s, %s)\n" % \
                        (parm,self.typemap[arraytype[parm]],parm)
        decl=\
          pytmpl[proc0]%(lprocname,plist1,comment,alist,package_name,procname,plist2)
        self.println(decl)

    def doprocv(self,owner,procname,package_name):
        """process one procedure, vectorized version"""
        #TODO: should we not generate this if there's an out parm?
        #TODO: or have it generate a warning?
        lprocname=procname.lower()
        parms=self.getparms(owner,procname, package_name)
        arrayindices=self.getarrayindices(owner,procname,package_name)
        raise_exception = ""
        if self.hasoutputparms(owner,procname,package_name):
            raise_exception ="        # We don't support out or in/out parameters\n"
            raise_exception+="        raise NotImplementedError('Out array parameters not supported')\n"
        if self.memberdocs.has_key(lprocname):
            comment=self.memberdocs[lprocname]
        else:
            comment= "        (No doc string for this procedure)\n"
            comment+="        (orapig --helpfmt for more info )"
        comment+='\n        (this is the autogenerated vectorized _V procedure)'
        comment+='\n        (dont use it if you have out parms)'
        nparms=len(parms)
        plist2=""
        for i in range(0,nparms):
            plist2+=', :%d'%(i+1)
        plist2=plist2[2:]
        param_loop = ""
        for i in range(1,len(parms)+1):
            if i in arrayindices.keys():
                param_loop+="            dict['%d']=self.curs.arrayvar(cx_Oracle.%s, parmlist[i][%d])\n" % \
                             (i,self.typemap[arrayindices[i]],i-1)
            else:
                param_loop+="            dict['%d']=parmlist[i][%d]\n" % (i, i-1)
        decl=pytmpl[procv0]%(lprocname+"_V",comment,raise_exception,param_loop,package_name,procname,plist2)
        self.println(decl)

    def doprocs(self,owner,package_name):
        """process all procs"""
        procs=self.getprocedures(owner,package_name)
        for p in procs:
            if self.isfunc(owner,p,package_name):
                self.dofunc1(owner,p,package_name)
            else:
                self.doproc1(owner,p,package_name)
                self.doprocv(owner,p,package_name)

    def dofunc1(self,owner,funcname, package_name):
        """process one func"""
        lfuncname=funcname.lower()
        oraretype,retype=self.getpyfunctype(owner,funcname)
        parms=self.getparms(owner,funcname,package_name)
        arraytype=self.getarrayparms(owner,funcname,package_name)
        if self.memberdocs.has_key(lfuncname):
            comment=self.memberdocs[lfuncname]
        else:
            comment= "        (No doc string for this function)\n"
            comment+="        (orapig --helpfmt for more info)"
        if len(parms)==0:
            plist1=''
            plist2=''
        else:
            plist1=','+','.join(parms)
            plist2=',['+','.join(parms)+']'
        alist=""
        if len(arraytype) > 0:
            for parm in parms:
                alist+="        %s=self.curs.arrayvar(cx_Oracle.%s, %s)" % \
                        (parm,self.typemap[arraytype[parm]],parm)
        if retype:
            decl=pytmpl[func0]%(lfuncname,plist1,comment,alist,
                            package_name,funcname,retype,plist2)
        else:
            decl=pytmpl[func1]%(lfuncname,plist1,comment,alist,oraretype)
            
        self.println(decl)

    def doclass(self,package_name):
        """process one class"""
        curs = self.conn.cursor()
        synonym = package_name
        _, _, owner, realname, part2, dblink, part1_type, object_number = \
             curs.callproc("DBMS_UTILITY.NAME_RESOLVE", (package_name, 1, " "*30, " "*30, " "*30, " "*30, 0, 0))
        if synonym == realname and self.conn.username.upper() == owner:
            synonym = None
        classname = (synonym or package_name).capitalize()
        assert part2 is None
        doctext=self.getdoc(synonym, owner, realname)
        if True: # if self.pkgexists(package_name):
            self.println(pytmpl[class0]%(classname,doctext))
            self.doprocs(owner, realname)
        else:
            self.err('ERROR: package not found: %s'%(package_name))

#-----------------------------------------------------------------------
# main
#-----------------------------------------------------------------------

def main():
    """Most people have never learned that one of the MAIN aims
       in life is to enjoy it.
         -- Samuel Butler
    """
    p = optparse.OptionParser(usage="usage: %prog options pkg...")
    p.add_option("-C","--conn",action="store",type="string",dest="conn",
                 help="Database connection string")
    p.add_option("-O","--output",action="store",type="string",dest="output",
                 help="Output file")
    p.add_option("","--lang",action="store",type="string",dest="lang",
                 help="Language binding")
    p.add_option("-P","--pass",action="store",type="string",dest="password",
                 help="Database password")
    p.add_option("","--dump",action="store_true",dest="dump",default=False,
                 help="dump datastructures for debugging")
    p.add_option("","--sys",action="store_true",dest="sys",default=False,
                 help="connect as sysdba")
    p.add_option("","--helpfmt",action="store_true",dest="helpfmt",
                 default=False, help="show help for formatting")
    (opts,args) = p.parse_args()

    if not (opts.conn and args):
        p.print_help()
        sys.exit(1)

    oraconnre = re.compile("^([^/@]*)(/([^@]*))?(@(.*))?$")
    user,password,host=oraconnre.match(opts.conn).groups()[0::2]
    if opts.password:
        password=opts.password
    if not password:
        password=getpass.getpass()
    connstr="%s/%s"%(user,password)
    if host:
        connstr+="@%s" % host
    if opts.sys:
        conn=cx_Oracle.connect(connstr,mode=cx_Oracle.SYSDBA)
    else:
        conn=cx_Oracle.connect(connstr)

    if opts.output:
        output=open(opts.output,"w")
    else:
        output=sys.stdout

    if opts.dump:
        trans=Trans(conn,output)
        trans.dump(args)
        sys.exit(0)

    if opts.lang is None or opts.lang=="python" or opts.lang=='py':
        trans=PyTrans(conn,output)
    elif opts.lang=='cxx':
        trans=None
    elif opt.lang=='rb':
        trans=None
    else:
        print >>sys.stderr,'unsupported language:',opt.lang
        sys.exit(1)

    trans.dofile(args)
    sys.exit(0)

main()
