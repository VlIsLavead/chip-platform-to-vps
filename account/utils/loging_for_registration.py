import requests

def get_client_ip(request):
    """Получение реального IP пользователя"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_country_by_ip(ip):
    """Определение страны по IP адресу через бесплатный API"""
    # Пропускаем локальные IP адреса
    local_ips = ['127.0.0.1', 'localhost', '::1']
    if ip in local_ips or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
        return 'Локальный адрес'
    
    try:
        # Используем бесплатный API ip-api.com
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = response.json()
        
        if data.get('status') == 'success':
            return data.get('country', 'Неизвестно')
        else:
            return 'Не удалось определить'
    except Exception as e:
        print(f'Ошибка при определении страны: {e}')
        return 'Ошибка определения'