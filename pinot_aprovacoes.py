from dash import html, dcc
from dash.dependencies import Input, Output, State

from pinot_crud import PinotSchemasCrud, PinotTablesCrud
from pinot_utils.src.integrations.gitlab_integration import GitlabIntegration

schemas_crud = PinotSchemasCrud()
tables_crud = PinotTablesCrud()
gitlab_integration = GitlabIntegration()

def render_page(schemas, tables):
    table_children = []
    for schema in schemas:
        row = html.Tr([
            html.Th(schema.id, className="border_style_tables"),
            html.Td(schema.schema_name, className="border_style_tables"),
            html.Td(schema.type_created, className="border_style_tables"),
            html.Td(schema.type_table, className="border_style_tables"),
            html.Td(schema.created_by, className="border_style_tables"),
            html.Td(schema.created_at, className="border_style_tables"),
            html.Td(dbc.ButtonGroup([
                dbc.Button("Detalhes", id={"type": "table-button", "index": f"schema_{schema.id}"},
                           color="info", className="me-1"),
                dbc.Button("Aprovar", id={"type": "approve-button", "index": f"schema_{schema.id}"},
                           color="success", className="me-1", disabled=False)
            ], size="sm", className="d-flex justify-content-between"), className="border_style_tables")
        ])
        table_children.append(row)

    for table in tables:
        row = html.Tr([
            html.Th(table.id, className="border_style_tables"),
            html.Td(table.table_name, className="border_style_tables"),
            html.Td(table.type_created, className="border_style_tables"),
            html.Td(table.type_table, className="border_style_tables"),
            html.Td(table.created_by, className="border_style_tables"),
            html.Td(table.created_at, className="border_style_tables"),
            html.Td(dbc.ButtonGroup([
                dbc.Button("Detalhes", id={"type": "table-button", "index": f"table_{table.id}"},
                           color="info", className="me-1"),
                dbc.Button("Aprovar", id={"type": "approve-button", "index": f"table_{table.id}"},
                           color="success", className="me-1", disabled=False)
            ], size="sm", className="d-flex justify-content-between"), className="border_style_tables")
        ])
        table_children.append(row)

    return html.Div([
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Id", className="border_style_tables"),
                html.Th("Tipo", className="border_style_tables"),
                html.Th("Nome", className="border_style_tables"),
                html.Th("Cadastro", className="border_style_tables"),
                html.Th("Tipo do Objeto", className="border_style_tables"),
                html.Th("Criado Por", className="border_style_tables"),
                html.Th("Criado Em", className="border_style_tables"),
                html.Th("Ações", className="border_style_tables")
            ])),
            html.Tbody(table_children, striped=True, bordered=True, hover=True, className="table-responsive")
        ])
    ])

layout = html.Div(
    className="content",
    children=[
        html.H1(children="Pinot - Aprovações", className="my-4"),
        html.Div(id="admin_pinot_aproves_page"),
        dcc.Location(id="admin_pinot_url_approve_object", refresh=True),
        dbc.Button("Refresh", id="admin_pinot_refresh_aproves", color="primary", className="my-2"),
        html.Div(dbc.Modal(
            children=[
                dbc.ModalHeader(dbc.ModalTitle("Criação da Tabela no Apache Pinot")),
                dbc.ModalBody("A tabela está sendo criada no Apache Pinot. Este processo pode levar alguns minutos."),
                dbc.ModalFooter(dbc.Button("Fechar", id="close_pinot_modal", className="ml-auto")),
            ],
            id="pinot-modal",
            is_open=False,
            style={"position": "relative", "zIndex": 1050}
        )),
        dcc.Store(id="modal-store", data={"is_open": False})
    ])

@app.callback(
    Output("admin_pinot_aproves_page", "children"),
    [Input("admin_pinot_refresh_aproves", "n_clicks")],
    prevent_initial_call=True
)
def refresh_approvals(n_clicks):
    schemas = schemas_crud.select()
    tables = tables_crud.select()
    return render_page(schemas, tables)

@app.callback(
    Output("pinot-modal", "is_open"),
    Output("modal-store", "data"),
    [Input({"type": "approve-button", "index": ALL}, "n_clicks"),
     Input("close_pinot_modal", "n_clicks")],
    [State("pinot-modal", "is_open"),
     State("modal-store", "data")],
    prevent_initial_call=True
)
def toggle_modal(n1, n2, is_open, modal_data):
    ctx = dash.callback_context
    triggered_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
    if "approve-button" in triggered_id:
        # Aprovar o schema ou a tabela usando a integração com GitLab
        if "schema" in triggered_id["index"]:
            schema_id = triggered_id["index"].replace("schema_", "")
            gitlab_integration.create_merge_request(f"Aprovar Schema {schema_id}")
        elif "table" in triggered_id["index"]:
            table_id = triggered_id["index"].replace("table_", "")
            gitlab_integration.create_merge_request(f"Aprovar Tabela {table_id}")
        modal_data["is_open"] = True
        return True, modal_data

    if n2:
        modal_data["is_open"] = False
        return False, modal_data

    return modal_data["is_open"], modal_data
