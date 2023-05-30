[![CI](https://github.com/duysqubix/cloudforge/actions/workflows/main.yml/badge.svg)](https://github.com/duysqubix/cloudforge/actions/workflows/main.yml)

# Cloud Forge 
Manage Azure by providing tools to validate and deploy
infrastructure



## General Use

Pull in docker image from qubix repositories.

`docker pull qubixds/cloudforge:latest` or the appropriate tag

You can test everything works by.. 

`docker run --rm qubixds/cloudforge:latest version` 


Now you can run your commands. Here are some samples.

To manage cloudtf files you need to supply a env file

```bash
docker run --rm -e ARM_VARS_USE_EXISTING=1 --env-file .env.dev -v $PWD:/cli/.tftest qubixds/cloudforge:dev -v tf validate dev -d .tftest/
``
<hr>

## Working with Synapse 

There are useful utilities that allow you to manage Azure Synapse Analytics Workspaces


### SQL Deployments 

Cloud Forge uses a repeatable design pattern that utilizes the built-in Synapse workspaces, providing the ability to manage database schemas and deploy them across multiple environments.

To use:
```bash
Usage: cf az syn deploysql [OPTIONS]

  Deploy SQL scripts to dedicated SQL pool

Options:
  -t, --target-dir TEXT    Target directory where synapse sql scripts are
                           stored  [required]
  -d, --database-uri TEXT  Name of dedicated SQL pool in a
                           workspace://database format  [required]
  -u, --username TEXT      Username to access database  [required]
  -p, --password TEXT      Password to access database  [required]
  --db-option TEXT         Additional DB options
  --help                   Show this message and exit.
```

Example:
```bash 
LOG_LEVEL=info cf az syn deploysql \
    -t synapse_workspace/sqlscript \ 
    -d main-synapse-workspace-dev://maindb \ 
    -u my-sql-username \
    -p my-strong-password \
    --db-option TrustServerCertificate=no \ 
    --db-option Encrypt=no
```

The previous example will look for the native JSON-style `sqlscript` folder that Synapse stores in a repository, it will attempt to connect to the synapse workspace name: `main-synapse-workspace-dev` and execute on the `maindb` database. It will use `-u` and `-p` SQL authentication to connect via ODBC. You can pass extra arguments to the ODBC driver using `--db-option` flags, these will take presedence over the defaults. 

<hr>

Cloud Forge expects two folders to exist in a Synapse Workspace in the SQL Scripts:

* etl_objects
* migrations 

Each folder serves a specific purpose.

#### **migrations**

Scripts in this folder should be prepended with a file naming system that allows for sequential sorting. You can choose the naming convention, but simply numbering them works well (e.g.., `0001_My_Script1`, `0002_My_Script2`, ...).

The migrations folder is intended for scripts that manage the underlying database schema.

When a deployment is initiated, Cloud Forge will sort and execute each script individually, first checking if the script has been executed before. This ensures that the exact same steps are taken in different development environments, and only new scripts are executed.

You can see a list of all migrations and their execution times in the `dbo.MigrationControl` table.

This pattern is similar to the Python web library Django's ORM management system. Each change to the database should be recorded in a new script that includes only definitions for creating or altering database objects, excluding views and stored procedures.


#### **etl_objects**

The `etl_objects` folder is intended for database objects that change more frequently than table definitions and would be cumbersome and confusing to track in migrations. Views and stored procedures are prime examples.

Instead, `etl_objects` serves as the single source of truth for all views and stored procedures. During every deployment, these objects are dropped and created again.

Cloud Forge supports a subset of SQL syntax for dependency management within this folder. For example, if you have two view definitions in two scripts where one view is built on the other, the first view must be created before the second.

```sql
-- file2.sql
\*
    DependsOn: [file1.sql]
*\
```

This tells Cloud Forge that `file1.sql` must be executed before `file2.sql`. You can list multiple dependencies by separating file names with commas: DependsOn: [`file2.sql`, `file3.sql`, `file4.sql`, ...].

Cloud Forge watches for circular dependencies, non-existent dependencies, and more.

The final two files would have the following content:

`file1.sql`
```sql
SET ANSI_NULLS ON
GO
q
SET QUOTED_IDENTIFIER ON
GO

CREATE VIEW [dbo].[Test1] AS 
SELECT 
*
FROM [dbo].[Employees]
GO
```

`file2.sql`
```sql
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

\* DependsOn: [file1.sql] *\

CREATE VIEW [dbo].[Test2] AS 
SELECT TOP 10
*
FROM [dbo].[Test1]
ORDER BY [RevenueGenerated] DESC
GO
```

