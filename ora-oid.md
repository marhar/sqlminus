If you ever get this on a Mac:

    ORA-21561: OID generation failed

It's because your hostname is not in /etc/hosts and
your hostname has changed, usually because you've gone onto a VPN.

You can wait (usually for a couple of minutes) for your DNS to
catch up, or to fix the problem permanently, add one line to
/etc/hosts as follows:

    ~ $ hostname
    dogbert

    127.0.0.1       localhost  <-- you have this line
    127.0.0.1       dogbert    <-- add this line
