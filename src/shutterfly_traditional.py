from pprint import pformat
import datetime
import math
import operator


def create_new_order(order_id, customer_id, event_time, total_amount):
    """

    :param order_id: str. Order identifier
    :param customer_id: str. Customer that placed the order
    :param event_time: datetime. When the order was placed
    :param total_amount: float. What was the purchase amount
    :return: customer_orders: dict. for each customer return all the orders he's placed so far
    """

    if customer_id not in customer_visits:
        raise RuntimeError('Cannot place an order for a customer that has not visited the site')

    if customer_id not in customer_orders:
        customer_orders[customer_id] = {}

    customer_orders[customer_id][order_id] = {
        'event_time': event_time,
        'order_id': order_id,
        'total_amount': total_amount
    }


def update_order(order_id, customer_id, event_time, total_amount):
    """

    :param order_id:str. Order identifier
    :param customer_id:str. Customer who placed the order
    :param event_time:datetime. Time of the order update
    :param total_amount:float. New amount for order
    :return: customer_orders: dict. update the order
    """
    if not hasattr(customer_orders, order_id):
        raise RuntimeError('Trying to update a non existing order: {}'.format(order_id))

    customer_orders[customer_id][order_id] = {
        'event_time': event_time,
        'order_id': order_id,
        'total_amount': total_amount
    }


def total_customer_expense(customer_id):
    """

    :param customer_id:str. For the given customer, what has he spent so far.
    :return: customer_total_expense: float.
    """

    if customer_id not in customer_orders:
        return 0

    customer_total_expense = 0
    for order_id, order_data in customer_orders[customer_id].items():
        customer_total_expense += order_data['total_amount']

    return customer_total_expense


def add_customer_visit(customer_id, event_time, page_id):
    """

    :param customer_id: str. Customer who visited the site
    :param event_time: datetime. When the customer visited
    :param page_id: str. What page the customer visited
    :return: customer_visits: dict. For each customer, return all their visit activity
    """
    if customer_id not in customer_visits:
        customer_visits[customer_id] = {}

    if event_time in customer_visits[customer_id]:
        raise RuntimeError('Trying to add another visit for the same event time: {}'.format(event_time))

    customer_visits[customer_id][event_time] = page_id


def total_customer_visits(customer_id):
    """

    :param customer_id: Customer identifier
    :return: total_visits: int. Total number of times a customer visited the site
    """
    total_visits = len(customer_visits[customer_id])

    return total_visits


def average_expenditure_per_customer_visit(customer_id):
    """

    :param customer_id: str. Customer identifier
    :return: average_expense_per_customer_visit:float. Avg amount a customer spends per visit
    """
    customer_total_expense = total_customer_expense(customer_id)
    customer_total_visits = total_customer_visits(customer_id)
    average_expense_per_customer_visit = customer_total_expense / customer_total_visits
    return average_expense_per_customer_visit


def unique_weeks(customer_id):
    """

    :param customer_id: str. Customer identifier
    :return: weeks_unique: dict. Unique weeks the customer visited
    """
    weeks_unique = {}
    for customer, visits in customer_visits.items():
        if customer == customer_id:
            for visit in visits:
                week_number = int(visit.strftime('%U'))
                if week_number not in weeks_unique:
                    weeks_unique[week_number] = True
            break
    return weeks_unique


def average_visits_per_week(customer_id):
    """

    :param customer_id: str. Customer identifier.
    :return: visit_avg_per_week: int. How many times a customer visits the website in a given week.
    """
    customer_total_visits = total_customer_visits(customer_id)
    customer_unique_weeks = len(unique_weeks(customer_id))
    visit_avg_per_week = int(math.ceil(customer_total_visits / customer_unique_weeks))

    return visit_avg_per_week


def average_customer_value_per_week(customer_id):
    """

    :param customer_id: str. Customer identifier
    :return: avg_ctv_per_week: float. The given customer's customer value per week

    """
    avg_ctv_per_week = average_visits_per_week(customer_id) * average_expenditure_per_customer_visit(customer_id)
    return avg_ctv_per_week


def simple_customer_lifetime_value(customer_id):
    """

    :param customer_id: str. Customer identifier
    :return: simple_ltv: float. Given customers simple lifetime value
    """
    simple_ltv = average_customer_value_per_week(customer_id) * 52 * AVERAGE_CUSTOMER_LIFESPAN
    return simple_ltv


def top_simple_ltv_customers(top):
    """

    :param top: int. Number of customers with highest simple LTV
    :return: sorted_customers: dict. Top x customers with their LTVs
    """
    customers_ltv = {}
    # Calculate LTVs for every customer visiting the website.
    for customer in customer_visits:
        customers_ltv[customer] = simple_customer_lifetime_value(customer)

    # Customer with highest LTV first.
    sorted_customers = sorted(customers_ltv.items(), key=operator.itemgetter(1), reverse=True)
    if len(sorted_customers) > top:
        return sorted_customers[:top]
    else:
        return sorted_customers


def ingest(event):
    """

    :param event: For each json object, add to the dictionary corresponding to it's type.
    :return: Nothing
    """
    if event['type'] == 'ORDER':
        order_id = event['key']
        action = event['verb']
        event_time = datetime.datetime.strptime(event['event_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
        customer_id = event['customer_id']
        total_amount = float(event['total_amount'].replace('USD', '').strip())

        if action == 'NEW':
            create_new_order(order_id, customer_id, event_time, total_amount)
        elif action == 'UPDATE':
            update_order(order_id, customer_id, event_time, total_amount)
        else:
            raise RuntimeError('Order event was raised but no action identified: {}'.format(action))

    if event['type'] == 'SITE_VISIT':
        page_id = event['key']
        event_time = datetime.datetime.strptime(event['event_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
        customer_id = event['customer_id']
        add_customer_visit(customer_id, event_time, page_id)


def parse_events(data):
    """

    :param data: given and array of nested json objects, separate each event 'type' to it's own dictionary.
    :return: Nothing
    """
    for event in data:
        ingest(event)


if __name__ == '__main__':

    """
    Calculate the simple LTV of top x customers.
    Assumptions:
    1. input is an array of nested json objects.
    2. type is case sensitive.
    3. For the same customer 2 page visits cannot occur at the same time.
    
    """

    customer_orders = {}
    customer_visits = {}
    customer_unique_weeks = {}
    AVERAGE_CUSTOMER_LIFESPAN = 10

    sample_json = [{"type": "SITE_VISIT",
                    "verb": "NEW",
                    "key": "ac05e815502f",
                    "event_time": "2017-01-01T12:45:52.041Z",
                    "customer_id": "1",
                    "tags": [{"some key": "some value"}]},
                   {"type": "SITE_VISIT",
                    "verb": "NEW",
                    "key": "ac05e815502f",
                    "event_time": "2017-01-01T12:45:52.041Z",
                    "customer_id": "2",
                    "tags": [{"some key": "some value"}]},
                   {"type": "SITE_VISIT",
                    "verb": "NEW",
                    "key": "ac05e815502f",
                    "event_time": "2017-01-02T12:46:52.041Z",
                    "customer_id": "3",
                    "tags": [{"some key": "some value"}]},
                   {"type": "SITE_VISIT",
                    "verb": "NEW",
                    "key": "ac05e815502f",
                    "event_time": "2017-01-14T12:48:52.041Z",
                    "customer_id": "1",
                    "tags": [{"some key": "some value"}]},
                   {"type": "ORDER",
                    "verb": "NEW",
                    "key": "68d84e5d1a43",
                    "event_time": "2017-01-06T12:55:55.555Z",
                    "customer_id": "1",
                    "total_amount": "12.34 USD"},
                   {"type": "ORDER",
                    "verb": "NEW",
                    "key": "68d84e5d1a45",
                    "event_time": "2017-01-07T12:55:55.555Z",
                    "customer_id": "2",
                    "total_amount": "5 USD"},
                   ]

    parse_events(sample_json)
    customer_id = '1'
    # print(pformat(customer_orders))
    # print(total_customer_expense('96f55c7d8f42'))
    # print(pformat(customer_visits))
    # print(total_customer_visits('1'))
    # print(average_expenditure_per_customer_visit('1'))
    # print('Unique weeks for customer {}:{}'.format(customer_id, len(unique_weeks(customer_id))))
    #print('Average customer visits per week: {}'.format(average_visits_per_week(customer_id)))
    # print('Average customer value per week: {}'.format(average_customer_value_per_week(customer_id)))
    print(pformat('Top 10 customer LTV: {}'.format(top_simple_ltv_customers(10))))

