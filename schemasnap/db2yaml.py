import collections
import logging
import os

import schemasnap.yaml_roundtrippable as yaml


logger = logging.getLogger(__name__)

# Map .table.yaml `type` to groups of SQLalchemy __visit_name__ values to
# replace. This serves to consolidate types that are roughly the same for the
# purposes of documentation such as boolean/bit flags, string types, and more.
# For example, we'll write down `string` instead of `VARCHAR(50) COLLATE
# "SQL_Latin1_General_CP1_CI_AS"`
TYPE_GROUPS = {
    # Boolean types
    'boolean': ('boolean', 'bit',),

    # Number types
    'float': ('float', 'real'),
    'integer': ('big_integer', 'bigint', 'integer', 'small_integer', 'smallint', 'tinyint',),
    'numeric': ('decimal', 'numeric',),

    # String types
    'string': ('char', 'clob', 'nchar', 'ntext', 'nvarchar', 'string', 'text', 'unicode', 'unicode_text', 'varchar',
               'uniqueidentifier',),

    # Temporal types
    'date': ('date',),
    'time': ('time',),
    'timestamp': ('datetime', 'datetime2', 'timestamp',),

    # Other types
    'array': ('array',),
    'binary': ('binary', 'blob', 'large_binary', 'varbinary',),
    'enum': ('enum',),
    'json': ('json',),
}


class DuplicateFieldException(Exception):
    pass


def sync_schema_to_disk(inspector, schema, output_directory, update_only=False):
    """Reflect all tables in specified schema into physical .table.yaml files.

    Format of the files will be:

      name: TableName
      description: TODO
      primary_key:
        - ColumnName
      columns:
        - name: ColumnName
          type: A simplified type for documentation purposes only
          description: TODO or "References Table.Field" if FK detected

          # Someday/maybe?
          created_at: when column was first noticed
          deleted_at: when column was last noticed (removed / renamed, maybe?)
          dialect_info:
            <dialect>:
              type: The dialect specific type
              default: The dialect specific default value
              nullable: The dialect specific nullability
              autoincrement: The value that comes back from sqlalchemy type?
              sequence: The dict that comes back from sqlalchemy type (sometimes)?

    :Parameters:
      `inspector`
        A sqlalchemy inspector instance.
      `schema`
        The schema name to reflect. If `None` is given, the default schema will be
        used such as `public` or `dbo` depending on the dialect.
      `output_directory`
        Where to write `*.table.yaml` files. One file per table will be created.
      `update_only`
        If enabled, only existing tables & column metadata will be modified.
    """
    for cased_table_name in inspector.get_table_names(schema=schema):
        table_name = cased_table_name.lower()

        # Load existing .table.yaml if it exists so we can update it
        yaml_path = os.path.join(output_directory, table_name + '.table.yaml')
        if os.path.exists(yaml_path):
            existing_str = open(yaml_path).read()
            existing_table = yaml.load(existing_str)
        elif update_only:
            logger.info('Skipping %s because update_only is enabled', cased_table_name)
            continue
        else:
            existing_str = None
            existing_table = yaml.load_empty()

        # Sync table attributes
        if 'name' not in existing_table or cased_table_name != table_name:
            existing_table['name'] = cased_table_name
        if 'description' not in existing_table:
            existing_table['description'] = 'TODO'
        if not existing_table.get('primary_key'):
            existing_table['primary_key'] = inspector.get_pk_constraint(
                cased_table_name, schema=schema)['constrained_columns']
        if 'columns' not in existing_table:
            existing_table['columns'] = []

        # Use foreign key data to generate column docs, so maintainers don't have
        # to document a field multiple times (just once in the table that it
        # appears as a primary/unique key in.)
        fks = inspector.get_foreign_keys(cased_table_name, schema=schema)
        fks_by_col = collections.defaultdict(list)
        for fk in fks:
            for i, cased_col_name in enumerate(fk['constrained_columns']):
                fks_by_col[cased_col_name.lower()].append('{}.{}'.format(
                    # TODO: do something with referred_schema if not None?
                    fk['referred_table'],
                    fk['referred_columns'][i],
                ))

        # Build a map {lower name => column} of columns.
        existing_col_map = collections.OrderedDict()
        for c in existing_table['columns']:
            col_name = c['name'].lower()
            if col_name in existing_col_map:
                raise DuplicateFieldException('{}.{} is defined twice'.format(cased_table_name, col_name))
            existing_col_map[col_name] = c

        # Sync columns
        for col in inspector.get_columns(cased_table_name, schema=schema):
            col_name = col['name'].lower()
            cased_col_name = col['name']
            existing_col = existing_col_map.get(col_name, yaml.load_empty())

            if 'name' not in existing_col or cased_col_name != col_name:
                existing_col['name'] = cased_col_name
            existing_col['type'] = simplify_type(col['type'])
            if 'description' not in existing_col:
                existing_col['description'] = 'TODO'
            if existing_col['description'] == 'TODO' and col_name in fks_by_col:
                existing_col['description'] = 'References ' + ', '.join(fks_by_col[col_name]) + '.'

            if col_name not in existing_col_map:
                if update_only:
                    logger.info('Skipping %s.%s because update_only is enabled', cased_table_name, cased_col_name)
                else:
                    existing_table['columns'].append(existing_col)

        # Save updates
        new_str = yaml.dump(existing_table)
        if new_str != existing_str:
            if os.path.exists(yaml_path):
                logger.info('Updating %s from %s', yaml_path, cased_table_name)
            else:
                logger.info('Creating %s from %s', yaml_path, cased_table_name)
                ensure_dir_exists(os.path.dirname(yaml_path))
            with open(yaml_path, 'w') as f:
                f.write(new_str)
        else:
            logger.info('No changes to %s from %s', yaml_path, cased_table_name)


def simplify_type(sa_type):
    visit_name = sa_type.__visit_name__.lower()
    for simple_name, visit_names in TYPE_GROUPS.items():
        if visit_name in visit_names:
            return simple_name
    return visit_name


def ensure_dir_exists(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
