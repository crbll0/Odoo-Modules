# -*- coding: utf-8 -*-
"""
@author: Ramon Caraballo Rojas.
"""
from dateutil import relativedelta
import datetime
import logging
import pdb

import openerp.addons.decimal_precision as dp
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval as eval
from openerp.osv import osv, fields

from workdays import workday

_logger = logging.getLogger(__name__)


class HrPersonnelAction(osv.osv):

    _name = 'hr.personnel.action'
    _description = "Hr Personnel Action"

    def calc_beneficios(self, cr, uid, ids, empl, fecha_termino, motivo=None,
                        fue_preavisado=True, tomo_vacaciones=True,
                        incluir_cesantia=False, incluir_salario_navidad=False,
                        contrat_id=None):

        contract_obj = self.pool.get('hr.contract')
        contrato_id = None

        if not motivo or (motivo == '1' and not contrat_id):
            return {'value': {
                              'vacations': False, 'days_forewarning': False,
                              'forewarning': False, 'months_worked': False,
                              'anios_trabajados': False, 'christmas_salary': False,
                              'days_worked': False, 'severance_days': False,
                              'severange_total': False, 'monthly_salary': 0.00,
                              'employee_benefits_total': False}}


        if empl:
            if contrat_id:
                contrato_id = contrat_id
            else:
                try:
                    contrato_id = contract_obj.search(cr, uid,
                                                      [('employee_id', '=', empl)],
                                                      order='date_start')
                except TypeError:
                    contrato_id = contract_obj.search(cr, uid,
                                                      [('employee_id', '=', empl)])
                except IndexError:
                    raise osv.except_osv(
                        'Error', 'El empleado debe contar con almenos un Contrato.'
                    )

        if contrato_id and fecha_termino:

            fecha_termino = self.str_to_datetime(cr, uid, ids, fecha_termino)

            temp_contrato = contrato_id if isinstance(contrato_id, int) else contrato_id[0]
            fecha_str = contract_obj.browse(cr, uid, temp_contrato).date_start
            fecha_inicio = self.str_to_datetime(cr, uid, ids, fecha_str)

            # Calcular los dia que tiene el mes de la fecha de termino.
            if fecha_termino.month in [1, 3, 5, 7, 8, 10, 12]:
                    dias_del_mes = 31
            else:
                if fecha_termino.month == 2:
                    # Si el anio es biciesto
                    dias_del_mes = 29 if fecha_termino.year % 4 == 0 else 28
                else:
                    dias_del_mes = 30

            anios = (fecha_termino - fecha_inicio).days / 365
            meses = (fecha_termino - fecha_inicio).days / dias_del_mes
            info_mes = abs(fecha_termino.month - fecha_inicio.month)
            dias = abs(fecha_termino.day - fecha_inicio.day)

            # diferencia = fecha_termino - fecha_inicio
            # print diferencia

            # La sumatorio de los salarios de todos los contratos.
            sueldo = 0
            for salario in contract_obj.browse(cr, uid, contrato_id):
                sueldo += salario.wage

            sueldo_diario = sueldo / 23.83

            # Pre-Aviso Art. 76 = La parte que omite el preaviso debe pagar
            # a la otra parte una indemnización equivalente a los siguientes días
            # dependiendo del tiempo trabajado en la empresa.
            # a.- Trabajo continuo no menor de 3 meses ni mayor de 6 meses = 7 días
            # b.- +6 meses y – 1 año = 14 días
            # c.- +1 año = 28 días
            dia_beneficio_id = 0
            try:
                dia_beneficio_id = self.pool.get('dias.beneficios').search(
                    cr, uid, [(1, '=', 1)])[0]
            except IndexError:
                pass
                # raise osv.except_osv('ERROR')

            dia_beneficio = self.pool.get('dias.beneficios').browse(cr, uid,
                                                                    dia_beneficio_id)
            # salario_min = dia_beneficio.salario_minimo

            preaviso_3 = dia_beneficio.preaviso_3 or 7
            preaviso_7 = dia_beneficio.preaviso_7 or 14
            preaviso_12 = dia_beneficio.preaviso_12 or 28

            dia_preaviso = 0
            if not fue_preavisado:
                if meses >= 3 and meses <= 6:
                    dia_preaviso = preaviso_3
                elif meses >= 7 and meses <= 11:
                    dia_preaviso = preaviso_7
                elif meses >= 12:
                    dia_preaviso = preaviso_12
                else:
                    dia_preaviso = 0

            monto_preaviso = dia_preaviso * sueldo_diario

            # Cesantía Art. 80= Cuando el empleador ejerce el desahucio
            # el empleado recibe un auxilio de cesantía,
            # aunque pase a trabajar a otra empresa.
            # a.-Trabajo continuo +3 meses y – de 6 = 6 días de salario ordinario
            # b.- +6 ni -1= 13 días
            # c.- +1 y -5= 21 días por cada año de servicio prestado

            # Si la consulta al modelo dia_beneficio en el campo de cesantia retorna
            # cero tomara el valor segundatio que se pasa con or.
            cesantia_3 = dia_beneficio.cesantia_3 or 6
            cesantia_7 = dia_beneficio.cesantia_7 or 13
            cesantia_12 = dia_beneficio.cesantia_12 or 21
            cesantia_5 = dia_beneficio.cesantia_5 or 23

            dia_cesantia = 0
            if incluir_cesantia:
                if meses >= 3 and meses <= 6:
                    dia_cesantia = cesantia_3

                elif meses >= 7 and meses <= 12:
                    dia_cesantia = cesantia_7

                elif meses > 12 and meses <= 71:
                    # temp = int(meses/12)
                    dia_cesantia = cesantia_12 * anios
                    dia_cesantia += 6 if info_mes >=3 else 13 if info_mes > 7 and info_mes < 12 else 0

                elif meses >= 72:  # Si es mayor a 5 Anios
                    dia_cesantia = cesantia_5 * anios
                    dia_cesantia += 6 if info_mes >=3 else 13 if info_mes > 7 and info_mes < 12 else 0

                else:
                    dia_cesantia = 0

            monto_cesantia = ((dia_cesantia * sueldo_diario) * 100) / 100
            # Vacaciones Art.177= Es el tiempo de descanso correspondiente
            # al trabajador por los meses o años trabajados.
            # Es obligatorio otorgarlo la empresa a sus empleados.
            # a.- +1 año y -5 años = 14 días de salario ordinario
            # b.- +5 años = 18 días

            # Cantidad de dias correspondiente dependiendo la cantidad total de meses
            # que tenga el empleado, si este lleva menos de un anio trabajando.
            dia_vacaviones = 0
            tomo_vacaciones = False if fecha_termino.month == 12 else tomo_vacaciones
            if not tomo_vacaciones:
                dia_vacaciones_meses = {5: 6,
                                        6: 7,
                                        7: 8,
                                        8: 9,
                                        9: 10,
                                        10: 11,
                                        11: 12, }
                if anios:
                    dia_vacaviones = 14 if anios < 5 else 16 if anios < 10 else 18

                else:
                    if meses >= 5:
                        dia_vacaviones = dia_vacaciones_meses[meses]
                    else:
                        dia_vacaviones = 0

            monto_vacaciones = dia_vacaviones * sueldo_diario

            # Navidad Art. 219= Se divide lo devengado mensual por 12 (meses).
            # Si no se han trabajado los doce meses del año se saca el promedio.
            # Si se trabajaron los doce meses el salario de navidad
            # será el equivalente al mensual.

            # El art.219 del código de trabajo establece que la suma a pagar
            # por el empleador no debe exceder del monto de cinco salarios mínimos
            # de ley. Por tanto, el empleado que gane un salario mensual que
            # sobrepase los cinco salarios mínimos de ley, sólo recibirá
            # por concepto de salario de Navidad la suma equivalente a cinco
            # salarios mínimos de ley (Art.219).

            monto_navidad = 0
            if incluir_salario_navidad:

                # monto_navidad = (((fecha_termino.month - 1) * sueldo) +
                #                  ((fecha_termino.day * 23.83) / dias_del_mes) *
                #                  sueldo_diario) / 12

                monto_navidad = ((info_mes * sueldo) +
                                 (((dias + 1) * 23.83) / dias_del_mes) *
                                 sueldo_diario) / 12

                # if salario_min and salario_min > 7000:
                #     monto_navidad_max = salario_min * 5
                #
                #     if monto_navidad > monto_navidad_max:
                #         monto_navidad = monto_navidad_max

            total_beneficio = monto_navidad + monto_preaviso + \
                              monto_cesantia + monto_vacaciones

            values = {'value': {'average_daily_salary': sueldo_diario,
                                'vacations_days': dia_vacaviones,
                                'vacations': monto_vacaciones,
                                'days_forewarning': dia_preaviso,
                                'forewarning': monto_preaviso,
                                'months_worked': info_mes,
                                'anios_trabajados': anios,
                                'christmas_salary': monto_navidad,
                                'days_worked': dias,
                                'severance_days': dia_cesantia,
                                'severange_total': monto_cesantia,
                                'employee_benefits_total': total_beneficio,
                                'monthly_salary': sueldo,}
                      }

            return values

    def calc_actual_total(self, cr, uid, ids, field_name, args, context=None):
        # Calculates the sum of the wage and the diff_scale

        #Returns: Dictionary{id: value}

        result = {}
        for record in self.browse(cr, uid, ids, context=None):
            result[record.id] = record.actual_diff_scale + record.actual_wage
        return result

    def calc_proposed_total(self, cr, uid, ids, field_name, args, context=None):
        # Calculates the sum of the wage and the diff_scale

        # Returns: Dictionary{id: value}
        result = {}
        records = self.browse(cr, uid, ids, context=None)
        for record in records:
            result[record.id] = (record.proposed_wage +
                                 record.proposed_diff_scale)
        return result

    def calc_employee_leave_total(self, cr, uid, ids, field_name, args,
                                  context=None):
        # Calculates the sum of the 3 fields of employee benefits.

        # Returns Dictionary{id: value}
        result = {}
        records = self.browse(cr, uid, ids, context=None)
        for record in records:
            result[record.id] = (record.severance + record.forewarning +
                                 record.christmas_salary)
        return result

    def calc_number_of_days(self, cr, uid, ids, from_date, to_date,
                            from_view=False, context=None):
        # Calculates the time beetwen two dates.

        # Arguments:
        # from_date -- start date, type string
        # to_date -- end date, type string

        # Returns: integer

        if from_date and to_date:
            to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
            from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            to_date = datetime.date(to_date.year, to_date.month, to_date.day)
            from_date = datetime.date(from_date.year, from_date.month,
                                      from_date.day)
            days = to_date - from_date
            num_of_days = str(days)[:-13]

            if from_view:
                # Si se esta llamando desde la vista.
                return {'value':
                            {'days_of_vacations': int(num_of_days)}
                        }

            return int(num_of_days)

    def verificar_fechas(self, cr, uid, ids, fecha_actual, fecha_prop):

        """ Para Saber si fecha_prop es mayor que fecha_actual

        EL uso Principal de esta funcion es saber si la fecha
        de fin de contrato (date_end) es menor a la nueva fecha
        de fin de contrato que se le asignara fecha_propuesta..

        : param fecha_actual: '1/1/2016'
        : type fecha_actual: str
        : param fecha_prop: '1/2/2016'
        : type fecha_prop: str

        """

        f_actual = self.str_to_datetime(cr, uid, ids, fecha_actual)

        f_propuesta = self.str_to_datetime(cr, uid, ids, fecha_prop)

        return f_propuesta > f_actual

    def get_actions_ids(self, cr, uid, context=None):
        actions_ids = self.search(cr, uid, [('stage', '=', 'listo')],
                                  context=None)
        return actions_ids

    def all_empleados(self, cr, uid, ids, context=None):
        """
         Retorna solo los empleados del departamento
         y sub departamento del usuario quien hace
         la peticion.
        """
        hr_empl = self.pool.get('hr.employee')
        manager = hr_empl.browse(cr, uid, uid)
        empl_depart_id = manager.department_id.id
        hr_depart = self.pool.get('hr.department')

        # Buscar los departamentos que tenga como ID padre
        # el id que viene de la variable empl_depart_id
        depart_hijos = hr_depart.search(cr, uid,
                [('parent_id', '=', empl_depart_id)]
        )

        lista = []
        for dep in depart_hijos:
            temp = hr_depart.search(cr, uid, [('parent_id', '=', dep)])

            if temp:
                lista.append(temp)

        depart_nietos = [n for sublista in lista for n in sublista]

        all_depart = depart_hijos + depart_nietos

        empleados = hr_obj.search(cr, uid, [
            ('department_id', '=', empl_depart_id)]
        )
        empleados += hr_obj.search(cr, uid, [
            ('department_id', 'in', all_depart)]
        )

        return [('department_id', '=', empl_depart_id),
                ('department_id', 'in', all_depart)]

    def run_personnel_actions(self, cr, uid, ids=None, context=None):

        """
        Runs a determined action on the date set in the field effective_date.
        Returns None"""

        # If the code is called from the form,
        # ids is the id of the record active.
        # If is called from the cron job,
        # this function get all records ids.
        if not ids:
            ids = self.get_actions_ids(cr, uid, context=None)

        # This variables holds the objects
        # we are going to be using in each action.
        hr_obj = self.pool.get('hr.employee')
        hr_cont_obj = self.pool.get('hr.contract')
        # hr_holiday = self.pool.get('hr.holidays')
        # hr_pay_obj = self.pool.get('hr.payslip')
        # hr_payslip_obj = self.pool.get('hr.payslip.input')

        # List with all the records for the object hr.personnel.action
        # Object that access all the records.
        # actions_ids is the list with all my ids.
        actions = self.browse(cr, uid, ids, context=None)

        # Loop for traversing all records in the hr.personnel.action table
        # and if the status is for approved and the date is today, run them.
        for action in actions:

            # This converts the date of the record
            #  to a format that can be evaluated.
            effective_date = self.str_to_datetime(cr, uid, ids,
                                                  action.effective_date)

            # If the record is set up to be applied today is applied.

            if effective_date <= datetime.date.today():

                # Opciones de Designacion. ##############################
                if action.action_requested == 'designacion':

                    """
                    Tipos de contratos por ID:
                    type_id: 1 = es el contrato fijo
                    type_id: 2 = es el contrato temporero
                    type_id: 3 = es el contrato pensionado
                    """

                    # Extencion de Contrato y  Extencion de Nombramiento

                    if action.action_designation_requested in ['1', '2']:

                        hr_cont_obj.write(
                            cr, uid, action.contract_id.id,
                            {'date_end': action.proposed_end_new_contract})

                        self.state_done(cr, uid, ids)

                    # Inicio de Pension
                    elif action.action_designation_requested == '3':
                        # SI el contrato del seleccionado es TIPO FIJO.
                        if int(action.contract_id.type_id) == 1:

                            hr_cont_obj.write(cr, uid, action.contract_id.id,
                                              {'type_id': 3})

                        self.state_done(cr, uid, ids)

                    # Nombramiento Fijo
                    elif action.action_designation_requested == '4':

                        hr_cont_obj.write(cr, uid, action.contract_id.id, {
                            'type_id': 1,
                            'wage': action.proposed_wage,
                            'struct_id': action.proposed_salary.id,
                            'date_start': action.effective_date,
                            'company_id': action.proposed_company_id.id,
                            'date_end': action.proposed_end_new_contract,
                            'working_hours': action.proposed_orderly_turn.id,
                            'job_id': action.proposed_ocupation.id, }
                        )

                        self.state_done(cr, uid, ids)

                    # Nombramiento Interino
                    elif action.action_designation_requested == '5':

                        hr_cont_obj.create(cr, uid, {
                            'employee_id': action.employee_id.id,
                            'type_id': 2,
                            'wage': action.proposed_wage,
                            'struct_id': action.proposed_salary.id,
                            'date_start': action.effective_date,
                            'date_end': action.proposed_end_new_contract,
                            'company_id': action.proposed_company_id.id,
                            'working_hours': action.proposed_orderly_turn.id,
                            'job_id': action.proposed_ocupation.id, }
                        )

                        self.state_done(cr, uid, ids)

                    # Nombramiento por Contrato
                    elif action.action_designation_requested == '6':

                        hr_cont_obj.create(cr, uid, {
                            'employee_id': action.employee_id.id,
                            'type_id': 2,
                            'wage': action.proposed_wage,
                            'struct_id': action.proposed_salary.id,
                            'date_start': action.effective_date,
                            'date_end': action.proposed_end_new_contract,
                            'company_id': action.proposed_company_id.id,
                            'notes': action.observations,
                            'job_id': action.proposed_ocupation.id,
                        })
                        self.state_done(cr, uid, ids)

                    # Nombramiento Probatorio
                    elif action.action_designation_requested == '7':

                        hr_cont_obj.create(cr, uid, {
                            'employee_id': action.employee_id.id,
                            'type_id': 2,
                            'wage': action.proposed_wage,
                            'struct_id': action.proposed_salary.id,
                            'date_start': action.effective_date,
                            'date_end': action.proposed_end_new_contract,
                            'company_id': action.proposed_company_id.id,
                            'working_hours': action.proposed_orderly_turn.id,
                            'job_id': action.proposed_ocupation.id, }
                        )

                        self.state_done(cr, uid, ids)

                    # Nombramiento Temporero
                    elif action.action_designation_requested == '8':

                        hr_cont_obj.create(cr, uid, {
                            'employee_id': action.employee_id.id,
                            'type_id': 2,
                            'wage': action.proposed_wage,
                            'struct_id': action.proposed_salary.id,
                            'date_start': action.effective_date,
                            'date_end': action.proposed_end_new_contract,
                            'company_id': action.proposed_company_id.id,
                            'working_hours': action.proposed_orderly_turn.id,
                            'job_id': action.proposed_ocupation.id, })

                        self.state_done(cr, uid, ids)
                    # Reingreso
                    elif action.action_designation_requested == '9':

                        hr_cont_obj.write(cr, uid, action.contract_id.id, {
                            'date_end': action.proposed_end_new_contract})

                        self.state_done(cr, uid, ids)
                    # Pasantia
                    elif action.action_designation_requested == '10':

                        hr_cont_obj.create(cr, uid, {
                            'employee_id': action.employee_id.id,
                            'type_id': 2,
                            'wage': action.proposed_wage,
                            'struct_id': action.proposed_salary.id,
                            'date_start': action.effective_date,
                            'date_end': action.proposed_end_new_contract,
                            'company_id': action.proposed_company_id.id,
                            'working_hours': action.proposed_orderly_turn.id, })

                        self.state_done(cr, uid, ids)
                    # VOluntarios
                    elif action.action_designation_requested == '11':
                        hr_cont_obj.create(cr, uid, {
                            'employee_id': action.employee_id.id,
                            'type_id': 2,
                            'wage': action.proposed_wage,
                            'struct_id': action.proposed_salary.id,
                            'date_start': action.effective_date,
                            'date_end': action.proposed_end_new_contract,
                            'company_id': action.proposed_company_id.id,
                            'working_hours': action.proposed_orderly_turn.id, })

                        self.state_done(cr, uid, ids)
                    # Entrenamiento
                    elif action.action_designation_requested == '12':
                        hr_cont_obj.create(cr, uid, {
                            'employee_id': action.employee_id.id,
                            'type_id': 2,
                            'wage': action.proposed_wage,
                            'struct_id': action.proposed_salary.id,
                            'date_start': action.effective_date,
                            'date_end': action.proposed_end_new_contract,
                            'company_id': action.proposed_company_id.id,
                            'working_hours': action.proposed_orderly_turn.id, }
                        )
                        self.state_done(cr, uid, ids)

                # Cambios ################################################
                elif action.action_requested == 'cambios':
                    # Promocion -- #12
                    if action.action_changes_requested == '1':
                        hr_obj.write(cr, uid, action.employee_id.id, {
                            'job_id': action.proposed_ocupation.id,
                            'salary_scale_category':
                                action.proposed_salary_scale_category,
                            'salary_scale_level': action.proposed_salary_scale_level,
                            'deparment_id': action.proposed_dependency.id,
                            'parent_id': action.proposed_parent_id.id, })

                        hr_cont_obj.write(cr, uid, ret['contract_id'][0], {
                            'working_hours': action.proposed_orderly_turn.id,
                            'wage': action.proposed_total, })

                        self.state_done(cr, uid, ids)
                    # Promocion y Transferencia -- # Probado
                    elif action.action_changes_requested == '2':
                        hr_obj.write(cr, uid, action.employee_id.id, {
                            'department_id': action.proposed_dependency.id,
                            'job_id': action.proposed_ocupation.id,
                            'salary_scale_category':
                                action.proposed_salary_scale_category,
                            'salary_scale_level': action.proposed_salary_scale_level,
                            'parent_id': action.proposed_parent_id.id,
                            'transfer_to': action.proposed_transfer.id, })

                        hr_cont_obj.write(cr, uid, ret['contract_id'][0], {
                            'working_hours': action.proposed_orderly_turn.id,
                            'wage': action.proposed_total})

                        self.state_done(cr, uid, ids)
                    # Reajuste de Sueldo -- # Probado
                    elif action.action_changes_requested == '3':
                        hr_obj.write(cr, uid, action.employee_id.id, {
                            'salary_scale_category':
                                action.proposed_salary_scale_category,
                            'salary_scale_level':
                                action.proposed_salary_scale_level, })

                        hr_cont_obj.write(cr, uid, ret['contract_id'][0], {
                            'wage': action.proposed_total,
                            'diff_scale': action.proposed_diff_scale, })

                        self.state_done(cr, uid, ids)
                    # Reclasificacion
                    elif action.action_changes_requested == '4':
                        hr_obj.write(cr, uid, action.employee_id.id, {
                            'department_id': action.proposed_dependency.id,
                            'job_id': action.proposed_ocupation.id,
                            # 'salary_scale_category': new_scale_categ,
                            # 'salary_scale_level': new_scale_level,
                            'parent_id': action.proposed_parent_id.id, })

                        hr_cont_obj.write(cr, uid, action.contract_id.id, {
                            'job_id': action.proposed_ocupation.id,
                            # 'analytic_account_id': res[0][0],
                            'working_hours': action.proposed_orderly_turn.id,
                            'wage':
                                action.proposed_wage + action.proposed_diff_scale})
                        self.state_done(cr, uid, ids)

                    # Transferencias -- # Probado
                    elif action.action_changes_requested == '5':

                        hr_obj.write(cr, uid, action.employee_id.id, {
                            'transfer_to': action.proposed_transfer.id})

                        self.state_done(cr, uid, ids)

                # Opciones de Salidas.#####################################
                elif action.action_requested == 'salidas':
                    contratos = hr_cont_obj.search(
                        cr, uid, [('employee_id', '=', action.employee_id.id)])

                    hr_cont_obj.write(cr, uid, contratos,
                                      {'date_end': action.effective_date})

                    hr_obj.write(cr, uid, action.employee_id.id,
                                 {'active': False})

                    user_id = self.pool.get('hr.employee').browse(
                        cr, uid, action.employee_id.id).resource_id.user_id.id

                    self.pool.get('res.users').write(cr, uid, user_id,
                                                     {'active': False})

                    self.state_done(cr, uid, ids)

                # Opciones de Vacaciones y Licencias. ###################
                elif action.action_requested == 'vacation_and_licenses':

                    # numero de la peticion de licencia.
                    num_peticion = action.action_others_requested
                    is_vac = True if num_peticion == '11' else False

                    if int(num_peticion) in range(1, 14):
                        cr.execute(
                            "SELECT date_to FROM hr_holidays \
                              WHERE employee_id IN ({0}) ORDER BY id \
                              DESC LIMIT 1".format(action.employee_id.id)
                        )
                        res = cr.fetchmany()

                        if res and not type(None):

                            # si la fecha de termino de la ultima
                            # licencia del usuario es menor a la fecha actual.
                            if self.verificar_fechas(
                                    cr, uid, ids, res[0][0][: 10],
                                    str(datetime.date.today())):

                                self.licencias(cr, uid, ids, action, is_vac)

                            # else:
                            #     raise osv.except_osv('Error',
                            #              'Este empleado cuenta \
                            #              con vacaciones y/o asignadas!')

                        # Si res esta vacio ejecuta la accion
                        else:
                            self.licencias(cr, uid, ids, action, is_vac)


    _columns = {
        'origin_employee_id': fields.many2one('hr.employee', 'Petitioner',
                                              required=True),
        'origin_department_id': fields.many2one('hr.department',
                                                'Departamento/Solicitante'),
        'origin_company_id': fields.many2one('res.company', 'Recinto'),
        'origin_address': fields.char('Address', size=128),
        'origin_state_id': fields.many2one('res.country.state', 'State'),
        'action_requested': fields.selection(
            (
                ('designacion', 'Designacion'),
                ('cambios', 'Cambios'),
                ('salidas', 'Salidas'),
                ('vacation_and_licenses', 'Vacaciones y Licencias')
            ), 'Tipo de Requerimiento', required=True
        ),

        'action_designation_requested': fields.selection(
            (
                ('1', 'Extencion de Contrato'),
                ('2', 'Extencion de Nombramiento'),
                ('3', 'Inicio de Pension'),
                ('4', 'Nombramiento Fijo'),
                ('5', 'Nombramiento Interino'),
                ('6', 'Nombramiento por Contrato'),
                ('7', 'Nombramiento Probatorio'),
                ('8', 'Nombramiento Temporero'),
                ('9', 'Reingreso'),
                ('10', 'Pasantia'),
                ('11', 'Voluntarios'),
                ('12', 'Entrenamiento')
            ), 'Designacion'
        ),

        'action_changes_requested': fields.selection(
            (
                ('1', 'Promocion'),
                ('2', 'Promocion y Transferencia'),
                ('3', 'Reajuste de Sueldo'),
                ('4', 'Reclasificacion'),
                ('5', 'Transferencia')
            ), 'Cambios'
        ),

        'action_out_requested': fields.selection(
            (
                ('1', 'Abandono de Cargo'),
                ('2', 'Desahucio'),
                ('3', 'Despido'),
                ('4', 'Dimision'),
                ('5', 'Fallecimiento'),
                ('6', 'Retiro por Pension'),
                ('7', 'Renuncia'),
                ('8', 'Rescision de Nombramiento'),
                ('9', 'Finalizacion de Pasantia'),
                ('10', 'Finalizacion de Voluntario'),
                ('11', 'Finalicacion de Entrenamiento')
            ), 'Salidas'
        ),

        'action_others_requested': fields.selection(
            (
                ('1', 'Asueto'),
                ('12', 'Ausencias justificadas'),
                ('14', 'Ausencias no justificadas'),
                ('2', 'Licencia por alumbramiento Conyuge'),
                ('3', 'Licencia por Enfermedad'),
                ('6', 'Licencia por Maternidad'),
                ('7', 'Licencia por Matrimonio'),
                ('13', 'Licencia por Estudios'),
                ('8', 'Licencia sin disfrute de sueldo'),
                ('4', 'Licencia por Fallecimiento de Familiar (Directo)'),
                ('5', 'Licencia por Fallecimiento de Familiar (Indirecto)'),
                ('10', 'Medio Dia de Cumpleaños'),
                ('9', 'Tardanza'),
                ('11', 'Vacaciones'),
            ), 'Vacaciones y Licencias'
        ),

        'referencia': fields.char('Referencia'),

        'effective_date': fields.date('Effective date', required=True),
        'employee_id': fields.many2one('hr.employee', 'Petitioned', required=True),
        'contract_id': fields.many2one('hr.contract', 'Contracts', default=0),
        'actual_employee_code': fields.char('Code', size=32, readonly=True),
        'actual_identification_id': fields.char('Identification No.', size=32,
                                                readonly=True),
        'actual_dependency': fields.many2one('hr.department',
                                             'Departamento/Empleado', readonly=True),
        'actual_ocupation': fields.many2one('hr.job', 'Ocupation', readonly=True),
        'actual_parent_id': fields.many2one('hr.employee', 'Inmediate Superior'),
        'actual_orderly_turn': fields.many2one('resource.calendar',
                                               'Actual work schedule'),
        'actual_salary_scale_category': fields.selection(
            (
                ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
                ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
                ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'),
                ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'),
                ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'),
                ('23', '23'), ('24', '24'), ('25', '25')
            ), 'Salary Scale Category'
        ),
        'actual_salary_scale_level': fields.selection(
            (
                ('1', '1'), ('2', '2'), ('3', '3'),
                ('4', '4'), ('5', '5'), ('6', '6')
            ), 'Salary Scale Level'
        ),
        'actual_wage': fields.float('Wage', digits=(16, 2)),
        'actual_diff_scale': fields.float('Diff. scale', digits=(16, 2)),
        'actual_total': fields.function(calc_actual_total,
                                        string='Actual Total', type='float'),
        'observations': fields.text('Observations'),
        'states': fields.selection(
            (
                ('draft', 'Creado'),
                ('confirmed', 'Confirmado'),
                ('approved', 'Aprobado por G.H'),
                ('aprobacion_de', 'Aprobado por D.E'),
                ('cancelled', 'Cancelado'),
                ('applied', 'Hecho')
            ), 'Status'),
        'stage': fields.selection(
            (
                ('draft', 'Esperando Confirmacion'),
                ('confirmed', 'Esperando Aprobacion de G.H'),
                ('confirmed2', 'Esperando Aprobacion de D.G.H'),
                ('approved', 'Esperando Aprobacion de D.E'),
                ('listo', 'Accion Lista para ser Ejecutada'),
                ('cancelled', 'La Accion ha sido Rechazada/Cancalada.'),
                ('applied', 'Accion Completada Satisfactoriamente.'),
            ), 'Stage',
        ),
        'start_leave': fields.date('Start licence'),
        'end_of_leave': fields.date('End of licence'),
        'days_of_vacations': fields.float('Cantidad de dias'),
        'proposed_dependency': fields.many2one('hr.department', 'Dependency'),
        'proposed_ocupation': fields.many2one('hr.job', 'Ocupation'),
        'proposed_parent_id': fields.many2one('hr.employee', 'Director'),
        'proposed_coach_id': fields.many2one('hr.employee', 'Coach'),
        'proposed_orderly_turn': fields.many2one('resource.calendar',
                                                 'Proposed work schedule'),
        'proposed_wage': fields.float('Wage', digits=(16, 2)),
        'proposed_salary_scale_category': fields.selection(
            (
                ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'),
                ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'),
                ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'),
                ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
                ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'),
                ('25', '25')
            ), 'Salary Scale Category'
        ),

        'proposed_salary_scale_level': fields.selection(
            (
                ('1', '1'), ('2', '2'),
                ('3', '3'), ('4', '4'),
                ('5', '5'), ('6', '6')
            ), 'Salary Scale Level'
        ),

        'proposed_diff_scale': fields.float('Diff. Scale', digits=(16, 2)),
        'proposed_total': fields.function(calc_proposed_total,
                                          string='Proposed Total',
                                          type='float'),
        'proposed_bonus': fields.float('Bonus', digits=(16, 2)),
        'proposed_end_new_contract': fields.date('End of contract'),
        'proposed_salary_cut': fields.float('Salary reduction', digits=(16, 2)),
        'proposed_misconduct': fields.text('Amonestacion'),
        'proposed_misconduct_level': fields.selection(
            (
                ('1', '1'), ('2', '2'), ('3', '3')
            ), 'Nivel falta cometida'
        ),
        'proposed_company_id': fields.many2one('res.company', 'Compania'),
        'proposed_salary': fields.many2one('hr.payroll.structure',
                                           'Estructura Salarial'),
        'date_start': fields.date('Duracion'),
        'proposed_transfer': fields.many2one('res.company',
                                             'Transferencia entre recintos'),
        'proposed_hours': fields.float('Horas'),

        'creado_por': fields.many2one('res.users', 'Creado por', readonly=True),
        'confirmado_por': fields.many2one('res.users', 'Confirmado por',
                                          readonly=True),
        'aprobadogh_por': fields.many2one('res.users', 'Aprobado G.H por',
                                          readonly=True),
        'aprobadode_por': fields.many2one('res.users', 'Aprobado D.E por',
                                          readonly=True),
        'cancelado_por': fields.many2one('res.users', 'Cancelado por',
                                         readonly=True),
        'aprobaciondgh_por' : fields.many2one('res.users', 'Aprobado D.G.H por',
                                              readonly=True),



        # From here on the fields are for information only regarding
        # salary compensation in case of employee leave.
        # This may change on another stage of the proyect.
        'days_severance': fields.integer('Days of severance', size=12),
        'severance': fields.float('Severance', digits=(16, 2)),
        'days_forewarning': fields.integer('Days of forewarning', size=12),
        'forewarning': fields.float('Forewarning', digits=(16, 2)),
        'months_worked': fields.integer('Months worked', size=12),
        'monthly_salary': fields.float('Monthly Salary', digits=(16, 2)),
        'christmas_salary': fields.float('Salario de navidad', digits=(16, 2)),
        'average_daily_salary': fields.float('Average daily salary', digits=(16, 2)),
        'vacations_days': fields.integer('Vacations days', size=12),
        'vacations': fields.float('Vacations', digits=(16, 2)),
        'employee_benefits_total': fields.function(calc_employee_leave_total,
                                                   string='Total Benefits',
                                                   type='float'),
        'severance_days': fields.integer('Dias de cesantia', size=12),
        'severange_total': fields.float('Monto cesantia', digits=(16, 2)),
        'days_worked': fields.integer('Dias trabajados', size=12),
        'anios_trabajados': fields.integer('Años Trabajados', size=2),
        'total_worked': fields.float('Monto dias trabajados', digits=(16, 2)),
        'peticion_ausencia': fields.many2one('hr.holidays',
                                             'Peticion de Ausencia'),

        'fue_preavisado': fields.boolean('Fue Preavisado?', defailt=True),
        'incluir_cesantia': fields.boolean('Incluir monto Cesantia', defailt=False),
        'tomo_vacaciones': fields.boolean('Tomo las Vacaciones?', defailt=True),
        'incluir_salario_navidad': fields.boolean('Incluir Salario Navidad',
                                                  defailt=False),

    }
    _defaults = {
        'states': 'draft',
        'stage': 'draft',
        'referencia': '',
        'origin_employee_id':
            lambda self, cr, uid, ids: self.logged_user(cr, uid, ids),

    }

    def licencias(self, cr, uid, ids, action, is_vac=False, context=None):
        hr_obj = self.pool.get('hr.employee')
        holiday_obj = self.pool.get('hr.holidays')

        holi_id = action.peticion_ausencia.id

        holiday_obj.write(cr, uid, holi_id, {'state': 'validate'})

        tipo = {'on_vacation': True} if is_vac else {'on_licence': True}

        hr_obj.write(cr, uid, action.employee_id.id, tipo)

        self.state_done(cr, uid, ids)

        return True

    def logged_user(self, cr, uid, ids, context=None):
        """
        Se encarga de buscar y retornar informacion
        del usuario logeado.
        """

        empl = self.pool.get('hr.employee')
        resource = self.pool.get('resource.resource')

        res = resource.search(cr, uid, [('user_id', '=', uid)], context=None)

        empleado_id = empl.search(cr, uid, [('resource_id', '=', res[0])],
                                  context=None)

        flag = self.pool.get('res.users').has_group(
            cr, uid, 'internal_requisition.internal_requisition_manager')

        return empleado_id[0] if flag else 3

    def get_contract(self, cr, uid, employee, context=None):
        contract_obj = self.pool.get('hr.contract')
        clause_final = [('employee_id', '=', employee.id)]
        contract_ids = contract_obj.search(cr, uid, clause_final)
        return contract_ids

    def onchange_petitioner(self, cr, uid, ids, origin_employee_id,
                            context=None):
        # Rellena los campos necesarios acorde con el solicitante

        hr_obj = self.pool.get('hr.employee')

        manager = hr_obj.browse(cr, uid, origin_employee_id)
        empl_depart_id = manager.department_id.id
        hr_depart = self.pool.get('hr.department')

        # Buscar los departamentos que tenga como ID padre
        # el id que viene de la variable empl_depart_id
        depart_hijos = hr_depart.search(cr, uid,
                                        [('parent_id', '=', empl_depart_id)])

        lista = []
        for dep in depart_hijos:
            temp = hr_depart.search(cr, uid, [('parent_id', '=', dep)])

            if temp:
                lista.append(temp)

        depart_nietos = [n for sublista in lista for n in sublista]

        all_depart = depart_hijos + depart_nietos

        empleados = hr_obj.search(cr, uid,
                                  [('department_id', '=', empl_depart_id)])
        empleados += hr_obj.search(cr, uid,
                                   [('department_id', 'in', all_depart)])

        domain = [('id', 'in', empleados)]

        # Retorna todos los IDs de los usuarios que esten en el grupo 518
        # que es Internal Requisition / Manager
        users_requi_manager = self.pool.get('res.users').search(
            cr, uid, [('groups_id.id', '=', 518)]
        )

        resource = self.pool.get('resource.resource')

        res = resource.search(cr, uid, [('user_id', 'in', users_requi_manager)])

        empleados_id = hr_obj.search(cr, uid, [('resource_id', 'in', res)])
        values = {
            'value': {
                'origin_address': False,
                'origin_department_id': False,
                'origin_company_id': False,
                'origin_state_id': False,
            },
            'domain': {
                'employee_id': domain,
                'origin_employee_id': [('id', 'in', empleados_id)],
            }
        }

        if origin_employee_id in empleados_id:
            employee = hr_obj.browse(cr, uid, origin_employee_id)

            values = {
                'value': {
                    'origin_address': employee.company_id.partner_id.street,
                    'origin_department_id': employee.department_id.id,
                    'origin_company_id': employee.company_id.id,
                    'origin_state_id':
                        employee.company_id.partner_id.state_id.id,
                },
                'domain': {
                    'employee_id': domain,
                    'origin_employee_id': [('id', 'in', empleados_id)],
                }
            }

        return values

    def onchange_empleado(self, cr, uid, ids, empleado, context=None):
        hr_obj = self.pool.get('hr.employee')
        hr_contract_obj = self.pool.get('hr.contract')

        values = {'value': {
                    'actual_employee_code': False,
                    'actual_identification_id': False,
                    'actual_dependency': False,
                    'actual_ocupation': False,
                    'actual_salary_scale_category': False,
                    'actual_salary_scale_level': False,
                    'actual_parent_id': False,
                }
        }

        if empleado:
            empleado_obj = hr_obj.browse(cr, uid, empleado, context=None)
            contratos_id = hr_contract_obj.search(cr, uid,
                                                  [('employee_id', '=', empleado)],
                                                  order='date_start')
            sueldo = 0
            for salario in hr_contract_obj.browse(cr, uid, contratos_id):
                sueldo += salario.wage

            values = {'value': {
                        'actual_employee_code': empleado_obj.employee_code,
                        'actual_identification_id': empleado_obj.identification_id,
                        'actual_dependency': empleado_obj.department_id.id,
                        'actual_ocupation': empleado_obj.job_id.id,
                        'actual_salary_scale_category':
                            empleado_obj.salary_scale_category,
                        'actual_salary_scale_level': empleado_obj.salary_scale_level,
                        'actual_parent_id': empleado_obj.parent_id.id,
                        'contract_id': contratos_id,
                        'monthly_salary': sueldo,
                    }
            }

        return values

    def onchange_contract_id(self, cr, uid, ids, employee_id=False,
                             contract_id=False, context=None):
        if context is None:
            context = {}
        hr_contract_obj = self.pool.get('hr.contract')
        res = {'value': {}}
        emp_cont = hr_contract_obj.browse(cr, uid, contract_id, context=None)
        # context.update({'contract': True, 'actual_wage': emp_cont.wage,
        #  'actual_diff_scale': emp_cont.diff_scale})
        print emp_cont.wage, 'salario'
        res['value'].update({'actual_wage': emp_cont.wage,
                             'actual_diff_scale': emp_cont.diff_scale,
                             'actual_total': emp_cont.wage + emp_cont.diff_scale,
                             'actual_orderly_turn': emp_cont.working_hours.id,
                             'monthly_salary': emp_cont.wage,
                             }
                            )
        if not contract_id:
            res['value'].update({'struct_id': False})
        return res

    def onchange_action_requested(self, cr, uid, ids, action_requested,
                                  context=None):

        if action_requested == 'designacion':
            return {'value': {'action_changes_requested': False,
                              'action_out_requested': False,
                              'action_others_requested': False}}

        elif action_requested == 'cambios':
            return {'value': {'action_designation_requested': False,
                              'action_out_requested': False,
                              'action_others_requested': False}}

        elif action_requested == 'salidas':
            return {'value': {'action_designation_requested': False,
                              'action_changes_requested': False,
                              'action_others_requested': False}}

        elif action_requested == 'vacation_and_licenses':
            return {'value': {'action_designation_requested': False,
                              'action_changes_requested': False,
                              'action_out_requested': False}}
        else:
            return {'value': {
                'action_changes_requested': False,
                'action_out_requested': False,
                'action_others_requested': False,
                'action_designation_requested': False, }}

    def onchange_end_of_vac(self, cr, uid, ids, effective_date,
                            days_of_vacations, context=None):
        return self.num_days(cr, uid, ids, effective_date, days_of_vacations)

    def onchange_option(self, cr, uid, ids, catg, opc, employee_id, fecha_fin=None,
                        context=None):
        hr_holiday_status_obj = self.pool.get('hr.holidays.status')
        hr_cont_obj = self.pool.get('hr.contract')

        if catg == 'salidas':
            value = self.calc_beneficios(cr, uid, ids, employee_id, fecha_fin, opc)
            return value

        if catg == "vacation_and_licenses" and opc:
            concepto_de = {
                '1': 19,  # Dia de asueto
                '2': 9,   # Licencia de por alumbramiento (conyuge)
                '3': 6,   # Licencia por enfermedad
                '4': 7,   # Licencia por fallecimiento de familiar (directo)
                '5': 15,  # Licencia por fallecimiento de familiar (indirecto)
                '6': 5,   # Licencia por maternidad
                '7': 8,   # Licencia de matrimonio
                '8': 20,  # Licencia sin disfrute de sueldo
                '9': 10,  # Tardanza
                '10': 18,  # Medio Dia de Cumpleaños
                '11': 27,  # Vacaciones
                '12': 13,  # Ausencia Justificada
                '13': 14,  # Licencia por estudios
                '14': 12,  # Ausencia no Justificada
            }

            if opc == '10':
                return {'value': {'days_of_vacations': 0.5}}

            elif opc == '11':

                hoy = datetime.date.today()

                try:
                    contract_id = hr_cont_obj.search(
                        cr, uid, [('employee_id', '=', employee_id)],
                        order='date_start')[0]
                except IndexError:
                    raise osv.except_osv(_('Warning'),
                                         _('El Empleado debe de contar '
                                           'con almenos Un Contrato de Trabajo'
                                           ' para esta Accion. !'))

                oldcontr = hr_cont_obj.browse(cr, uid, contract_id).date_start

                dias = (hoy - self.str_to_datetime(cr, uid, ids, oldcontr)).days
                anios = dias / 365
                get_dias = 14 if anios <= 5 else 19 if anios <= 10 else 21

                return {'value': {'days_of_vacations': get_dias}}
            else:
                id_hs = concepto_de[opc]

                # Obtiene los dias de la licencia.
                dias = hr_holiday_status_obj.browse(cr, uid, id_hs).dias



                return {'value': {'days_of_vacations': dias}}

    def create(self, cr, uid, ids, context=None):
        if 'from_holi' in ids:  # Si se crea desde la Peticion de Ausencias.
            del ids['from_holi']
            creado = super(HrPersonnelAction, self).create(cr, uid, ids, context)

            self.write(cr, uid, creado, {'stage': 'draft', 'states': 'draft'})

            return creado

        if ids['action_designation_requested'] in ['1', '2', '9']:
            cont_fecha = self.pool.get('hr.contract').browse(
                cr, uid, ids['contract_id']).date_end
            if cont_fecha:
                prop = ids['proposed_end_new_contract']

                # Verifica si la fecha propuesta es mayor
                # a la fecha con la que ya cuenta el contrato
                is_check = self.verificar_fechas(cr, uid, ids, cont_fecha, prop)

                if not is_check:  # Si la fecha Propuesta es menor.
                    raise osv.except_osv(
                        'Error', 'La fecha de Fin de contrato debe '
                                 'ser mayor a la que ya cuenta el '
                                 'contrato: {0}'.format(cont_fecha))

        if ids['action_designation_requested'] == '3':
            contrato = self.pool.get('hr.contract').browse(cr, uid,
                                                           ids['contract_id'])
            if contrato.type_id.id != 1:
                raise osv.except_osv(
                    'Error', 'El Contrato seleccionado debe '
                             'ser un Contrato tipo Fijo no '
                             'un {}'.format(contrato.type_id.name[9:]))

        value = ids

        empleado_id = ids['employee_id']
        empleado = self.pool.get('hr.employee').browse(cr, uid, empleado_id)

        deparramento_id = empleado.department_id.id
        ocupacion = empleado.job_id.id
        manager = empleado.parent_id.id

        seq = self.pool.get('ir.sequence').get(cr, uid, 'hr.personnel.action')

        ids['end_of_leave'] = self.num_days(cr, uid, ids,
                                            ids['effective_date'],
                                            ids['days_of_vacations']
                                            )['value']['end_of_leave']

        ids['actual_employee_code'] = empleado.employee_code

        ids['actual_identification_id'] = empleado.identification_id

        hh_id_id = ''
        num = ''
        if ids['action_others_requested']:
            num = ids['action_others_requested']
            accion = {
                '1': {'name': 'Solic. de Asueto',
                      'hsi': 19},
                '2': {'name': 'Solic. Licencia Alumbramiento conyugue',
                      'hsi': 9},
                '3': {'name': 'Solic. Licencia por Enfermedad',
                      'hsi': 6},
                '4': {'name': 'Solic. Licencia Fallecimiento Fam. Direct.',
                      'hsi': 7},
                '5': {'name': 'Solic. Licencia Fallecimiento Fam. Indirec.',
                      'hsi': 15},
                '6': {'name': 'Solic. Licencia por Maternidad',
                      'hsi': 5},
                '7': {'name': 'Solic. Licencia por Matrimonio',
                      'hsi': 8},
                '8': {'name': 'Solic. LIcencia sin disfrute de sueldo',
                      'hsi': 20},
                '9': {'name': 'Tardanza',
                      'hsi': 10},
                '10': {'name': 'Solic. Medio dia de Cumpleanos',
                       'hsi': 18},
                '11': {'name': 'Solic. de Vacaciones',
                       'hsi': 27},
                '12': {'name': 'Ausencias justificadas',
                       'hsi': 13},
                '13': {'name': 'Solic. Licencia por Estudios',
                       'hsi': 14},
                '14': {'name': 'Ausencias No justificadas',
                       'hsi': 12},
            }

            if num not in ['3', '9', '14']:
                hr_holiday = self.pool.get('hr.holidays')

                name = accion[num]['name']
                hsi = accion[num]['hsi']

                hh_id_id = hr_holiday.create(
                    cr, uid, {'holiday_status_id': hsi,
                              'employee_id': ids['employee_id'],
                              'department_id': ids['proposed_dependency'],
                              'holiday_type': 'employee',
                              'date_from': ids['effective_date'],
                              'type': 'remove',
                              'date_to': ids['end_of_leave'],
                              'number_of_days_temp': ids['days_of_vacations'],
                              'name': name,
                              'horas': ids['proposed_hours'],
                              'from_ap': 'True', })

                hr_holiday.write(cr, uid, hh_id_id, {'state': 'confirm'})

        data = {
            'referencia': seq,
            'states': 'draft',
            'creado_por': uid,
            'stage': 'draft',
            'actual_dependency': deparramento_id,
            'actual_ocupation': ocupacion,
            'actual_parent_id': manager,
            'peticion_ausencia': hh_id_id,
            'end_of_leave': ids['end_of_leave'],
            'actual_employee_code': ids['actual_employee_code'],
            'actual_identification_id': ids['actual_identification_id'],
        }
        value.update(**data)
        if ids['action_out_requested']:
            beneficios = self.calc_beneficios(
                cr, uid, ids, empleado_id, ids['effective_date'],
                ids['action_out_requested'], ids['fue_preavisado'],
                ids['tomo_vacaciones'], ids['incluir_cesantia'],
                ids['incluir_salario_navidad'], ids['contract_id'])['value']
            value.update(**beneficios)

        creado = super(HrPersonnelAction, self).create(cr, uid, value,
                                                       context=None)

        if ids['action_others_requested'] and num == '10':
            self.write(cr, uid, creado, {'states': 'draft',
                                         'days_of_vacations': 0.50})

        else:
            self.write(cr, uid, creado, {'states': 'draft', 'stage': 'draft'})

        return creado

    def unlink(self, cr, uid, ids, context=None):
        for id in ids:
            pa = self.browse(cr, uid, id).peticion_ausencia

            # Si tiene peticion de ausencia.
            if pa:
                self.pool.get('hr.holidays').write(cr, uid, pa.id,
                                                   {'state': 'refuse'})

        super(HrPersonnelAction, self).unlink(cr, uid, ids, context=None)

    def button_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'states': 'confirmed',
                                  'stage': 'confirmed',
                                  'confirmado_por': uid,
                                  }, context=None)
        return True

    def state_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'states': 'applied', 'stage': 'applied'})
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        ap = self.pool.get('hr.personnel.action').browse(cr, uid, ids)

        if ap.peticion_ausencia:
            holiday_obj = self.pool.get('hr.holidays')

            hd = holiday_obj.browse(cr, uid, ap.peticion_ausencia.id)

            holiday_obj.write(cr, uid, hd.id, {'state': 'cancel'})

        self.write(cr, uid, ids, {'states': 'cancelled',
                                  'cancelado_por': uid,
                                  }, context=None)

        return True

    def button_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'states': 'draft',
                                  'stage': 'draft',
                                  'creado_por': uid,
                                  }, context=None)

        return True

    def button_aprobacion_gh(self, cr, uid, ids, context=None):
        lic = self.browse(cr, uid, ids)
        if lic.action_requested != 'vacation_and_licenses':
            self.write(cr, uid, ids, {'stage': 'confirmed2',
                                      'states': 'approved',
                                      'aprobadogh_por': uid,})
        else:
            self.write(cr, uid, ids, {'stage': 'listo',
                                      'aprobadogh_por': uid,})

        # if lic.action_requested == 'vacation_and_licenses':
        #     self.write(cr, uid, ids, {'stage': 'listo'})


        return True

    def aprobacion_dgh(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'states': 'approved', 'stage': 'approved',
                                         'aprobaciondgh_por': uid,})


    def button_aprobacion_de(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'states': 'aprobacion_de',
                                  'stage': 'listo',
                                  'aprobadode_por': uid,
                                  }, context=None)
        return True

    def num_days(self, cr, uid, ids, effective_date, days_of_vacations,
                 context=None):
        """
        Se encarga de calcular y retornar la fecha de fin ( date_to )
        para las licencias y vacaciones, omitiendo los fines de semana
        y los dias festivos que se encuentren registrados previamente
        en el modelo ( hr_holiday_list ).

        Note: Se utiliza la ThirdPartyModule llamado " workdays ".

        : param effective_date: 2016/01/22
        : type effective_date: str
        : param days_of_vacations: 14
        : type days_of_vacations: int
        : return: 2016/02/15
        : type return: datetime
        """

        # Obtiene el anio actual. ( current_year )
        c_year = datetime.date.today().year

        if effective_date:
            holiday_list_obj = self.pool.get('hr.holiday.list')
            holidays_ids = holiday_list_obj.search(
                cr, uid, [('day', '>=', '01/01/' + str(c_year)),
                          ('day', '<=', '01/01/' + str(c_year + 1))])

            holiday_list = holiday_list_obj.browse(cr, uid, holidays_ids)

            all_str_date = []
            for date in holiday_list:
                all_str_date.append(date.day)

            # Convierte el listado de fechas a tipo datetime
            all_holidays = self.str_to_datetime(cr, uid, ids, all_str_date)

            effdate = self.str_to_datetime(cr, uid, ids, effective_date)

            days_of_vacations = 0 if days_of_vacations < 1 else int(
                days_of_vacations)

            wkd = workday(effdate, days_of_vacations, all_holidays)

            return {'value': {'end_of_leave': wkd}}

    def str_to_datetime(self, cr, uid, ids, str_date, context=None):
        """
        Convierte fechas dadas en formato <string> a formato <datetime>.

        El parametro str_date puede ser una fecha o una lista de fechas.
        : param str_date: '2016/2/14' or ['2016/2/14', '2016/2/27']
        : return: datetime(2016, 2. 14) or [datetime(2016, 2, 14), ...]
        """

        if isinstance(str_date, list):
            fechas = []
            for date in str_date:
                fecha = datetime.datetime.strptime(date, '%Y-%m-%d')
                fecha = datetime.date(fecha.year, fecha.month, fecha.day)
                fechas.append(fecha)

            return fechas

        elif isinstance(str_date, str):
            str_date = str_date[: 10]
            fecha = datetime.datetime.strptime(str_date, '%Y-%m-%d')
            fecha = datetime.date(fecha.year, fecha.month, fecha.day)

            return fecha

    def enable_employee_from_licence_or_vacation(self, cr, uid):

        #
        # Esto es una Accion Automatizada para poder quitarle el CHECK
        # de Vacaciones o Licencias a los Empleados
        #

        today = datetime.date.today()

        hr_obj = self.pool.get('hr.employee')

        hr_holidays_obj = self.pool.get('hr.holidays')

        hr_holidays_id = hr_holidays_obj.search(
            cr, uid, [('date_to', '<', str(today)), ('concluido', '=', False)])

        hr_holidays_id_obj = hr_holidays_obj.browse(cr, uid, hr_holidays_id)

        emp_rea = 0
        id_emp = []
        for lic_or_vac in hr_holidays_id_obj:
            if lic_or_vac.date_to:

                hr_holidays_obj.write(cr, uid, lic_or_vac.id, {'concluido': True})
                hr_obj.write(cr, uid, lic_or_vac.employee_id.id,
                             {'on_licence': False,
                              'on_vacation': False})
                emp_rea += 1
                id_emp.append(lic_or_vac.employee_id.id)

        _logger.info("""
        Se termino la Accion Automatizada:
         |------------( enable_employee_from_licence_or_vacation )
                        |----( Total de Empleados Reanudados: {} )
                        |----( ID de los Empleados: {} )
         """.format(emp_rea, id_emp))

HrPersonnelAction()


class HrEmployee(osv.osv):
    _name = 'hr.employee'
    _inherit = 'hr.employee'
    _columns = {
        'salary_scale_category': fields.selection(
            (
                ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'),
                ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'),
                ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'),
                ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
                ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'),
                ('25', '25')
            ), 'Salary Scale Category'
        ),

        'salary_scale_level': fields.selection(
            (
                ('1', '1'), ('2', '2'), ('3', '3'),
                ('4', '4'), ('5', '5'), ('6', '6')
            ), 'Salary Scale Level'
        ),

        'personnel_actions_ids': fields.one2many('hr.personnel.action',
                                                 'employee_id',
                                                 'Personnel actions'),

        'transfer_to': fields.many2one('res.company', 'Transfererido a '),
        'on_vacation': fields.boolean('On vacation'),
        'on_licence': fields.boolean('On licence'),
        'proposed_misconduct': fields.text('Amonestacion'),
        'proposed_misconduct_level': fields.selection(
            (
                ('1', '1'), ('2', '2'), ('3', '3')
            ), 'Nivel falta cometida'
        ),

    }


HrEmployee()


class HrContract(osv.osv):
    # Class extends the hr.contract model with 1 field.
    _name = "hr.contract"
    _inherit = "hr.contract"
    _columns = {
        'diff_scale': fields.float('Diff. Scale', size=16),
    }

    _defaults = {
        'name': ' ',
    }

    def get_analytic_account(self, cr, uid, ids, employee_id, context=None):

        if employee_id:
            empl_obj = self.pool.get('hr.employee')

            job = empl_obj.browse(cr, uid, employee_id).job_id.id
            department = empl_obj.browse(cr, uid, employee_id).department_id.id

            # depart = department.parent_id.id if department.parent_id else department.id

            analitic_account_obj = self.pool.get('account.analytic.account')
            analytic_id = analitic_account_obj.search(
                cr, uid, [('department_id', '=', department)])

            print job
            print department
            print analytic_id
            try:
                analytic_id1 = analytic_id[0]
            except IndexError:
                analytic_id1 = False
                
            return {'value': {'job_id' : job, 'analytic_account_id': analytic_id1}}

    def create(self, cr, uid, ids, context=None):
        # Overwritten to the create method of hr_contract.

        created_id = super(HrContract, self).create(cr, uid, ids, context)

        ids['name'] = self.pool.get('ir.sequence').get(cr, uid, 'hr.contract')

        self.write(cr, uid, created_id, ids, context)

        return created_id

HrContract()


class HrHolidays(osv.osv):
    #
    # Clase para Extender el modelo hr.holidays.
    #

    _name = "hr.holidays"
    _inherit = "hr.holidays"

    _columns = {
        "horas": fields.float('Horas',
                              help="Ej: 1.15 Una Hora con Quince Minutos"),
        'concluido': fields.boolean(default=False),

    }

    def onchange_fecha_dias(self, cr, uid, ids, date_from, dias):
        #
        # Update the number_of_days.
        #

        result = {'value': {}}

        c_year = datetime.date.today().year

        if date_from and dias:
            holiday_list_obj = self.pool.get('hr.holiday.list')
            holidays_ids = holiday_list_obj.search(
                cr, uid, [('day', '>=', '01/01/' + str(c_year)),
                          ('day', '<=', '01/01/' + str(c_year+1))],
                context=None)
            holiday_list = holiday_list_obj.browse(cr, uid, holidays_ids)

            ap = self.pool.get('hr.personnel.action')

            all_str_date = []
            for date in holiday_list:
                all_str_date.append(date.day)

            # Convierte el listado de fechas a tipo datetime
            all_holidays = ap.str_to_datetime(cr, uid, ids, all_str_date)

            effdate = ap.str_to_datetime(cr, uid, ids, date_from)

            if dias != 0.5:
                dia_temp = int(dias) if dias > 1 else 1
                wkd = workday(effdate, dia_temp, all_holidays)
            else:
                wkd = effdate

            return {'value': {'date_to': wkd}}

        return result

    def onchange_option(self, cr, uid, ids, opc, employee_id):
        hr_holiday_status_obj = self.pool.get('hr.holidays.status')
        # hr_obj = self.pool.get('hr.employee')
        hr_cont_obj = self.pool.get('hr.contract')
        ap = self.pool.get('hr.personnel.action')

        if opc == 27:

            hoy = datetime.date.today()

            try:
                contract_id = hr_cont_obj.search(
                            cr, uid, [('employee_id', '=', employee_id)],
                            order='date_start')[0]
            except IndexError:
                raise osv.except_osv(_('Warning'),
                                     _('El Empleado debe de contar '
                                       'con almenos Un Contrato de Trabajo'
                                       ' para esta Accion. !'))

            oldcontr = hr_cont_obj.browse(cr, uid, contract_id).date_start

            dias = (hoy - ap.str_to_datetime(cr, uid, ids, oldcontr)).days
            anios = dias / 365
            get_dias = 14 if anios <= 5 else 19 if anios <= 10 else 21

            return {'value': {'number_of_days_temp': get_dias}}

        # Si es Medio Dia de cumpleanos
        elif opc == 18:
            return {'value': {'number_of_days_temp': 0.5, }}

        # Obtiene los dias de la licencia.
        dias = hr_holiday_status_obj.browse(cr, uid, opc).dias

        return {'value': {'number_of_days_temp': dias, }}

    def unlink(self, cr, uid, ids, context=None):
        for id in ids:
            ap = self.pool.get('hr.personnel.action')
            ap_id = ap.search(cr, uid, [('peticion_ausencia', '=', id)])
            
            if ap_id:
                ap.write(cr, uid, ap_id, {'states': 'cancelled'})
        
        super(HrHolidays, self).unlink(cr, uid, ids, context)

    def create(self, cr, uid, ids, context=None):
        accion_id = ids['holiday_status_id']
        concepto_de = {
                19: '1',   # Dia de asueto
                9: '2',    # Licencia de por alumbramiento (conyuge)
                6: '3',    # Licencia por enfermedad
                7: '4',    # Licencia por fallecimiento de fam (directo)
                15: '5',   # Licencia por fallecimiento de fam (indirecto)
                5: '6',    # Licencia por maternidad
                8: '7',    # Licencia de matrimonio
                20: '8',   # Licencia sin disfrute de sueldo
                10: '9',   # Tardanza
                18: '10',  # Medio Dia de Cumpleaños
                27: '11',  # Vacaciones
                13: '12',  # Ausencia Justificada
                14: '13',  # Licencia por estudios
                12: '14',  # Ausencia no Justificada

        }

        if ids['type'] == 'remove':

            if 'from_ap' in ids:
                del ids['from_ap']
                return super(HrHolidays, self).create(cr, uid, ids, context)

            all_value = {}
            values = ids

            ap = self.pool.get('hr.personnel.action')
            hr_holiday_status_obj = self.pool.get('hr.holidays.status')

            employee_id = values['employee_id']
            employee_obj = self.pool.get('hr.employee').browse(cr, uid,
                                                               employee_id)

            director_id = employee_obj.parent_id.id

            director_data = ap.onchange_petitioner(cr, uid, ids, director_id)

            employee_data = ap.onchange_empleado(cr, uid, ids, employee_id)

            solicita = concepto_de[accion_id]

            date_from = values['date_from']

            if 'number_of_days_temp' in values:
                dias = values['number_of_days_temp']

            else:
                # Si es Medio Dia de Cumpleanos
                if accion_id == 18:
                    dias = 0.5

                # Si Es vacaciones
                elif accion_id == 27:
                    hr_cont_obj = self.pool.get('hr.contract')
                    hoy = datetime.date.today()

                    contract_id = hr_cont_obj.search(
                        cr, uid, [('employee_id', '=', employee_id)],
                        order='date_start')[0]

                    oldcon = hr_cont_obj.browse(cr, uid, contract_id).date_start

                    d = (hoy - ap.str_to_datetime(cr, uid, ids, oldcon)).days
                    anios = d / 365

                    dias = 14 if anios <= 5 else 19 if anios <= 10 else 21

                else:
                    # Busca los Dias que corresponde a la accion Solicitada
                    dias = hr_holiday_status_obj.browse(cr, uid, accion_id).dias

            # Fecha en que se concluye la licencia/vacaiones
            if dias != 0.5:
                dia_temp = int(dias) if dias > 1 else 1
                end = ap.num_days(cr, uid, ids, date_from, dia_temp)['value'][
                    'end_of_leave']
            else:
                end = date_from

            cont = employee_obj.contract_id.id

            ids['date_to'] = end
            ids['number_of_days_temp'] = dias

            created_id = super(HrHolidays, self).create(cr, uid, ids, context)

            seq = self.pool.get('ir.sequence').get(cr, uid,
                                                   'hr.personnel.action')
            comentario = ''
            if ids['name']:
                comentario = '<ul><li><span style="font-weight: bold;">' \
                             'DESCRIPCION y/o DE LA LICENCIA. POR {empl_name} :' \
                             '</span></li></ul><blockquote style="margin: -15px 0 0 40px; ' \
                             'border: none; padding: 0px;">' \
                             '<span style="font-size:13px;">{comm}' \
                             '</span></blockquote>'.format(empl_name=employee_obj.name,
                                                           comm=ids['name'])

            datos = {
                'referencia': seq,
                'origin_employee_id': director_id,
                'employee_id': employee_id,
                'contract_id': cont,
                'action_requested': 'vacation_and_licenses',
                'action_others_requested': solicita,
                'effective_date': date_from,
                'days_of_vacations': dias,
                'end_of_leave': end,
                'peticion_ausencia': created_id,
                'observations': comentario,
                'states': 'draft',
                'stage': 'draft',
                'creado_por': uid,
                'from_holi': 'True',
            }
            _logger.info(datos['days_of_vacations'])
            all_value.update(**employee_data['value'])
            all_value.update(**datos)
            all_value.update(**director_data['value'])

            ap_id = ap.create(cr, uid, all_value)
            ap.write(cr, uid, ap_id, {'states': 'draft'})
            
            return created_id

        # if ids['type'] == 'add':
        #     ap = self.pool.get('hr.personnel.action')
        #
        #     hr_holiday_status_obj = self.pool.get('hr.holidays.status')
        #     ids['number_of_days_temp'] = hr_holiday_status_obj.browse(
        #                                             cr, uid, accion_id).dias
        #     ids['date_to'] = ap.num_days(cr, uid, ids,
        #                          ids['date_from'],
        #                          ids['number_of_days_temp'])['value']['end_of_leave']

        return super(HrHolidays, self).create(cr, uid, ids, context)

HrHolidays()


class HrHolidaysList(osv.osv):
    # Modelo para registrar los dias festivos.

    _name = 'hr.holiday.list'

    _columns = {
        'description': fields.char('Descipcion', help='EJ: Dia de Duarte.'),
        'day': fields.date('Fecha ', required=True),
    }

HrHolidaysList()


class HrHolidaysStatus(osv.osv):
    #
    # Clase para Extender el modelo hr.holidays.status
    #
    # INFO: hr.holidays.status es donde se almacenan
    # los tipos de licencias que tiene el sistema.
    #

    _name = 'hr.holidays.status'
    _inherit = 'hr.holidays.status'

    _columns = {
        'dias': fields.integer('Dias'),
    }

HrHolidaysStatus()


# Acciones Automatizadas para los Activos.
class Activos(osv.osv):

    _inherit = 'account.asset.asset'

    def calcular_tabla_activos(self, cr, uid):
        activo_obj = self.pool.get('account.asset.asset')
        activos_ids = activo_obj.search(cr, uid, [(1, '=', 1)])
        total = len(activos_ids)

        for num, id in enumerate(activos_ids):
            _logger.info('por el {0} de {1}'.format(num, total))
            activo = activo_obj.browse(cr, uid, id)

            activo.compute_depreciation_board()

        return True

    def update_activos_values(self, cr, uid):

        # Esta funcion sera una Accion Programada, cuyo objetivo es
        # de actualizar multiples campos de los activo.

        activo_obj = self.pool.get('account.asset.asset')
        cat_obj = self.pool.get('account.asset.category')

        # Para Obtener todos los ID de los activos.
        activo_ids = activo_obj.search(cr, uid, [(1, '=', 1)])
        total = len(activo_ids)

        for num, id in enumerate(activo_ids):
            activo = activo_obj.browse(cr, uid, id)

            activo_cat_id = activo.category_id.id

            categoria = cat_obj.browse(cr, uid, activo_cat_id)

            _logger.info('Posicion: {0}/{1}'.format(num, total))

            activo_obj.write(cr, uid, id,
                             {'prorata': categoria.prorata,
                              'method_number': categoria.method_number,
                              'method_period': 1,
                              })

        return True

    def update_parent_category(self, cr, uid):

        # Esta funcion sera una Accion Programada, cuyo objetivo es
        # de actualizar la categoria padre del activo.

        activo_obj = self.pool.get('account.asset.asset')
        cat_obj = self.pool.get('account.asset.category')

        # Para Obtener todos los ID de los activos.
        activo_ids = activo_obj.search(cr, uid, [(1, '=', 1)])

        for num, id in enumerate(activo_ids):
            activo = activo_obj.browse(cr, uid, id)

            activo_cat_id = activo.category_id.id

            activo_cat_parent_id = activo.category_parent_id.id

            cat_parent_ori = cat_obj.browse(cr, uid, activo_cat_id).parent_id.id

            if activo_cat_parent_id != cat_parent_ori:

                activo_obj.write(cr, uid, id,
                                 {'category_parent_id': cat_parent_ori})

        return True

Activos()


class Employee(osv.osv):
    _inherit = 'hr.employee'

    def set_antiguedad_label(self, cr, uid):
        
        contra_obj = self.pool.get('hr.contract')

        # Lista de IDs de todos los empleados.
        empleados_ids = self.search(cr, uid, [(1, '=', 1)])

        hoy = datetime.date.today()

        for empleado_id in empleados_ids:

            try:
                # Obtiene el contrato mas Antiguo del Empleado.
                contra_id = contra_obj.search(
                    cr, uid, [('employee_id', '=', empleado_id)],
                    order='date_start')[0]

            except IndexError:
                continue

            # if contra_id:
            contra_viejo = contra_obj.browse(cr, uid, contra_id).date_start

            # Convertir la fecha tipo STR a tipo DATETIME
            fecha = datetime.datetime.strptime(contra_viejo, '%Y-%m-%d')
            fecha = datetime.date(fecha.year, fecha.month, fecha.day)

            dias = (hoy - fecha).days
            anios = dias / 365

            # ID de la Etiqueta de Antiguedad que le corresponde
            # segun la fecha del contrato mas antigup del empleado.
            etiqueta_id = 2 if anios <= 5 else 3 if anios <= 10 else 4

            etiquetas_empl = self.browse(cr, uid, empleado_id).category_ids
            etiquetas_ids = [etiqueta.id for etiqueta in etiquetas_empl]

            if etiqueta_id not in etiquetas_ids:
                # Remover las Etiquetas de Antiguedad anteriores.
                update = [et for et in etiquetas_ids if et not in [2, 3, 4]]
                update.append(etiqueta_id)

                self.write(cr, uid, empleado_id,
                           {'category_ids': [(6, 0, update)]})
        return True



class ProductUpdate(osv.osv):
    _inherit = 'product.template'

    def onchange_category(self, cr, uid, ids, id_categoria, context=None):
        values = {'value': {
            'property_account_income':False,
            'property_account_expense': False,
            'property_stock_account_input': False,
        }}
        if id_categoria:
            categ_obj = self.pool.get('product.category')
            categ = categ_obj.browse(cr, uid, id_categoria)
            values = {'value': {
                'property_account_income': categ.property_account_income_categ.id,
                'property_account_expense': categ.property_account_expense_categ.id,
                'property_stock_account_input': categ.property_stock_account_input_categ.id,
            }}

        return values


    def update_product_categ(self, cr, uid):
        # pro = self.pool.get('product.template')
        prod_ids = self.search(cr, uid, [('purchase_ok','=', True)])
        products = self.browse(cr, uid, prod_ids)

        for num, product in enumerate(products):

            # print num
            # print product.categ_id.property_account_income_categ
            # print product.property_account_income
            # print product.property_account_income
            # print product.categ_id.property_account_income_categ
            # print product.id
            _logger.info('{} / {})'.format(num, len(products)))
            ingreso = False
            if product.categ_id.property_account_income_categ:  # and not product.property_account_income:
                self.write(cr, uid, product.id,
                          {'property_account_income':product.categ_id.property_account_income_categ.id})
                ingreso = True

            gasto = False
            if product.categ_id.property_account_expense_categ:  # and not product.property_account_expense:

                self.write(cr, uid, product.id,
                          {'property_account_expense': product.categ_id.property_account_expense_categ.id})
                gasto = True

            inventario = False
            if product.categ_id.property_stock_account_input_categ:  # and not product.property_stock_account_input:

                self.write(cr, uid, product.id,
                          {'property_stock_account_input': product.categ_id.property_stock_account_input_categ.id})
                inventario = True

            if ingreso or gasto or inventario:
                _logger.info(product.id)

        return True

ProductUpdate()