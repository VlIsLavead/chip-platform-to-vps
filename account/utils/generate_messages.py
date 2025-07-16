from ..models import Topic, Message, File

def add_file_message(order, field_name, user):
    file_field = getattr(order, field_name, None)
    
    if not file_field or not file_field.name:
        return
    
    file_display_names = {
        'contract_file': 'Файл договора',
        'GDS_file': 'Файл GDS', 
        'invoice_file': 'Файл счёта',
    }
    
    display_name = file_display_names.get(field_name, field_name)

    topic = Topic.objects.filter(related_order=order).first()
    if not topic:
        return

    message_text = f'📎 Загружен {display_name}'
    message = Message.objects.create(
        topic=topic,
        user=user,
        text=message_text
    )

    File.objects.create(message=message, file=file_field)
