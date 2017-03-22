import collections
import os
import logging

import xlrd

import schemasnap.yaml_roundtrippable as yaml

"""
This script is designed to pull field descriptions stored in an excel
file and place them in the deisred yaml location. This assumes that
each tab of the excel workbook containing valid descriptions you want
has the a consistent header for table name, column name and description.
It also assumes that these headers are in the first row of each sheet.
"""

logger = logging.getLogger(__name__)


class DuplicateFieldException(Exception):
    pass


def read_workook(wbpath, tablecolname, fieldcolname, descrcolname):

    def makeAllLower(l):
        return [elem.value.lower() for elem in l]

    excel_descriptions = collections.defaultdict(lambda: [])
    wb = xlrd.open_workbook(wbpath)
    for sheet in wb.sheets():
        # test if sheet has valid headers
        colnames = makeAllLower(sheet.row(0))
        if tablecolname.lower() in colnames and fieldcolname.lower() in colnames and descrcolname.lower() in colnames:
            tableindex = colnames.index(tablecolname.lower())
            fieldindex = colnames.index(fieldcolname.lower())
            descrindex = colnames.index(descrcolname.lower())
            for r in range(1, sheet.nrows):  # start at 1 to skip headers
                if sheet.cell(r, descrindex).value.lower() != '':
                    excel_descriptions[sheet.cell(r, tableindex).value.lower()].append(
                        (sheet.cell(r, fieldindex).value.lower(), sheet.cell(r, descrindex).value)
                    )
        else:
            logger.info('Skipping %s because it does not have valid headers', sheet.name)

    return excel_descriptions


def update_yaml(output_directory, excel_data):
    for table_name in excel_data:
        yaml_path = os.path.join(output_directory, table_name + '.table.yaml')
        if os.path.exists(yaml_path):
            existing_str = open(yaml_path).read()
            existing_table = yaml.load(existing_str)
        else:
            logger.info('Skipping %s because %s.table.yaml file not found', table_name, table_name)
            continue

        if 'columns' not in existing_table:
            logger.info('Skipping %s because %s.table.yaml file has not attribute `columns`', table_name, table_name)
            continue
        else:
            # Build a map {lower name => column} of columns.
            existing_col_map = collections.OrderedDict()
            for c in existing_table['columns']:
                col_name = c['name'].lower()
                if col_name in existing_col_map:
                    raise DuplicateFieldException('{}.{} is defined twice'.format(table_name, col_name))
                existing_col_map[col_name] = c

            # Sync columns
            for col in excel_data[table_name]:
                col_name = col[0].lower()
                col_descr = col[1]
                existing_col = existing_col_map.get(col_name, yaml.load_empty())

                if 'description' not in existing_col or existing_col.get('description') == 'TODO':
                    existing_col['description'] = col_descr.strip()

            # Save updates
            new_str = yaml.dump(existing_table)
            if new_str != existing_str:
                if os.path.exists(yaml_path):
                    logger.info('Updating %s from %s', yaml_path, table_name)
                else:
                    raise Exception("File %s doesn't exist", yaml_path)
                with open(yaml_path, 'w') as f:
                    f.write(new_str)
            else:
                logger.info('No changes to %s from %s', yaml_path, table_name)


def main(xlfilepath, tablecolname, colcolname, desccolname, targetpath):
    xl = read_workook(xlfilepath, tablecolname, colcolname, desccolname)
    update_yaml(targetpath, xl)
