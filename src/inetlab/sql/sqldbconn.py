import os, re, logging, inspect
from typing import Any, ClassVar

import sqlalchemy
from sqlalchemy import create_engine, __version__ as sqlalchemy_version, text as text_wrapper, Connection, CursorResult, Row
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

re_execute1 = re.compile('(?<!%)%s')
re_execute2 = re.compile(r'(?:(_binary|_text)\s+)?:([a-z0-9_]+)')

class SQLDBConnector :
    # Must be provided by derived classes
    tables : ClassVar[dict[str, str]]
    app_yaml : ClassVar[str]
    _conn : Connection|None
    _proxy : CursorResult[Any]|None
    database: ClassVar[str]

    @classmethod
    def _local_credentials(cls) :
        """
        Only used for local development: on App Engine the app runs as its service account, so Application Default
        Credentials (ADC) are used as is. Locally, ADC are your own (`gcloud auth application-default login`), and we
        impersonate the app's service account (from app.yaml) so that IAM database login uses the same DB user as the
        deployed app. Requires roles/iam.serviceAccountTokenCreator on that service account.
        """
        import yaml
        import google.auth
        from google.auth import impersonated_credentials

        with open(cls.app_yaml) as f :
            service_account = yaml.safe_load(f)['service_account']
        source_credentials, _ = google.auth.default()
        return impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=service_account,
            target_scopes=["https://www.googleapis.com/auth/sqlservice.admin"])

    @classmethod
    def make_engine_project(cls, gae_project: str, remote_db: bool, local_dev: bool, echo: bool = False) :
        connect_args = {"charset": "utf8mb4", "local_infile" : True}
        pool_config : dict[str, Any]

        if remote_db:
            from google.cloud.sql.connector import Connector

            # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/main/cloud-sql/mysql/sqlalchemy/connect_tcp.py
            pool_config = {
                # [START cloud_sql_mysql_sqlalchemy_limit]
                # Pool size is the maximum number of permanent connections to keep.
                "pool_size": 5,
                # Temporarily exceeds the set pool_size if no connections are available.
                "max_overflow": 2,
                # The total number of concurrent connections for your application will be
                # a total of pool_size and max_overflow.
                # [END cloud_sql_mysql_sqlalchemy_limit]
                # [START cloud_sql_mysql_sqlalchemy_backoff]
                # SQLAlchemy automatically uses delays between failed connection attempts,
                # but provides no arguments for configuration.
                # [END cloud_sql_mysql_sqlalchemy_backoff]
                # [START cloud_sql_mysql_sqlalchemy_timeout]
                # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
                # new connection from the pool. After the specified amount of time, an
                # exception will be thrown.
                "pool_timeout": 30,  # 30 seconds
                # [END cloud_sql_mysql_sqlalchemy_timeout]
                # [START cloud_sql_mysql_sqlalchemy_lifetime]
                # 'pool_recycle' is the maximum number of seconds a connection can persist.
                # Connections that live longer than the specified amount of time will be
                # reestablished
                "pool_recycle": 1800,  # 30 minutes
                # [END cloud_sql_mysql_sqlalchemy_lifetime]
            }

            if echo:
                pool_config['echo'] = echo

            # Only need this locally to avoid the warning (otherwise harmless)
            if local_dev:
                os.environ.setdefault("GOOGLE_CLOUD_PROJECT", gae_project)
                os.environ.setdefault("GOOGLE_CLOUD_QUOTA_PROJECT", gae_project)

            connector = Connector(
                quota_project=gae_project,
                credentials=cls._local_credentials() if local_dev else None
            )

            engine = create_engine(
                "mysql+pymysql://",
                creator=lambda: connector.connect(
                    os.environ['CLOUDSQL_CONNECTION_NAME'],
                    "pymysql",
                    user=os.environ['sql_user'],
                    db=cls.database,
                    enable_iam_auth=True,
                    **connect_args
                ),
                **pool_config
            ) 
  
        else :
            host = "localhost"
            port = 3306
            pool_config = {
                "poolclass" : NullPool
            }
            if echo:
                pool_config['echo'] = echo

            prefix = f"{host}:{port}:{cls.database}:"
            with open(os.path.expanduser('~/.pgpass')) as f :
                for line in f :
                    if line.startswith(prefix) :
                        db_user, db_pass = line.rstrip('\n')[len(prefix):].split(':', 1)
                        break
                else :
                    raise RuntimeError(f"No entry '{prefix}<db_user>:<db_pass>' found in ~/.pgpass")

            # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
            connect_url = sqlalchemy.engine.url.URL.create(
                            drivername="mysql+pymysql",
                            username=db_user,
                            password=db_pass,
                            host=host,
                            port=port,
                            database=cls.database,
                            query={k: str(v) for k, v in connect_args.items()})
            print("Connecting to", connect_url)
            engine = sqlalchemy.create_engine(connect_url, **pool_config)

        return engine

    def __init__ (self, pool=None, engine_url=None, engine_url_dbg=None, echo=False) :
        self._sqlalchemy2 = not sqlalchemy_version.startswith("1.")

        # if self._sqlalchemy2 :
            # To revert back to 1.4.44, run this command: python3 -m pip install --force-reinstall 'SQLAlchemy==1.4.44
            # logging.info("SQLAlchemy version %s, support is experimental", sqlalchemy_version)

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

    def set_dry_run(self, dry_run : bool = True) -> bool :
        old_dry_run = self._dry_run
        if dry_run != old_dry_run :
            self._dry_run = dry_run
            if dry_run :
                logging.info("Set dry run mode")
            else :
                logging.info("Unset dry run mode")
        return old_dry_run

    def execute2(self, in_query, **pars) -> int :
        assert self._sqlalchemy2

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
                res = self._conn.execute(text_wrapper(query))
        else :
            # logging.info("query = %s, pars = %s", query, pars)
            lim = 50
            def ps(m) :
                k = m.group(2)
                if k in pars:
                    if m.group(1) == '_text' :
                        assert isinstance(pars[k], str), f"parameter {k} of type {type(pars[k]).__name__}"
                        text_par = pars[k]
                        if len(text_par) > lim :
                            text_par = text_par[:lim-3] + '...'
                        return f"TXT[{text_par}[{len(pars[k])} chars]]"
                    elif m.group(1) == '_binary' :
                        assert isinstance(pars[k], bytes), f"parameter {k} of type {type(pars[k]).__name__}"
                        ascii_par = pars[k].hex()
                        if len(ascii_par) > 10 :
                            ascii_par = ascii_par[:10] + '...'
                        return f"BIN[{ascii_par}[{len(pars[k])} bytes]]"
                    elif isinstance(pars[k], str) :
                        if len(pars[k]) > lim :
                            return pars[k][:lim-3] + '...'
                        else :
                            return pars[k]
                    else :
                        return str(pars[k])
                else :
                    return f"<ERROR:{k}>"
            logging.info(caller + " ~~ " + re_execute2.sub(ps, query))
            if issel or not self._dry_run :
                res = self._conn.execute(text_wrapper(query.replace('_text', '')), pars)
        if res is False :
            logging.debug("Query not actually run in dry run mode")
            return res
        n = res.rowcount
        if n :
            logging.debug("Query returned: %d", n)

        self._close_proxy()
        self._proxy = res
        return n

    def execute(self, in_query, *pars) -> int :
        if self._sqlalchemy2 :
            # logging.info("query[1] = %s, pars = %s", in_query, pars)

            idx = [0]
            def par_sub(m) :
                idx[0] += 1
                return f":par_{idx[0]}"

            query2 = re_execute1.sub(par_sub, in_query)
            assert idx[0] == len(pars), f"query {in_query}, passed {len(pars)} pars but replaced {idx[0]}"

            pars2 = {f"par_{x+1}" : pars[x] for x in range(len(pars))}
            return self.execute2(query2, **pars2)
        else :
            return self.execute1(in_query, *pars)

    def execute1(self, in_query, *pars) -> int :
        assert not self._sqlalchemy2

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
                res = self._conn.execute(text_wrapper(query))
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
                res = self._conn.execute(text_wrapper(query.replace('_text %s','%s')), pars)
        else :
            # logging.info("query = %s, pars = %s", query, pars)
            lim = 50
            logging.info(caller + " ~~ " + query, *[x if not isinstance(x, str) or len(x) < lim + 5 else x[:lim] + '... [%d chars]' % len(x) for x in pars])
            if issel or not self._dry_run :
                res = self._conn.execute(text_wrapper(query), pars)
        if res is False :
            logging.debug("Query not actually run in dry run mode")
            return res
        n = res.rowcount
        if n :
            logging.debug("Query returned: %d", n)

        self._close_proxy()
        self._proxy = res
        return n

    def commit(self) -> None :
        # https://stackoverflow.com/questions/26717790/how-to-set-autocommit-1-in-a-sqlalchemy-engine-connection
        # Wne not dealing with transactions, auto-commit is assumed
        if self._sqlalchemy2 :
            logging.debug("COMMIT" + (" (dry run mode)" if self._dry_run else ""))
            if not self._dry_run and self._conn:
                return self._conn.commit()
        else :
            logging.info("commit() has no effect in no-transaction mode")

    def commit_on_exit (self) :
        self.commit_requested = True

    def commit_if_requested (self) :
        if self.commit_requested :
            self.commit ()
            self.commit_requested = False

    def rollback(self) :
        # https://stackoverflow.com/questions/26717790/how-to-set-autocommit-1-in-a-sqlalchemy-engine-connection
        # Wne not dealing with transactions, auto-commit is assumed
        if self._sqlalchemy2 :
            logging.debug("ROLLBACK"  + (" (dry run mode)" if self._dry_run else ""))
            if not self._dry_run and self._conn :
                return self._conn.rollback()
        else :
            logging.warning("rollback() has no effect in no-transaction mode")

    def close(self) :
        if self._conn :
            logging.debug("Closing connection")
            self._conn.close()
            self._conn = None
        if self.session :
            logging.debug("Remove session")
            self.session.remove ()
            self.session = None

    def fetchone(self) -> Row[Any] | None :
        assert self._proxy
        res = self._proxy.fetchone()
        self._close_proxy ()
        return res

    def getone(self) -> Row[Any] :
        res = self.fetchone()
        assert res is not None
        return res    

    def fetchall(self) :
        assert self._proxy
        res = self._proxy.fetchall()
        self._close_proxy ()
        return res

    def get_columns(self) :
        assert self._proxy
        return self._proxy._metadata.keys

    def __iter__(self) :
        assert self._proxy
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
        assert self._conn is not None
        for row in self :
            irow += 1
            if irow == 1 :
                out.writeheader([desc[0] for desc in self.get_columns()])
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
