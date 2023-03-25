import os, re, logging, inspect
from sqlalchemy import create_engine, __version__ as sqlalchemy_version
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

class SQLDBConnector :
    def __init__ (self, pool=None, engine_url=None, engine_url_dbg=None, echo=False) :
        if not sqlalchemy_version.startswith("1.") :
            logging.critical("This implementation is incopatible with SQLAlchemy version %s", sqlalchemy_version)
            logging.info("To revert back to 1.4.44, run this command: python3 -m pip install --force-reinstall 'SQLAlchemy==1.4.44'")
            exit(1)

        assert int(pool is None) + int(engine_url is None) == 1, \
            "Exactly one of `pool` and `engine_url` must be provided"

        if pool :
            self._pool = pool
            self.session = None
        else :
            # This is for local dev testing
            # raise RuntimeError("NO!!!!!!!!!!!!")
            self._pool, self.session = self.make_pool(engine_url, engine_url_dbg, False, echo=echo, poolclass=NullPool)

        self._conn = None
        self._proxy = None
        self._dry_run = False
        self._dbg_connection_url = None

    @staticmethod
    def make_pool(engine_url, engine_url_dbg, from_flask, **pars) :
        # For some weird reason when commenced from flask app logging doesn't work here and breaks logging down the road
        if from_flask :
            print("Allocating pool", engine_url_dbg, "with parameters", pars)
        else :
            logging.info("Allocating pool at %s with options %s", engine_url_dbg, pars)

        pool = create_engine(engine_url, **pars)
        sqla_session = scoped_session(sessionmaker(bind=pool))

        return pool, sqla_session

    def get_engine(self) :
        return self._pool

    @classmethod
    def set_env_from_yaml(cls, app_yaml=None):
        from ..gae import dbgyamlenv
        if app_yaml is None:
            app_yaml = cls.app_yaml

        dbgyamlenv.set_env_from_yaml(app_yaml)

    def set_dry_run(self, dry_run=True) :
        old_dry_run = self._dry_run
        if dry_run != old_dry_run :
            self._dry_run = dry_run
            if dry_run :
                logging.info("Set dry run mode")
            else :
                logging.info("Unset dry run mode")
        return old_dry_run

    def execute(self, in_query, *pars) :
        if self._conn is None:
            self._conn = self._pool.connect ()
            logging.info("Allocating connection from pool")

        stack = inspect.stack ()
        ii = 0
        while 'execute' in stack[ii][3] : ii += 1
        caller = "{}:{}".format(os.path.basename(stack[ii][1]), stack[ii][2])
        query = re.compile(r'\s+').sub(' ',in_query.format(**self.tables)).strip()
        issel = query.lower().startswith('select')
        res = False
        if len(pars) == 0 :
            logging.info(caller + " ~~ " + query)
            if issel or not self._dry_run :
                res = self._conn.execute(query)
        elif '_binary %s' in query or '_text %s' in query :
            # logging.debug(caller + " ~~ " + "%s (+ %d params)", query, len(pars))
            npars = []
            for ii,f in enumerate([i.group() for i in re.compile(r'(_binary |_text )?%s').finditer(query)]) :
                if '_binary' in f :
                    ascii_par = pars[ii].hex()
                    if len(ascii_par) > 10 :
                        ascii_par = ascii_par[:10] + '...'
                    npars.append("{%s}[%d bytes]" % (ascii_par,len(pars[ii])))
                elif '_text' in f :
                    text_par = pars[ii]
                    if len(text_par) > 50 :
                        text_par = text_par[:50] + '...'
                    npars.append("{%s}[%d chars]" % (text_par,len(pars[ii])))
                else :
                    npars.append(pars[ii])
            logging.info(caller + " ~~ " + query, *npars)
            if issel or not self._dry_run :
                res = self._conn.execute(query.replace('_text %s','%s'), pars)
        else :
            # logging.info("query = %s, pars = %s", query, pars)
            lim = 50
            logging.info(caller + " ~~ " + query, *[x if not isinstance(x, str) or len(x) < lim + 5 else x[:lim] + '... [%d chars]' % len(x) for x in pars])
            if issel or not self._dry_run :
                res = self._conn.execute(query, pars)
        if res is False :
            logging.debug("Query not actually run in dry run mode")
            return res
        n = res.rowcount
        if n :
            logging.debug("Query returned: %d", n)

        self._close_proxy()
        self._proxy = res
        return n

    def commit(self) :
        # https://stackoverflow.com/questions/26717790/how-to-set-autocommit-1-in-a-sqlalchemy-engine-connection
        # Wne not dealing with transactions, auto-commit is assumed
        logging.info("commit() has no effect in no-transaction mode")
        if False:
            logging.debug("COMMIT" + (" (dry run mode)" if self._dry_run else ""))
            if not self._dry_run :
                return self._conn.commit()

    def commit_on_exit (self) :
        self.commit_requested = True

    def commit_if_requested (self) :
        if self.commit_requested :
            self.commit ()
            self.commit_requested = False

    def rollback(self) :
        # https://stackoverflow.com/questions/26717790/how-to-set-autocommit-1-in-a-sqlalchemy-engine-connection
        # Wne not dealing with transactions, auto-commit is assumed
        logging.warning("rollback() has no effect in no-transaction mode")
        if False:
            logging.debug("ROLLBACK"  + (" (dry run mode)" if self._dry_run else ""))
            if not self._dry_run :
                return self._conn.rollback()

    def close(self) :
        if self._conn :
            logging.debug("Closing connection")
            self._conn.close()
            self._conn = None
        if self.session :
            logging.debug("Remove session")
            self.session.remove ()
            self.session = None

    def fetchone(self) :
        res = self._proxy.fetchone()
        self._close_proxy ()
        return res

    def fetchall(self) :
        res = self._proxy.fetchall()
        self._close_proxy ()
        return res

    def get_columns(self) :
        return self._proxy._metadata.keys

    def __iter__(self) :
        return iter(self._proxy)

    def print_formatted(self) :
        def print_column(val) :
            if val is None :
                return ""
            elif isinstance(val,str) :
                return re.compile(r'\s+', re.S).sub(' ', val).strip()
            else :
                return val

        from ..cli.genformatter import GenericFormatter
        out = GenericFormatter("aligned,width=30")
        irow = 0
        for row in self._conn :
            irow += 1
            if irow == 1 :
                out.writeheader([desc[0] for desc in self._conn.description])
            out.writerow(list(map(print_column,row)))
        out.close ()

    def _close_proxy(self) :
        if self._proxy :
            self._proxy.close()
            self._proxy = None

    def set_dbg_connection_url(self, url):
        self._dbg_connection_url = url

    def get_dbg_connection_url(self):
        return self._dbg_connection_url

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close ()
