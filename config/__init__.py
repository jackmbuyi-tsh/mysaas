# PyMySQL is a pure-Python driver, so no C build tools are needed
# to talk to MariaDB. It registers itself as MySQLdb for Django.
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover
    pass
