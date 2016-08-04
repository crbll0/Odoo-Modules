{
'name':'ADR Automatizaciones',
'version': '1.0',
'author':'OBS',
'category':'Updates',
'description': """Agrega varias Acciones:
1-Accion para todos los empleado para asignarles la tarifa de empleado.
2- Accion para todos los estudiantes para agregarle el plazo de pago y cuanta a cobrar""",
'depends':['base', 'account', 'npg_account_make_deposit'],
'data':['acciones.xml',
        'sequence.xml',
        'ext_view_deposit.xml',
        'ext_bank_statement.xml',
        'product_product_form_ext.xml'],
'installable':True,
'active': True,
}

