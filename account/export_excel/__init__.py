import openpyxl

from openpyxl.styles import Font, Border, Side, Alignment
from ..models import *

def generate_excel_file(session_data):
    try:
        order_id = session_data.get('id')
        order = Order.objects.get(id=order_id)
        
        print(session_data)
    except Profile.DoesNotExist:
        print('Профиль не найден')
        
    order_type_code = session_data.get('order_type')
    order_type_display = dict(Order.OrderType.choices).get(order_type_code, order_type_code)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Order Data'
    
    first_border = Border(right=Side(style='thick'),
                          bottom=Side(style='thick'))
    
    header_cell = ws.cell(row = 1, column = 1, value = 'Информация по заказу')
    header_cell.font = ws.cell(row = 1, column = 1).font = Font(bold=True)
    header_cell.border = first_border
    header_cell.alignment = Alignment(wrap_text=True)

    custom_headers = {
        'Тип заказа': 'Не определено',
        'Номер заказа': session_data.get('order_number'),
        'Наименование предприятия заказчика': order.creator.company_name,
        'Код заказчика': order.creator.id,
        'Номер шаблона': 'Определяется куратором',     
        #TODO если номер шаблона есть, возвращать его, если 0, не возвращать
        'Техпроцесс': order.technical_process.name_process,        
        'Производственная площадка': order.platform_code.platform_name,
        'Тип запуска': order_type_display,
        'Число проектов в кадре': session_data.get('product_count'),
        'Толщина подложки': order.substrate.thikness,
        'Диаметр подложки': order.substrate.diameter,
        'Контроль DC/RF параметров на пластине': session_data.get('dc_rf_probing_e_map'),
        'Маркировка бракованных по DC/RF параметрам кристаллов': session_data.get('dc_rf_probing_inking'),
        'Визуальный контроль и маркировка брака': session_data.get('visual_inspection_inking'),
        'Метод разделения пластины на кристаллы': session_data.get('dicing_method'),
        'УФ засветка полимерного носителя': session_data.get('tape_uv_support'),
        'Вид поставки пластин': session_data.get('wafer_deliver_format'),
        'Возвращение пластин на фабрику для разделения на кристаллы': 'НЕПОНЯТНО',
        'Схема разделения пластины на кристаллы': 'загрузить pdf',
        'Корпусирование силами производителя': session_data.get('package_servce'),
        'Ускоренный запуск производства фотошаблонов': session_data.get('delivery_premium_template'),
        'Ускоренный запуск производства пластин': session_data.get('delivery_premium_plate'),
        'Примечания': 'Заполняет заказчик',
        'Форму заполнил': '@mail',
        
    }
    
    first_border = Border(right=Side(style='thick'),
                          bottom=Side(style='thick'))
    
    header_cell = ws.cell(row = 1, column = 1, value = 'Информация по заказу')
    header_cell.font = ws.cell(row = 1, column = 1).font = Font(bold=True)
    header_cell.border = first_border
    header_cell.alignment = Alignment(wrap_text=True)

    row = 3  
    for row, (header, value) in enumerate(custom_headers.items(), start=3):
        if isinstance(value, bool):
            value = 'да' if value else 'нет'
            
        header_cell = ws.cell(row=row, column=1, value=header)
        header_cell.alignment = Alignment(wrap_text=True, horizontal='left')
        data_cell = ws.cell(row=row, column=2, value=value)
        data_cell.alignment = Alignment(wrap_text=True, horizontal='left')
    

        
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 35
            
    return wb