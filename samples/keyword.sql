CREATE TABLE KEYWORDS
(
  ID       NUMBER                               NOT NULL,
  KEYWORD  VARCHAR2(32 BYTE)                    NOT NULL
)
LOGGING 
NOCOMPRESS 
NOCACHE
NOPARALLEL
MONITORING;

COMMENT ON TABLE KEYWORDS IS 'table for demonstrating the data access api.';

COMMENT ON COLUMN KEYWORDS.ID IS 'some asset id';

COMMENT ON COLUMN KEYWORDS.KEYWORD IS 'a keyword associated with that id';


CREATE INDEX KEYWORDS_KEYWORD_IX ON KEYWORDS
(KEYWORD)
LOGGING
NOPARALLEL;


CREATE UNIQUE INDEX KEYWORDS_PK ON KEYWORDS
(ID, KEYWORD)
LOGGING
NOPARALLEL;


CREATE INDEX KEYWORDS_ID_IX ON KEYWORDS
(ID)
LOGGING
NOPARALLEL;


CREATE OR REPLACE package keyword
as
    type my_ref is ref cursor;

    --------------------------------------------------------------------
    --+ add a keyword to an asset
    --+ aid       : asset identifier
    --+ akeyword  : keyword to add
    --------------------------------------------------------------------
    procedure add(aid in number, akeyword in varchar2);

    --------------------------------------------------------------------
    --+ delete a keyword from an asset
    --+ aid      : asset identifier
    --+ akeyword : keyword to delete
    --------------------------------------------------------------------
    procedure delet(aid in number, akeyword in varchar2);

    --------------------------------------------------------------------
    --+ find all assets with a given keyword
    --+ aref     : reference cursor for results
    --+ akeyword : specified keyword
    --------------------------------------------------------------------
    procedure get_ids(aref out sys_refcursor, akeyword in varchar2);

    --------------------------------------------------------------------
    --+ find all assets with a given keyword
    --+ aref     : reference cursor for results
    --+ akeyword : specified keyword
    --------------------------------------------------------------------
    procedure get_keywords(aref out sys_refcursor, aid in number);

    --------------------------------------------------------------------
    --+ find all assets with a given keyword
    --+ aref     : reference cursor for results
    --+ akeyword : specified keyword
    --+ returns: iterator over all keywords
    --------------------------------------------------------------------
    function get_keywords2(aid in number)
        return my_ref;

    --------------------------------------------------------------------
    --+ list all the keywords defined for the assets
    --+ returns: ref cursor to iterate over all keywords
    --------------------------------------------------------------------
    function all_words
        return my_ref;
end KEYWORD;
/

SHOW ERRORS;


CREATE OR REPLACE package body KEYWORD
is
    --------------------------------------------------------------------
    procedure add(aid in number, akeyword in varchar2)
    is
    begin
        delete from keywords
              where id = aid and keyword = akeyword;

        insert into keywords
                    (id, keyword)
             values (aid, akeyword);
    end add;

    --------------------------------------------------------------------
    procedure delet(aid in number, akeyword in varchar2)
    is
    begin
        delete from keywords
              where id = aid and keyword = akeyword;
    end delet;

    --------------------------------------------------------------------
    procedure get_ids(aref out sys_refcursor, akeyword in varchar2)
    is
    begin
        open aref for
            select id
              from keywords
             where keyword = akeyword;
    end get_ids;

    --------------------------------------------------------------------
    procedure get_keywords(aref out sys_refcursor, aid in number)
    is
    begin
        open aref for
            select keyword
              from keywords
             where id = aid;
    end get_keywords;

    --------------------------------------------------------------------
    function get_keywords2(aid in number)
        return my_ref
    is
        xref   my_ref;
    begin
        open xref for
            select keyword
              from keywords
             where id = aid;

        return xref;
    end get_keywords2;

    --------------------------------------------------------------------
    function all_words
        return my_ref
    is
        xref   my_ref;
    begin
        open xref for
            select distinct keyword
                       from keywords
                   order by keyword;

        return xref;
    end all_words;
end keyword;
/

SHOW ERRORS;


ALTER TABLE KEYWORDS ADD (
  CONSTRAINT KEYWORDS_PK
 PRIMARY KEY
 (ID, KEYWORD));

