{
'name':'Personnel Action',
'version': '1.0',
'author':'OBS',
'category':'Updates',
'description': """
A module that creates a personnel action for an employee that shows
 the current situation and requests changes if required.
""",
'images': [
        'images/OBSlogo.png', ],
'depends':['base','hr','hr_contract', 'hr_payroll'],
'data':[
    'sequence.xml',
    'hr_personnel_action_view.xml',
    'hr_personnel_action_workflow.xml',
    'hr_holiday_types.xml',
    'hr_holidays_extends_view.xml',
    'hr_holiday_calendar.xml',
    'hr_holidays_status_extends.xml',
    'dias_beneficios_view.xml',
    'product_template_extds.xml',
    'button_accion_personal.xml',
],
    'installable':True,
    'active': True,
}

