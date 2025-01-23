import openpyxl
from openpyxl.styles import Font, Border, Side, Alignment
from ..models import *


def generate_excel_file(request, session_data=None, order_id=None):
    # TODO refactor if chain, move decision logic to the call site
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return None
    else:
        if session_data is None:
            session_data = request.session.get('form_data', None)
        if session_data is None:
            return None

        order_id = session_data.get('id')
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return None

    order_type_code = session_data.get('order_type') if not order_id else order.order_type
    order_type_display = dict(Order.OrderType.choices).get(order_type_code, order_type_code)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Order Data'

    first_border = Border(right=Side(style='thick'), bottom=Side(style='thick'))

    header_cell = ws.cell(row=1, column=1, value='Информация по заказу')
    header_cell.font = Font(bold=True)
    header_cell.border = first_border
    header_cell.alignment = Alignment(wrap_text=True)

    custom_headers = {
        'Тип заказа':
            session_data.get('order_start')
            if not order_id else order.order_start,
        'Номер заказа':
            session_data.get('order_number')
            if not order_id else order.order_number,
        'Наименование предприятия заказчика':
            session_data.get('company_name')
            if not order_id else order.creator.company_name,
        'Код заказчика':
            session_data.get('client_code')
            if not order_id else order.creator.id,
        'Номер шаблона':
            'Определяется куратором',
        # TODO если номер шаблона есть, возвращать его, если 0, не возвращать
        'Техпроцесс':
            session_data.get('process_name')
            if not order_id else order.technical_process.name_process,
        'Производственная площадка':
            session_data.get('platform_name')
            if not order_id else order.platform_code.platform_name,
        'Тип запуска':
            session_data.get('order_type')
            if not order_id else order_type_display,
        'Число проектов в кадре':
            session_data.get('product_count')
            if not order_id else order.product_count,
        'Формирование кадра заказчиком':
            session_data.get('formation_frame_by_customer')
            if not order_id else order.formation_frame_by_customer,
        'Тип толщины подложки':
            order.get_substrate_type_display(),
        'Толщина подложки':
            order.selected_thickness.value,
        'Диаметр подложки':
            order.selected_diameter.value,
        'Экспериментальная структура':
            session_data.get('experimental_structure')
            if not order_id else order.experimental_structure,
        'Контроль электрических параметров на пластине':
            order.get_dc_rf_probing_e_map_display(),
        'Маркировка бракованных по электрическим параметрам':
            session_data.get('dc_rf_probing_inking')
            if not order_id else order.dc_rf_probing_inking,
        'Визуальный контроль и маркировка брака':
            session_data.get('visual_inspection_inking')
            if not order_id else order.visual_inspection_inking,
        'Предоставление данных контроля параметрического монитора':
            session_data.get('parametric_monitor_control')
            if not order_id else order.parametric_monitor_control,
        'Способ разделения пластины на кристаллы':
            order.get_dicing_method_display(),
        'УФ засветка полимерного носителя':
            session_data.get('tape_uv_support')
            if not order_id else order.tape_uv_support,
        'Вид поставки пластин':
            session_data.get('wafer_deliver_format')
            if not order_id else order.wafer_deliver_format,
        'Возвращение пластин на фабрику для разделения на кристаллы':
            'НЕПОНЯТНО',
        'Схема разделения пластины на кристаллы по схеме заказчика':
            session_data.get('multiplan_dicing_plan')
            if not order_id else order.multiplan_dicing_plan,
        'Корпусирование силами производителя':
            session_data.get('package_servce')
            if not order_id else order.package_servce,
        'Ускоренный запуск производства фотошаблонов':
            session_data.get('delivery_premium_template')
            if not order_id else order.delivery_premium_template,
        'Ускоренный запуск производства пластин':
            session_data.get('delivery_premium_plate')
            if not order_id else order.delivery_premium_plate,
        'Примечания':
            order.special_note,
        'Форму заполнил':
            '@mail',
    }

    row = 3
    for header, value in custom_headers.items():
        if isinstance(value, bool):
            value = 'да'
        elif value is None:
            value = 'нет'

        header_cell = ws.cell(row=row, column=1, value=header)
        header_cell.alignment = Alignment(wrap_text=True, horizontal='left')

        data_cell = ws.cell(row=row, column=2, value=value)
        data_cell.alignment = Alignment(wrap_text=True, horizontal='left')

        row += 1

    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 35

    return wb
