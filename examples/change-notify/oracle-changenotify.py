import cx_Oracle
import time

def callback(message):
    print "Message type:", message.type
    print "Message database name:", message.dbname
    print "Message tables:"
    for table in message.tables:
        print "--> Table Name:", table.name
        print "--> Table Operation:", table.operation
        if table.rows is not None:
            print "--> Table Rows:"
            for row in table.rows:
                print "--> --> Row RowId:", row.rowid
                print "--> --> Row Operation:", row.operation
                print "-" * 60
        print "=" * 60

connection = cx_Oracle.Connection("scott/tiger", events = True)
sub = connection.subscribe(callback = callback, timeout = 1800, rowids = True)
print "Subscription:", sub
print "--> Connection:", sub.connection
print "--> Callback:", sub.callback
print "--> Namespace:", sub.namespace
print "--> Protocol:", sub.protocol
print "--> Timeout:", sub.timeout
print "--> Operations:", sub.operations
print "--> Rowids?:", sub.rowids
sub.registerquery("select * from TestExecuteMany")

while True:
    print "Waiting for notifications...."
    time.sleep(5000)

