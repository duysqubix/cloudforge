import pytest

from unittest.mock import MagicMock

from . import MSSQL_MIGRATION_CONTROL_TABLE_NAME, DEFAULT_ODBC_MSSQL_DRIVER

from .mssql import (
    ODBCConnection,
    MSSQLConnection,
    SynapseAnalyticsConnection,
    Migration,
    ODBCValue,
    DBObject,
    DBObjectResolver,
)


def test_odbc_connection_init_invalid_uri():
    with pytest.raises(ValueError):
        ODBCConnection("invalid_uri", "username", "password")


def test_mssql_connection_create_conn_string():
    mssql_conn = MSSQLConnection("server://database", "username", "password")
    conn_string = mssql_conn.create_conn_string()
    expected_conn_string = (
        f"DRIVER={DEFAULT_ODBC_MSSQL_DRIVER};"
        "SERVER=tcp:server;"
        "PORT=1433;"
        "DATABASE=database;"
        "UID=username;"
        "PWD=password;"
        "CONNECTION TIMEOUT=30;"
    )
    assert conn_string == expected_conn_string


def test_synapse_analytics_connection_create_conn_string():
    synapse_conn = SynapseAnalyticsConnection(
        "server://database", "username", "password"
    )
    conn_string = synapse_conn.create_conn_string()
    expected_conn_string = (
        f"DRIVER={DEFAULT_ODBC_MSSQL_DRIVER};"
        "SERVER=tcp:server.sql.azuresynapse.net;"
        "PORT=1433;"
        "DATABASE=database;"
        "UID=username;"
        "PWD=password;"
        "CONNECTION TIMEOUT=30;"
        "ENCRYPT=yes;"
        "TRUSTSERVERCERTIFICATE=no;"
    )
    assert conn_string == expected_conn_string


def test_migration_exist():
    mock_db_con = MagicMock()
    mock_db_con.execute_script.return_value = [[[1]]]

    migration = Migration(
        db_con=mock_db_con, initial_setup={"query": ""}, etl_objects=[], migrations=[]
    )

    result = migration.migration_exist("test_migration")
    assert result is True
    mock_db_con.execute_script.assert_called_with(
        f"SELECT COUNT(1) FROM {MSSQL_MIGRATION_CONTROL_TABLE_NAME} WHERE ScriptName ='test_migration'",
    )


def test_add_migration():
    mock_db_con = MagicMock()

    migration = Migration(
        db_con=mock_db_con, initial_setup={"query": ""}, etl_objects=[], migrations=[]
    )

    migration.migration_exist = MagicMock(return_value=False)
    fixed_timestamp = "2023-05-23 13:41:26.000"
    migration.add_migration("test_migration", timestamp=fixed_timestamp)

    mock_db_con.execute_script.assert_called_with(
        f"INSERT INTO {MSSQL_MIGRATION_CONTROL_TABLE_NAME} (ScriptName, Applied) VALUES ('test_migration', '{fixed_timestamp}')",
    )


def test__execute_initial_setup():
    mock_db_con = MagicMock()

    migration = Migration(
        db_con=mock_db_con,
        initial_setup={"query": "initial_query"},
        etl_objects=[],
        migrations=[],
    )

    migration._execute_initial_setup()
    mock_db_con.execute_script.assert_called_with(
        "initial_query",
    )


def test__execute_migrations():
    mock_db_con = MagicMock()

    migrations = [
        {"name": "migration_1", "query": "migration_query_1"},
        {"name": "migration_2", "query": "migration_query_2"},
    ]

    migration = Migration(
        db_con=mock_db_con,
        initial_setup={"query": ""},
        etl_objects=[],
        migrations=migrations,
    )

    migration.migration_exist = MagicMock(side_effect=[False, True])
    migration.add_migration = MagicMock()

    migration._execute_migrations()

    mock_db_con.execute_script.assert_called_with("migration_query_1")
    migration.add_migration.assert_called_with("migration_1")


def test__execute_etl_objects():
    mock_db_con = MagicMock()

    etl_objects = [
        {"name": "etl_object_1", "query": "etl_query_1"},
        {"name": "etl_object_2", "query": "etl_query_2"},
    ]

    migration = Migration(
        db_con=mock_db_con,
        initial_setup={"query": ""},
        etl_objects=etl_objects,
        migrations=[],
    )

    migration._execute_etl_objects()

    calls = [((etl["query"],),) for etl in etl_objects]
    mock_db_con.execute_script.assert_has_calls(calls)


def test_non_sensitive_value():
    value = ODBCValue("non_sensitive")
    assert str(value) == "non_sensitive"
    assert repr(value) == "non_sensitive"
    assert value.get_raw_value() == "non_sensitive"


def test_sensitive_value():
    value = ODBCValue("sensitive", sensitive=True)
    assert str(value) == "****"
    assert repr(value) == "****"
    assert value.get_raw_value() == "sensitive"


def test_db_object_dependencies():
    content = "/* DependsOn: [file2.sql, file3.sql] */"
    db_object = DBObject("file1.sql", content)
    assert db_object.dependencies == ["file2.sql", "file3.sql"]


def test_db_object_no_dependencies():
    content = "SELECT * FROM users;"
    db_object = DBObject("file1.sql", content)
    assert db_object.dependencies == []


def test_db_object_resolver():
    db_objects_dict = {
        "file1.sql": "SELECT * FROM users; /* DependsOn: [file2.sql, file3.sql] */",
        "file2.sql": "CREATE TABLE users (id INT); /* DependsOn: [] */",
        "file3.sql": "ALTER TABLE users ADD name VARCHAR(255); /* DependsOn: [file2.sql] */",
    }

    resolver = DBObjectResolver(db_objects_dict)
    execution_order = resolver.get_execution_order()

    orders = {"file1.sql": 0, "file2.sql": 0, "file3.sql": 0}

    for idx, filename in enumerate(execution_order):
        orders[filename] = idx
    print(orders)
    assert orders["file2.sql"] < orders["file1.sql"]
    assert orders["file3.sql"] < orders["file1.sql"]
    assert orders["file2.sql"] < orders["file3.sql"]


def test_db_object_resolver_2():
    db_objects_dict = {
        "file1.sql": "SELECT * FROM users; /* DependsOn: [file2.sql, file3.sql] */",
        "file2.sql": "CREATE TABLE users (id INT); /* DependsOn: [] */",
        "file3.sql": "ALTER TABLE users ADD name VARCHAR(255); /* DependsOn: [file2.sql] */",
    }

    resolver = DBObjectResolver(db_objects_dict)
    execution_order = resolver.get_execution_order()
    assert execution_order == ["file2.sql", "file3.sql", "file1.sql"]


def test_db_object_resolver_circular_dependency():
    db_objects_dict = {
        "file1.sql": "SELECT * FROM users; /* DependsOn: [file2.sql] */",
        "file2.sql": "CREATE TABLE users (id INT); /* DependsOn: [file1.sql] */",
    }

    with pytest.raises(ValueError, match="Circular dependency detected"):
        resolver = DBObjectResolver(db_objects_dict)
        resolver.get_execution_order()


def test_db_object_resolver_non_existent_dependency():
    db_objects_dict = {
        "file1.sql": "SELECT * FROM users; /* DependsOn: [file2.sql] */",
        "file2.sql": "CREATE TABLE users (id INT); /* DependsOn: [file3.sql] */",
    }

    with pytest.raises(ValueError, match="Dependency file3.sql not found"):
        resolver = DBObjectResolver(db_objects_dict)
        resolver.get_execution_order()


def test_db_object_resolver_multiple_dependencies():
    db_objects_dict = {
        "file1.sql": "SELECT * FROM users; /* DependsOn: [file2.sql, file3.sql] */",
        "file2.sql": "CREATE TABLE users (id INT); /* DependsOn: [file5.sql] */",
        "file3.sql": "ALTER TABLE users ADD name VARCHAR(255); /* DependsOn: [file2.sql, file4.sql, file6.sql] */",
        "file4.sql": "SELECT * FROM orders; /* DependsOn: [file5.sql, file7.sql] */",
        "file5.sql": "CREATE TABLE orders (id INT); /* DependsOn: [] */",
        "file6.sql": "CREATE INDEX idx_users_id ON users(id); /* DependsOn: [file5.sql] */",
        "file7.sql": "ALTER TABLE orders ADD user_id INT; /* DependsOn: [] */",
    }

    resolver = DBObjectResolver(db_objects_dict)
    execution_order = resolver.get_execution_order()

    orders = {
        "file1.sql": 0,
        "file2.sql": 0,
        "file3.sql": 0,
        "file4.sql": 0,
        "file5.sql": 0,
        "file6.sql": 0,
        "file7.sql": 0,
    }

    for idx, filename in enumerate(execution_order):
        orders[filename] = idx

    # Check dependencies' order
    print(execution_order)

    assert orders["file5.sql"] < orders["file2.sql"]
    assert orders["file5.sql"] < orders["file6.sql"]

    assert orders["file2.sql"] < orders["file1.sql"]
    assert orders["file3.sql"] < orders["file1.sql"]

    assert orders["file2.sql"] < orders["file3.sql"]
    assert orders["file4.sql"] < orders["file3.sql"]
    assert orders["file6.sql"] < orders["file3.sql"]

    assert orders["file5.sql"] < orders["file4.sql"]
    assert orders["file7.sql"] < orders["file4.sql"]


def test_db_object_multiline_dependencies():
    content = """/*
DependsOn: [
    file2.sql,
    file3.sql,
    file4.sql
]
*/"""
    db_object = DBObject("file1.sql", content)
    expected_dependencies = ["file2.sql", "file3.sql", "file4.sql"]
    assert db_object.dependencies == expected_dependencies


def test_db_object_multiple_comment_blocks():
    content = """/*
Some other comment
*/

/* DependsOn: [file2.sql, file3.sql] */

/*
Another comment
*/"""
    db_object = DBObject("file1.sql", content)
    expected_dependencies = ["file2.sql", "file3.sql"]
    assert db_object.dependencies == expected_dependencies


def test_db_object_multiple_depends_on_blocks():
    content = """/*
DependsOn: [file2.sql]
*/

/*
DependsOn: [file3.sql]
*/"""

    with pytest.raises(ValueError, match="Multiple DependsOn statements found"):
        db_object = DBObject("file1.sql", content)


def test_db_object_resolver_nested_dependencies():
    db_objects_dict = {
        "file1.sql": "CREATE TABLE users (id INT); /* DependsOn: [] */",
        "file2.sql": "ALTER TABLE users ADD name VARCHAR(255); /* DependsOn: [file1.sql] */",
        "file3.sql": "SELECT * FROM users; /* DependsOn: [file1.sql, file2.sql] */",
    }

    resolver = DBObjectResolver(db_objects_dict)
    execution_order = resolver.get_execution_order()

    orders = {
        "file1.sql": 0,
        "file2.sql": 0,
        "file3.sql": 0,
    }

    for idx, filename in enumerate(execution_order):
        orders[filename] = idx

    # Check dependencies' order
    assert orders["file1.sql"] < orders["file2.sql"]
    assert orders["file1.sql"] < orders["file3.sql"]
    assert orders["file2.sql"] < orders["file3.sql"]
    
def test_db_object_resolver_nested_multiple_dependencies():
    db_objects_dict = {
        "file1.sql": "/* DependsOn: [] */",
        "file2.sql": "/* DependsOn: [] */",
        "file3.sql": "/* DependsOn: [file1.sql, file2.sql] */",
        "file4.sql": "/* DependsOn: [file1.sql, file2.sql] */",
        "file5.sql": "/* DependsOn: [file4.sql] */",
        "file6.sql": "/* DependsOn: [file3.sql, file5.sql] */",
    }

    resolver = DBObjectResolver(db_objects_dict)
    execution_order = resolver.get_execution_order()

    orders = {
        "file1.sql": 0,
        "file2.sql": 0,
        "file3.sql": 0,
        "file4.sql": 0,
        "file5.sql": 0,
        "file6.sql": 0,
    }

    for idx, filename in enumerate(execution_order):
        orders[filename] = idx

    # Check dependencies' order
    assert orders["file1.sql"] < orders["file3.sql"]
    assert orders["file2.sql"] < orders["file3.sql"]
    assert orders["file1.sql"] < orders["file4.sql"]
    assert orders["file2.sql"] < orders["file4.sql"]
    assert orders["file4.sql"] < orders["file5.sql"]
    assert orders["file3.sql"] < orders["file6.sql"]
    assert orders["file5.sql"] < orders["file6.sql"]

def test_db_object_resolver_circular_dependency_multiple_nested():
    db_objects_dict = {
        "file1.sql": "/* DependsOn: [] */",
        "file2.sql": "/* DependsOn: [file5.sql] */",
        "file3.sql": "/* DependsOn: [file1.sql, file2.sql] */",
        "file4.sql": "/* DependsOn: [file1.sql, file2.sql] */",
        "file5.sql": "/* DependsOn: [file4.sql] */",
        "file6.sql": "/* DependsOn: [file3.sql, file5.sql] */",
    }

    with pytest.raises(ValueError, match="Circular dependency detected"):
        resolver = DBObjectResolver(db_objects_dict)
        resolver.get_execution_order()

