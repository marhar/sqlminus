sqlminus
========

A lightweight, modern replacement for sqlplus.
  [(docs)](https://github.com/marhar/sqlminus/tree/master/sqlminus)

- readline support
- table, column completions
- optimized table formatting
- development tools

Also includes a couple of other handy Oracle things.

- orapig -- oracle python interface generator.  Generate Python classes that correspond to PL/SQL packages.
  [(docs)](https://github.com/marhar/sqlminus/tree/master/orapig)
- configomat -- bake database tables into Python and C data structures.
  [(docs)](https://github.com/marhar/sqlminus/tree/master/configomat)

All of these packages use Python and the excellent cx_Oracle package.

- [Installing cx_Oracle on Mac](https://github.com/marhar/sqlminus/tree/master/docs/mac-install-source.md)
- [Sample packages used in this documentation](https://github.com/marhar/sqlminus/tree/master/docs/sample-packages.md)

Binary Distribution

- I've put together a binary distribution for MacOS in case you're
- not interested in building a cx_Oracle environment.
  [(docs)](https://github.com/marhar/sqlminus/tree/master/docs/mac-install-binaries.md)
