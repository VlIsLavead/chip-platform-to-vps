STATUS_CONFIG = {
        'MTP': {
            'title': 'Этап производства шаблонов',
            'next_status': 'MPP',
            'prev_status': 'MPO',
            'next_button': 'Передать заказ на этап производства пластин',
            'prev_button': 'Отменить изменения',
        },
        'MPP': {
            'title': 'Этап производства пластин', 
            'next_status': 'MPM',
            'prev_status': 'MTP',
            'next_button': 'Передать заказ на этап измерениий ПМ',
            'prev_button': 'Вернуть заказ на этап производства шаблонов',
        },
        'MPM': {
            'title': 'Этап измерения параметрического монитора',
            'next_status': 'MCP', 
            'prev_status': 'MPP',
            'next_button': 'Передать заказ на этап резки пластин',
            'prev_button': 'Вернуть заказ на этап производства пластин',
        },
        'MCP': {
            'title': 'Этап резки пластин',
            'next_status': 'MPOP',
            'prev_status': 'MPM', 
            'next_button': 'Передать заказ на этап упаковки пластин',
            'prev_button': 'Вернуть заказ на этап измерения ПМ',
        },
        'MPOP': {
            'title': 'Этап упаковки пластин',
            'next_status': 'SO',
            'prev_status': 'MCP',
            'next_button': 'Завершить производство заказа',
            'prev_button': 'Вернуть заказ на этап резки пластин',
        }
    }