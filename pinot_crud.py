from pinot_utils.src.integrations import TableApi, SchemaApi

class PinotSchemasCrud:
    def __init__(self):
        self.schema_api = SchemaApi()

    def select(self, **kwargs):
        # Retorna todos os schemas disponíveis no Pinot
        schemas = self.schema_api.get_all_schemas()
        return [MockSchema(id=i, schema_name=schema['schemaName'], type_created='Manual', type_table='Event',
                           created_by='user123', created_at='2023-09-23 10:30') for i, schema in enumerate(schemas)]

class PinotTablesCrud:
    def __init__(self):
        self.table_api = TableApi()

    def select(self, **kwargs):
        # Retorna todas as tabelas disponíveis no Pinot
        tables = self.table_api.get_all_tables()
        return [MockTable(id=i, table_name=table['tableName'], type_created='Manual', type_table='Event',
                          created_by='user123', created_at='2023-09-23 10:30') for i, table in enumerate(tables)]
