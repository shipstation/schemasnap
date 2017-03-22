# SchemaSnap

This project specifies a YAML-based format for documenting schemas. It aims to
be:

- easily generated and updated (e.g. new columns) by software,
- easily read and updated (e.g. descriptions) by humans, and
- easily read by additional software to generate any number of nicer looking
  docs, such as Confluence pages, a Git Book, and so on.

To get started, follow the next sections for configuring servers, installing the
software, and tips on running it.

## Configure servers

Make a `~/.schemasnap-config.yaml` file that map server nicknames to SQLAlchemy
connection strings, e.g.:

	servers:
	  server1:
	    url: 'mssql+pymssql://user:pass@host:1433/database'
	  server2:
	    url: 'postgresql+psycopg2://user:pass@host:5439/database'

## Install from source (virtualenv)

This project has been developed and tested only on Python 3.

First, have Python 3 installed on your system, and create a virtualenv using it:

	virtualenv -p python3 venv
	. venv/bin/activate

Then install  
	
	pip install -e .

If you are on a Mac and wish to connect to a DB via PyMSSQL, you may need to
install a working patch, to be released as pymssql==2.2.0.dev0 per
https://github.com/pymssql/pymssql/issues/432#issuecomment-258181766 - this
allows use of FreeTDS 1.0 on OS X

	brew install freetds
	pip install git+https://github.com/pymssql/pymssql@3bc299936fe2d35196dd4c9ebc8a22777f0c97e6#egg=pymssql

## Run `db2yaml`

Activate the virtualenv if you're using it:

	. venv/bin/activate

Run the command:

	db2yaml [--update-only] <server_name> <yaml_output_directory>

e.g.

	db2yaml server1 ~/myschemas/server1
	db2yaml server2 ~/myschemas/server2

to sync each server to it's own directory.

## Run `db2yaml`: advanced case

A more advanced example of the above is to make use of the `--update-only`
(`-u`) flag:

	db2yaml server_with_cols ~/myschemas/app
	db2yaml -u server_with_fks ~/myschemas/app

The above points two servers to the same output directory:

- `server_with_cols` will write the initial tables & columns out.
- `server_with_fks` will update (`-u`) existing tables & columns:

	- Case sensitive names will be kept from the server that has them.
	- Foreign keys will be used from the server that has them.
	- Data type inconsistencies will be resolved by using the last server synced with.

An example use case of the above is to combine metadata from servers with
otherwise same schema, but slightly different metadata, such as a data warehouse
with a subset of the tables and columns pulled from a SQL Server instance with
better names (`TitleCaseName` vs `titlecasename`), better data types (`time` vs
`string`, e.g.), foreign key metadata (to auto generate better docs), and so on.

## Run `excel2yaml`

Excel to yaml is a sister script of db2yaml, only it takes data from excel to populate
the yaml rather than a database. Given that this is a less common operation for our
use-case, excel2yaml has only a subset of the functionality of db2yaml, and relies
entirely on command line argument instead of configurations.

The set up relies on the exact same environment as db2yaml, so if you need to set up
your environment checkout that section above. The command is run with the following
syntax:

	excel2yaml <syaml_path> <table_col_name> <field_col_name> <descr_col_name>
		<path_to_excel_file> --update-only

These arguments are defined by the following:

- `yaml_path` path to the existing YAML files that are to be updated
- `table_col_name` is the name of the column in the excel sheets where the tool should look for the table name
- `field_col_name` is the name of the column in the excel sheets where the tool should look for the field name
- `descr_col_name` is the name of the column in the excel sheets where the tool should look for the field description
- `path_to_excel_file` is a path to the input excel file
- `--update-only` is currently a non-optional flag. This is because this tool was designed to only update existing yaml for now.
