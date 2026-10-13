import os, os.path

def gae_engine_url(db, remote = False) :
    port = 3306  # default mysql port
    charset = 'utf8mb4' # default charset in MySQL 8.0+

    user = os.environ.get('db_user')
    assert user, "Invalid call"

    pswd = os.environ.get('db_password')
    assert pswd, "No password"
    
    host = os.environ.get('cloudsql_host') if remote else "localhost"

    if len(pswd or '') < 4 :
        sub_pswd = '****'
    else :
        sub_pswd = pswd[0] + '*' * (len(pswd) - 2) + pswd[-1]

    if os.getenv('GAE_ENV', '').startswith('standard') :
        # GAE production environment

        conn_name = os.environ.get('CLOUDSQL_CONNECTION_NAME')
        assert conn_name, "CLOUDSQL_CONNECTION_NAME not set"

        unix_socket = os.path.join(os.environ.get("DB_SOCKET_DIR", "/cloudsql"), conn_name)

        return f'mysql+pymysql://{user}:{pswd}@/{db}?unix_socket={unix_socket}&charset={charset}', \
               f'mysql+pymysql://{user}:{sub_pswd}@/{db}?unix_socket={unix_socket}&charset={charset}'

    else :
        return f'mysql+pymysql://{user}:{pswd}@{host}:{port}/{db}?local_infile=1&charset={charset}', \
               f'mysql+pymysql://{user}:{sub_pswd}@{host}:{port}/{db}?local_infile=1&charset={charset}'
