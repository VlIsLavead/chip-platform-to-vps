from account.models import Order

ACCESS_RULES = {
    Order.OrderStatus.NFW: ['Заказчик'],
    Order.OrderStatus.OVK: ['Куратор'],
    Order.OrderStatus.OVC: ['Исполнитель'],
    Order.OrderStatus.OA: ['Заказчик'],
    Order.OrderStatus.SA: ['Заказчик'],
    Order.OrderStatus.CSA: ['Куратор'],
    Order.OrderStatus.ESA: ['Исполнитель'],
    Order.OrderStatus.OGDS: ['Заказчик'],
    Order.OrderStatus.CGDS: ['Куратор'],
    Order.OrderStatus.EGDS: ['Исполнитель'],
    Order.OrderStatus.PO: ['Заказчик'],
    Order.OrderStatus.POK: ['Куратор'],
    Order.OrderStatus.POC: ['Исполнитель'],
    Order.OrderStatus.MPO: ['Исполнитель'],
    Order.OrderStatus.SO: ['Исполнитель'],
    Order.OrderStatus.PS: ['Куратор'],
    Order.OrderStatus.CR: ['Заказчик'],
}