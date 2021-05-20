import os, os.path

def gae_engine_url(db, remote = False) :
    port = 3306  # default mysql port
    user     = os.environ.get('db_user')

    assert user, "Invalid call"
    pswd = os.environ.get('db_password')
    host = os.environ.get('cloudsql_host') if remote else "localhost"

    if len(pswd or '') < 4 :
        sub_pswd = '****'
    else :
        sub_pswd = pswd[0] + '*' * (len(pswd) - 2) + pswd[-1]

    if os.getenv('GAE_ENV', '').startswith('standard') :
        # GAE produnction environment

        unix_socket = os.path.join(os.environ.get("DB_SOCKET_DIR", "/cloudsql"),
             os.environ.get('CLOUDSQL_CONNECTION_NAME'))

        return f'mysql+pymysql://{user}:{pswd}@/{db}?unix_socket={unix_socket}', \
               f'mysql+pymysql://{user}:{sub_pswd}@/{db}?unix_socket={unix_socket}'

    else :
        return f'mysql+pymysql://{user}:{pswd}@{host}:{port}/{db}?local_infile=1', \
               f'mysql+pymysql://{user}:{sub_pswd}@{host}:{port}/{db}?local_infile=1'
