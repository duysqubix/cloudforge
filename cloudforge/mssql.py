from datetime import datetime
from collections import deque
from pygments.formatters import find_formatter_class
from pygments.lexers import find_lexer_class_by_name

import pyodbc
import re
import sys
import pygments


from . import logger, MSSQL_MIGRATION_CONTROL_TABLE_NAME, DEFAULT_ODBC_MSSQL_DRIVER
from .utils import is_interactive


class ODBCValue:
    def __init__(self, value, sensitive=False):
        self._value = str(value)
        self._sensitive = sensitive

    def __str__(self):
        if self._sensitive:
            return "****"
        return self._value

    def __repr__(self):
        return self.__str__()

    def get_raw_value(self):
        return self._value


class ODBCConnection:
    def __init__(self, database_uri, username, password, **options):
        database_uri = database_uri.split("://")

        if len(database_uri) != 2:
            raise ValueError(
                "Database URI must be in the format of `worksapce://<database_name>`, %s"
                % database_uri
            )

        self.server = database_uri[0]
        self.db = database_uri[1]
        self.username = username
        self.password = password

        self.setup()

        # ensure all keys are uppercase for driver connection string
        options = {k.upper(): ODBCValue(v) for k, v in options.items()}

        self.conn_string = self.create_conn_string(**options)

    def setup(self):
        pass

    def create_conn_string(self):
        raise NotImplementedError

    def execute(self, cursor, sql):
        logger.debug(f"Executing SQL: \n{sql}")
        cursor.execute(sql)
        return cursor


class MSSQLConnection(ODBCConnection):
    def create_conn_string(self, timeout=30, port=1433, **options):
        main_options = {
            "DRIVER": ODBCValue(DEFAULT_ODBC_MSSQL_DRIVER),
            "SERVER": ODBCValue(f"tcp:{self.server}"),
            "PORT": ODBCValue(port),
            "DATABASE": ODBCValue(self.db),
            "UID": ODBCValue(self.username),
            "PWD": ODBCValue(self.password, sensitive=True),
            "CONNECTION TIMEOUT": ODBCValue(timeout),
        }

        # options take precedence over main options
        combined = {**main_options, **options}
        print(combined)

        con_string = ""
        con_string += ";".join(
            [f"{k}={v.get_raw_value()}" for k, v in combined.items()]
        )
        if con_string[-1] != ";":
            con_string += ";"
        return con_string

    def execute_script(self, script, conn_string=None):
        _con_str = self.conn_string if conn_string is None else conn_string

        with pyodbc.connect(_con_str, autocommit=True) as conn:
            cursor = conn.cursor()
            batches = script.split("GO")

            results = []
            for batch in batches:
                batch = batch.strip()

                if batch:
                    self.execute(cursor, batch)

                    if cursor.description:
                        results.append(cursor.fetchall())

            cursor.close()
            return results


class SynapseAnalyticsConnection(MSSQLConnection):
    def setup(self):
        self.server = f"{self.server}.sql.azuresynapse.net"

    def create_conn_string(self, timeout=30, port=1433, **options):
        """Creates a connection string for Synapse Analytics Dedicated SQL Pool"""
        if "ENCRYPT" not in options:
            options["ENCRYPT"] = ODBCValue("yes")

        if "TRUSTSERVERCERTIFICATE" not in options:
            options["TRUSTSERVERCERTIFICATE"] = ODBCValue("no")

        return super().create_conn_string(timeout=timeout, port=port, **options)


class DBObject:
    DEPENDS_ON_PATTERN = r"/\*\s*DependsOn:\s*\[(.*?)\]\s*\*/"

    def __init__(self, filename, content):
        self.filename = filename
        self.content = content
        self.dependencies = self._extract_dependencies()
        logger.debug(f"Dependencies for {filename}: {self.dependencies}")

    def _extract_dependencies(self):
        matches = list(
            re.finditer(self.DEPENDS_ON_PATTERN, self.content, re.DOTALL | re.MULTILINE)
        )

        if len(matches) > 1:
            raise ValueError("Multiple DependsOn statements found")
        elif len(matches) == 1:
            dependency_string = matches[0].group(1)
            dependencies = [
                dep.strip() for dep in dependency_string.split(",") if dep.strip()
            ]
            return dependencies
        return []


class DBObjectResolver:
    def __init__(self, db_objects_dict):
        self.db_objects = {
            filename: DBObject(filename, content["query"])
            for filename, content in db_objects_dict.items()
        }
        self.execution_order = self._resolve_dependencies()
        self.execution_order.reverse()

    def _resolve_dependencies(self):
        order, visiting, visited = deque(), set(), set()

        def visit(db_object):
            if db_object.filename not in visited:
                if db_object.filename in visiting:
                    raise ValueError(
                        f"Circular dependency detected: {db_object.filename}"
                    )

                visiting.add(db_object.filename)
                for dependency_name in db_object.dependencies:
                    if dependency_name in self.db_objects:
                        visit(self.db_objects[dependency_name])
                    else:
                        raise ValueError(f"Dependency {dependency_name} not found")
                visiting.remove(db_object.filename)
                visited.add(db_object.filename)
                order.appendleft(db_object.filename)

        for db_object in self.db_objects.values():
            visit(db_object)

        return list(order)

    def get_execution_order(self):
        return self.execution_order


class Migration:
    def __init__(
        self,
        db_con,
        initial_setup,
        etl_objects,
        migrations,
    ) -> None:
        self.db_con = db_con
        self.etl_objects = etl_objects
        self.migrations = migrations

        # sort migrations by name
        self.migrations.sort(key=lambda x: x["name"])

        self.initial_setup = initial_setup

        self.interactive = False

    def deploy(self, interactive=True):
        self.interactive = interactive
        if self.interactive:
            if not is_interactive():
                logger.error(
                    "Interactive mode enabled, but executor is not interactive"
                )

        logger.debug(
            "************************* Initial Script Execution *************************"
        )
        self._execute_initial_setup()

        logger.debug(
            "************************* Migrations ***************************************"
        )
        self._execute_migrations()

        logger.debug(
            "************************* ETL Objects **************************************"
        )

        self._execute_etl_objects()

    def migration_exist(self, name):
        _stmt = f"SELECT COUNT(1) FROM {MSSQL_MIGRATION_CONTROL_TABLE_NAME} WHERE ScriptName ='{name}'"
        results = self.db_con.execute_script(
            _stmt,
        )[0][
            0
        ][0]
        return results > 0

    def add_migration(self, name, timestamp=None):
        if self.migration_exist(name):
            logger.error(f"Migration {name} already exists")
            return

        now = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        _stmt = f"INSERT INTO {MSSQL_MIGRATION_CONTROL_TABLE_NAME} (ScriptName, Applied) VALUES ('{name}', '{now}')"
        results = self.db_con.execute_script(
            _stmt,
        )
        return results

    def _execute_script(self, script_obj):
        script = script_obj["query"]
        if self.interactive:
            colored_script = pygments.highlight(
                script,
                lexer=find_lexer_class_by_name("sql")(),
                formatter=find_formatter_class("terminal256")(),
            )
            print(f"Executing script [{script_obj['name']}]: \n{colored_script}")
            if input("Execute Script? (y/n): ").lower() != "y":
                logger.critical("Aborting....")
                return

        results = self.db_con.execute_script(
            script,
        )
        print("*" * 100)
        return results

    def _execute_initial_setup(self):
        self._execute_script(self.initial_setup)

    def _execute_migrations(self):
        for migration in self.migrations:
            name = migration["name"]

            if not self.migration_exist(name):
                # self.add_migration(name)

                try:
                    logger.info(f"Executing migration: {name}")
                    self._execute_script(migration)
                    self.add_migration(name)
                except Exception as e:
                    logger.error(f"Failed to execute migration: {name}. Reason: `{e}`")
                continue

            logger.info(f"Migration Exists: {name}")

    def _execute_etl_objects(self):
        # print(self.etl_objects)
        db_objects_dict = {
            v["name"]: {"query": v["query"], "name": v["name"]}
            for v in self.etl_objects
        }

        resolver = DBObjectResolver(db_objects_dict)

        execution_order = resolver.get_execution_order()
        for etl_object in execution_order:
            try:
                query = db_objects_dict[etl_object]
                logger.info(f"Refreshing ETL Object: {etl_object}")
                self._execute_script(query)
            except Exception as e:
                logger.error(
                    f"Failed to execute migration: {etl_object}. Reason: `{e}`"
                )
