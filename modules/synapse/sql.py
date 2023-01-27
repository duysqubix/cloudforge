import logging

logging.basicConfig(level=logging.DEBUG)

import pyodbc
import argparse

from pathlib import Path

parser = argparse.ArgumentParser()
sub_parser = parser.add_subparsers(help='subcommands', dest='subcmd')

deploy_subcmd = sub_parser.add_parser(
    'deploy', help='deploy sql scripts to dedicated SQL pools')

deploy_subcmd.add_argument('--workspace_name',
                           '-w',
                           help='Synapse Workspace Name',
                           required=True)
deploy_subcmd.add_argument('--database',
                           '-d',
                           help='Database name',
                           required=True)
deploy_subcmd.add_argument('--username',
                           '-u',
                           help='username name',
                           required=True)
deploy_subcmd.add_argument('--password',
                           '-p',
                           help='password to access database',
                           required=True)

deploy_subcmd.add_argument("--target-dir",
                           '-t',
                           help='directory of sql scripts',
                           required=True)

args = parser.parse_args()


def create_conn_string(name, db, username, password):
    server = f"{name}.sql.azuresynapse.net"
    return (
        'DRIVER={ODBC Driver 17 for SQL Server};' + f'SERVER=tcp:{server};' +
        'PORT=1433;' + f'DATABASE={db};' + f'UID={username};' +
        f'PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'
    )


def deploy_scripts(sqlscripts):
    name = args.workspace_name
    db = args.database
    username = args.username
    pwd = args.password

    conn_string = create_conn_string(name, db, username, pwd)
    with pyodbc.connect(conn_string, autocommit=True) as conn:
        for scriptname, sqlscript in sqlscripts.items():
            with conn.cursor() as cursor:
                print("Executing Script: ", scriptname, '.........', end='')
                cursor.execute(sqlscript)
                try:
                    print(cursor.fetchall())
                except:
                    print(cursor.messages)


if __name__ == '__main__':
    scripts_path = Path(args.target_dir)
    scripts = []
    for script in scripts_path.glob("*.sql"):
        scripts.append(script)

    scripts.sort(key=lambda x: x.stem)

    sqlscripts = {}
    for sorted_script in scripts:
        with open(sorted_script, 'r') as f:
            sqlscripts[sorted_script.name] = (f.read())

    deploy_scripts(sqlscripts)
