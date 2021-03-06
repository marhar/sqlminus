#!/Users/mh/stools/bin/python
#-----------------------------------------------------------------------
# gen_testcases -- generate test cases for code generator
#
# todo:
#  figure out inout parms
#  ref cursor return
#  check against http://www.psoug.org/reference/packages.html
#-----------------------------------------------------------------------

########################################################################
########################################################################

HPKGHEAD="""
------------------------------------------------------------------------
--+ %(pkg)s -- autogenerated package named %(pkg)s
------------------------------------------------------------------------

create or replace package %(pkg)s
as
"""

HPKGFOOT="""
    --------------------------------------------------------------------
    --+ p_noparms -- test a proc with no parameters
    --+ parameters:
    --+   none
    --------------------------------------------------------------------
    procedure p_noparms;

    --------------------------------------------------------------------
    --+ f_noparms -- test a function with no parameters
    --+ parameters:
    --+   none
    --------------------------------------------------------------------
    function f_noparms return number;

end %(pkg)s;
/
"""

HPROC="""
    --------------------------------------------------------------------
    --+ p3_%(type)s -- test the type %(type)s
    --+ parameters:
    --+   x_%(type)s_in : in parameter of type %(type)s
    --+   x_%(type)s_out : out parameter of type %(type)s
    --+   x_%(type)s_inout : inout parameter of type %(type)s
    --------------------------------------------------------------------
    procedure p3_%(type)s(
        x_%(type)s_in in %(type)s,
        x_%(type)s_out out %(type)s,
        x_%(type)s_inout in out %(type)s
    );
"""

HFUNC="""
    --------------------------------------------------------------------
    --+ f_%(type)s -- test the type %(type)s
    --+ parameters:
    --+   x_%(type)s_in : in parameter of type %(type)s
    --+   x_%(type)s_out : out parameter of type %(type)s
    --+   x_%(type)s_inout : inout parameter of type %(type)s
    --+ returns:
    --+   a value of type %(type)s
    --------------------------------------------------------------------
    function f_%(type)s(
        x_%(type)s_in in %(type)s,
        x_%(type)s_out out %(type)s,
        x_%(type)s_inout in out %(type)s
    ) return %(type)s;
"""

########################################################################
########################################################################

BPKGHEAD="""
create or replace package body %(pkg)s
as
"""

BPKGFOOT="""
    --------------------------------------------------------------------
    procedure p_noparms
    is
    begin
        dbms_output.put_line('p_noparms:');
    end p_noparms;

    --------------------------------------------------------------------
    function f_noparms
    return number
    is
    begin
        dbms_output.put_line('f_noparms:');
        return NULL;
    end f_noparms;

    --------------------------------------------------------------------
    procedure p_private
    is
    begin
        dbms_output.put_line('p_private:');
    end p_private;
end %(pkg)s;
/
"""

BPROC="""
    --------------------------------------------------------------------
    procedure p3_%(type)s(
        x_%(type)s_in in %(type)s,
        x_%(type)s_out out %(type)s,
        x_%(type)s_inout in out %(type)s
    )
    is
    begin
        dbms_output.put_line('p3_%(type)s: ' ||
            to_char(x_%(type)s_in)||' '||
            to_char(x_%(type)s_out)||' '||
            to_char(x_%(type)s_inout));
        x_%(type)s_out := x_%(type)s_in;
        x_%(type)s_inout := x_%(type)s_in;
        dbms_output.put_line('p3_%(type)s: ' ||
            to_char(x_%(type)s_in)||' '||
            to_char(x_%(type)s_out)||' '||
            to_char(x_%(type)s_inout));
    end p3_%(type)s;
"""

BFUNC="""
    --------------------------------------------------------------------
    function f_%(type)s(
        x_%(type)s_in in %(type)s,
        x_%(type)s_out out %(type)s,
        x_%(type)s_inout in out %(type)s
    )
    return %(type)s
    is
    begin
        dbms_output.put_line('p3_%(type)s: ' ||
            to_char(x_%(type)s_in)||' '||
            to_char(x_%(type)s_out)||' '||
            to_char(x_%(type)s_inout));
        x_%(type)s_out := x_%(type)s_in;
        dbms_output.put_line('p3_%(type)s: ' ||
            to_char(x_%(type)s_in)||' '||
            to_char(x_%(type)s_out)||' '||
            to_char(x_%(type)s_inout));
        return x_%(type)s_in;
    end f_%(type)s;
"""

########################################################################
########################################################################

TYPES=[
'varchar2',
'number',
'date',
'float',
'timestamp'
]

HPKGHEAD=HPKGHEAD.strip('\n')
HPKGFOOT=HPKGFOOT.strip('\n')
HPROC=HPROC.strip('\n')
HFUNC=HFUNC.strip('\n')

BPKGHEAD=BPKGHEAD.strip('\n')
BPKGFOOT=BPKGFOOT.strip('\n')
BPROC=BPROC.strip('\n')
BFUNC=BFUNC.strip('\n')

pkgname='alltypes'
print HPKGHEAD%{'pkg':pkgname}
for i in TYPES:
    print HPROC%{'type':i}
for i in TYPES:
    print HFUNC%{'type':i}
print HPKGFOOT%{'pkg':pkgname}

print BPKGHEAD%{'pkg':pkgname}
for i in TYPES:
    print BPROC%{'type':i}
for i in TYPES:
    print BFUNC%{'type':i}
print BPKGFOOT%{'pkg':pkgname}
