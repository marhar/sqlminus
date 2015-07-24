
import cx_Oracle
import unittest
import datetime


class ExportedModuleBase(object):
    """
    Base class used for tests on exported modules
    To test a new sample package, create a new class, inherit from this class and unittest.TestCase
    Then override the module_name property to the name of the sample package to be tested
    """

    module_name=''
    conn=None
    _connstr=''

    def connstr(cls, cnstr):
        cls._connstr=cnstr
    connstr=classmethod(connstr)

    def setUp(self):
        if not self.module_name:
            self.fail('No module name was declared')
        try:
            exec('import %s'%self.module_name.lower())
        except ImportError:
            self.fail("Could not import %s, did you run 'make export-samples'?"%self.module_name)
        if not self._connstr:
            self.fail('No connection string specified')
        if not self.conn:
            ExportedModuleBase.conn=cx_Oracle.Connection(self._connstr)
        self.cur=self.conn.cursor()
        self.package=eval("%s.%s(self.cur)"%(self.module_name.lower(),self.module_name.title()))

    def tearDown(self):
        self.conn.rollback()

    def testCoverage(self):
        """Check that for each function on the package, there is a corresponding function on the test case"""
        for f in [f for f in dir(self.package) if not f.startswith('_') and callable(getattr(self.package,f))]:
            err_msg = 'Python function %s.%s should have a unit test'%(self.package.__class__.__name__,f)
            self.assert_(hasattr(self,'test'+f), err_msg)

    def assertEqualTime(self,dtime,cxtime,msg=None):
        if not isinstance(dtime, datetime.datetime):
            self.fail('First argument is %s not datetime'%str(type(dtime)))
        elif not isinstance(cxtime, cx_Oracle.Timestamp):
            self.fail('Second argument is %s not cx_Oracle'%str(type(cxtime)))
        elif dtime.minute!=cxtime.minute or dtime.hour!=cxtime.hour or dtime.second!=cxtime.second or \
            dtime.month!=cxtime.month or dtime.year!=cxtime.year or dtime.day!=cxtime.day:
            self.fail(msg or '%s does not equal %s'%(dtime,cxtime))


class AllTypesTest(ExportedModuleBase, unittest.TestCase):
    """Tests against the 'alltypes' package"""

    module_name='alltypes'

    #Package Function Tests
    def testf_float(self):
        result=self.package.f_float(1.1, 2.2, 3.3)
        self.assertEquals(1.1, result)

    def testf_number(self):
        result=self.package.f_number(1, 2, 3)
        self.assertEquals(1.0, result)

    def testf_varchar2(self):
        result=self.package.f_varchar2("a", "b", "c")       
        self.assertEquals('a', result)

    def testf_date(self):
        date1=datetime.datetime(2001, 1, 1, 1, 11, 11)
        date2=datetime.datetime(2002, 2, 2, 2, 22, 22)
        date3=datetime.datetime(2003, 3, 3, 3, 33, 33)
        result=self.package.f_date(date1, date2, date3)
        self.assertEqualTime(date1,result)

    def testf_noparms(self):
        result=self.package.f_noparms()
        self.assert_(result is None)

    def testf_timestamp(self):
        date1=datetime.datetime(2001, 1, 1, 1, 11, 11)
        date2=datetime.datetime(2002, 2, 2, 2, 22, 22)
        date3=datetime.datetime(2003, 3, 3, 3, 33, 33)
        result=self.package.f_timestamp(date1,date2,date3)
        self.assertEqualTime(date1,result)

    #Package Procedure Tests
    def testp3_float(self):
        result=self.package.p3_float(1.1, 2.2, 3.3)
        self.assertEquals([1.1,]*3, result)

    def testp3_number(self):
        result=self.package.p3_number(1, 2, 3)
        self.assertEquals([1,]*3, result)

    def testp3_date(self):
        date1=datetime.datetime(2001, 1, 1, 1, 11, 11)
        date2=datetime.datetime(2002, 2, 2, 2, 22, 22)
        date3=datetime.datetime(2003, 3, 3, 3, 33, 33)
        result=self.package.p3_date(date1, date2, date3)
        self.assertEqualTime(date1,result[0])
        self.assertEqualTime(date1,result[1])
        self.assertEqualTime(date1,result[2])

    def testp_noparms(self):
        result=self.package.p_noparms()
        self.assertEquals([],result)

    #Procedures with arrays
    def testp3_varchar2(self):
        result=self.package.p3_varchar2("mh", "bjorn", "bjorn")
        self.assertEquals(['mh','mh','mh'], result)
        
    def testp3_float(self):
        result=self.package.p3_float(1.1, 2.2, 3.3)
        self.assertEquals([1.1000000000000001]*3, result)

    def testp3_number(self):
        result=self.package.p3_number(1, 2, 3)
        self.assertEquals([1]*3, result)

    def testp3_timestamp(self):
        date1=datetime.datetime(2001, 1, 1, 1, 11, 11)
        date2=datetime.datetime(2002, 2, 2, 2, 22, 22)
        date3=datetime.datetime(2003, 3, 3, 3, 33, 33)
        result=self.package.p3_timestamp(date1,date2,date3)
        self.assertEqualTime(date1,result[0])
        self.assertEqualTime(date1,result[1])
        self.assertEqualTime(date1,result[2])

    #Vectorized procedures with arrays
    def testp3_varchar2_V(self):
        result=self.package.p3_varchar2_V([["aaa","bbb","ccc"], ["ccc","ddd","fff"]])
        self.assert_(result is None)

    def testp3_float_V(self):
        result=self.package.p3_varchar2_V([ [1.1, 2.2, 3.3], [4.4, 5.5, 6.6] ])
        self.assert_(result is None)

    def testp3_number_V(self):
        result=self.package.p3_number_V([ [1,1,1] , [2,2,2] , [3,3,3] ])
        self.assert_(result is None)

    def testp3_date_V(self):
        date1=datetime.datetime(2001, 1, 1, 1, 11, 11)
        date2=datetime.datetime(2002, 2, 2, 2, 22, 22)
        date3=datetime.datetime(2003, 3, 3, 3, 33, 33)
        result=self.package.p3_date_V([[date1,date2,date3],[date3,date2,date1]])
        self.assert_(result is None)

    def testp3_timestamp_V(self):
        date1=datetime.datetime(2001, 1, 1, 1, 11, 11)
        date2=datetime.datetime(2002, 2, 2, 2, 22, 22)
        date3=datetime.datetime(2003, 3, 3, 3, 33, 33)
        result=self.package.p3_timestamp_V([[date1,date2,date3],[date3,date2,date1]])
        self.assert_(result is None)

    def testp_noparms_V(self):
        result=self.package.p_noparms_V([[],[],[]])
        self.assert_(result is None)


class TinySampleTest(ExportedModuleBase, unittest.TestCase):
    """Tests against the 'tinysample' package"""

    module_name='tinysample'

    def testf0(self):
        result=self.package.f0()
        self.assertEquals(17,result)

    def testf1(self):
        result=self.package.f1(18)
        self.assertEquals(18,result)

    def testp0(self):
        result=self.package.p0()
        self.assertEquals([],result)

    def testp1(self):
        result=self.package.p1(14)
        self.assertEquals([14],result)

    def testp0_V(self):
        result=self.package.p0_V([[],[],[]])
        self.assert_(result is None)

    def testp1_V(self):
        result=self.package.p1_V([[1],[2],[3]])
        self.assert_(result is None)


class KeywordTest(ExportedModuleBase, unittest.TestCase):
    """Tests against the 'keyword' package"""

    module_name='keyword'
    words = [
        [21,'orange'],
        [21,'blue'],
        [21,'white'],
        [24,'blue'],
        [22,'white']
    ]

    def testadd(self):
        result=self.package.add(22,'blue')
        self.assertEquals([22,'blue'],result)

    def testall_words(self):
        self.package.add_V(self.words)
        result=[w[0] for w in self.package.all_words()]
        words=[w[1]for w in self.words]
        wd = {}
        for w in words:
            wd[w]=None
        words=wd.keys()
        words.sort()
        self.assertEquals(words,result)

    def testdelet(self):
        self.package.add(22,'blue')
        result=self.package.delet(22,'blue')
        self.assertEquals([22,'blue'],result)

    def testget_ids(self):
        self.package.add_V(self.words)
        cur=self.conn.cursor()
        result=self.package.get_ids(cur,'blue')
        self.assert_(result[0] is cur)
        self.assertEquals(result[1],'blue')
        rwords=[w[0] for w in result[0]]
        ewords=[w[0] for w in self.words if w[1]=='blue']
        self.assertEquals(ewords,rwords)

    def testget_keywords(self):
        self.package.add_V(self.words)
        cur=self.conn.cursor()
        result=self.package.get_keywords(cur,21)
        self.assert_(result[0] is cur)
        self.assertEquals(21,result[1])
        result=[f[0] for f in result[0]]
        eresult=[w[1] for w in self.words if w[0]==21]
        eresult.sort()
        result.sort()
        self.assertEquals(eresult,result)

    def testget_keywords2(self):
        self.package.add_V(self.words)
        result=self.package.get_keywords2(21)
        result=[w[0] for w in result]
        eresult=[w[1] for w in self.words]
        ed={}
        for w in eresult:
            ed[w]=None
        eresult=ed.keys()
        eresult.sort()
        result.sort()
        self.assertEquals(eresult,result)

    def testadd_V(self):
        result=self.package.add_V(self.words)
        self.assert_(result is None)

    def testdelet_V(self):
        self.package.add(22,'blue')
        result=self.package.delet(22,'blue')
        self.assertEquals([22,'blue'],result)

    def testget_ids_V(self):
        self.package.add_V(self.words)
        cur=self.conn.cursor()
        cur2=self.conn.cursor()
        result=self.package.get_ids_V([[cur,'blue'],[cur2,'white']])
        self.assert_(result is None)
        result=[w[0] for w in cur]
        eresult=[w[0] for w in self.words if w[1]=='blue']
        self.assertEquals(result,eresult)
        result=[w[0] for w in cur2]
        eresult=[w[0] for w in self.words if w[1]=='white']

    def testget_keywords_V(self):
        self.package.add_V(self.words)
        cur=self.conn.cursor()
        cur2=self.conn.cursor()
        result=self.package.get_keywords_V([[cur,21],[cur2,22]])
        self.assert_(result is None)
        result=[w[0] for w in cur]
        eresult=[w[1] for w in self.words if w[0]==21]
        eresult.sort()
        result.sort()
        self.assertEquals(result,eresult)
        result=[w[0] for w in cur2]
        eresult=[w[1] for w in self.words if w[0]==22]
        eresult.sort()
        self.assertEquals(result,eresult)


if __name__ == '__main__':
    import optparse,sys,re
    p = optparse.OptionParser(usage="usage: %prog options pkg...")
    p.add_option("-C","--conn",action="store",type="string",dest="conn",
                 help="Database connection string")
    p.add_option("-P","--pass",action="store",type="string",dest="password",
                 help="Database password")
    (opts,args) = p.parse_args()
    if opts.conn:
        for a in sys.argv:
            if a.startswith('-C'):sys.argv.remove(a);break;
        oraconnre = re.compile("^([^/@]*)(/([^@]*))?(@(.*))?$")
        user,password,host=oraconnre.match(opts.conn).groups()[0::2]
        if opts.password:
            password=opts.password
        if not password:
            password=getpass.getpass()
        connstr="%s/%s"%(user,password)
        if host:
            connstr+='@'+host
        ExportedModuleBase.connstr(connstr)
    unittest.main()
