import sys

python_arg=sys.argv[1:len(sys.argv)]
schema=python_arg[0]
table=python_arg[1]
table_with_schema=schema+"."+table
table_name=schema+"."+table
app_name="dba-pg-tools"

