------------------------------------------------------------------------
--+ text about the packakge
--+ more text about the package
------------------------------------------------------------------------

create or replace package tinysample
as
    --------------------------------------------------------------------
    --+ this is a procedure
    --------------------------------------------------------------------
    procedure p0;

    --------------------------------------------------------------------
    --+ this is a procedure
    --+ x : some number
    --------------------------------------------------------------------
    procedure p1(x in number);

    --------------------------------------------------------------------
    --+ this is a function
    --------------------------------------------------------------------
    function f0
        return number;

    --------------------------------------------------------------------
    --+ this is a function
    --+ x : some number
    --------------------------------------------------------------------
    function f1(x in number)
        return number;
end tinysample;
/

create or replace package body tinysample
as
    procedure p0
    is
    begin
        dbms_output.put_line('hello p0');
    end p0;

    procedure p1(x in number)
    is
    begin
        dbms_output.put_line('hello p1');
    end p1;

    function f0
        return number
    is
    begin
        dbms_output.put_line('hello');
        return 17;
    end f0;

    function f1(x in number)
        return number
    is
    begin
        dbms_output.put_line('hello');
        return 18;
    end f1;

    --------------------------------------------------------------------
    --+ this is some internal thing
    --+ note: this is private procedure
    --+ x : some number
    --------------------------------------------------------------------
    procedure private1(x in number)
    is
    begin
        dbms_output.put_line('hello');
    end private1;
end tinysample;
/
