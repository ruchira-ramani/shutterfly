#https://github.com/sflydwh/code-challenge
#Solving for #2
# Test run
####################################################
#0 - rramani@C02R83K8G8WP: ~$ python shutterfly.py
#   customer_id  avg
#1            2  4420
#0            1  1820
####################################################


"""
Assumptions:
1. For each event, the headers would always be present even if the value is null
Example: you will always have field tags in site visit even if it is null
2. All amounts are in USD
3. You cannot place an order when you haven't visited the website
"""
import pandas as pd


def ingest(e, D):
    """
    For the given data, return only records belonging to event e

    Attributes:
        e: event name
        df: dataframe

     For the first run df that is returned is None, for subsequent runs you append to it
    """
    df1 = D.loc[D['type'] == e]
    try:
        df.append(df1)
    except (AttributeError, NameError) as error:
        df = df1
    return df


def merge_data(df1, df2, on, how, numerator=None, denominator=None):
    """
    combining two dataframes together. Emulates table join

    Attributes:
        df1: dataframe1
        df2: datafram2
        on: joining column
        how: which join
        numerator: numerator for the average
        denominator: denominator for the average

    """
    # Add 0 when the left join returns Nulls
    temp_table = pd.merge(df1, df2, on=on, how=how).fillna(0)
    if numerator and denominator:
        temp_table['avg'] = temp_table[numerator]/temp_table[denominator]
    return temp_table

def calculate_LTV(D):
    """
    A simple LTV can be calculated using the following equation: 52(a) x t.
    Where a is the average customer value per week (customer expenditures per visit (USD)
    multiplied by number of site visits per week)
    and t is the average customer lifespan. The average lifespan for Shutterfly is 10 years.

    Attributes:
        D: dataframe

    """
    # Extract Relevant events
    site_visits = ingest('SITE_VISIT', D)
    orders = ingest('ORDER', D)
    # removing currency code
    orders['total_amount'] = orders['total_amount'].str.replace('USD', '').astype(float)
    # Calculate customer expenditure per visit
    # Formula: (total amount spent by customer / total number of visits)
    total_expenses = orders.groupby('customer_id')['total_amount'].sum().reset_index(name='total_expenses')
    total_visits = site_visits.groupby('customer_id').size().reset_index(name='total_visits')
    avg_customer_expense = merge_data(total_visits, total_expenses, 'customer_id', 'left', 'total_expenses',
                                      'total_visits')[['customer_id', 'avg']]
    # Renaming columns
    avg_customer_expense.columns = ['customer_id', 'expense_per_week']
    # Calculate the number of visits per week
    # Formula: (total number of visits / number of active weeks)
    active_weeks = site_visits.groupby('customer_id').weekNumber.nunique().reset_index(name='active_weeks')
    avg_customer_visit = merge_data(active_weeks, total_visits, 'customer_id', 'inner', 'total_visits',
                                    'active_weeks')[['customer_id', 'avg']]
    avg_customer_visit['avg'] = avg_customer_visit['avg'].astype(int)
    # Renaming columns
    avg_customer_visit.columns = ['customer_id', 'visit_per_week']
    # Calculate average customer value per week
    avg_customer_value = merge_data(avg_customer_visit, avg_customer_expense, 'customer_id', 'inner')
    avg_customer_value['avg'] = avg_customer_value['visit_per_week']*avg_customer_value['expense_per_week']*52*10
    avg_customer_value = avg_customer_value[['customer_id', 'avg']]
    return avg_customer_value


def TopXSimpleLTVCustomers(x, D):
    """
    Return the top x customers with the highest Simple Lifetime Value from data D.

    Attributes:
        x: Number of customers to return
        D: dataframe

    """
    all_customers = calculate_LTV(D).sort('avg', ascending=False)
    return all_customers.head(x)


if __name__=='__main__':
    raw_data = pd.read_json('/shutterfly/input/input.txt')
    #raw_data = pd.read_json('[{"type": "ORDER", "verb": "NEW", "key": "1", "event_time": "2017-01-06T12:55:55.555Z", "customer_id": "1", "total_amount": "3.50 USD"},{"type": "ORDER", "verb": "NEW", "key": "2", "event_time": "2017-01-06T12:55:55.555Z", "customer_id": "2", "total_amount": "8.50 USD"},{"type": "SITE_VISIT", "verb": "NEW", "key": "1", "event_time": "2017-01-09T12:45:52.041Z", "customer_id": "1", "tags": [{"some key": "some value"}]},{"type": "SITE_VISIT", "verb": "NEW", "key": "1", "event_time": "2017-01-09T12:45:52.041Z", "customer_id": "1", "tags": [{"some key": "some value"}]},{"type": "SITE_VISIT", "verb": "NEW", "key": "1", "event_time": "2017-01-09T12:45:52.041Z", "customer_id": "1", "tags": [{"some key": "some value"}]},{"type": "SITE_VISIT", "verb": "NEW", "key": "1", "event_time": "2017-01-09T12:45:52.041Z", "customer_id": "1", "tags": [{"some key": "some value"}]},{"type": "SITE_VISIT", "verb": "NEW", "key": "2", "event_time": "2017-01-09T12:45:52.041Z", "customer_id": "2", "tags": [{"some key": "some value"}]},{"type": "SITE_VISIT", "verb": "NEW", "key": "2", "event_time": "2017-01-09T12:45:52.041Z", "customer_id": "2", "tags": [{"some key": "some value"}]},{"type": "SITE_VISIT", "verb": "NEW", "key": "2", "event_time": "2017-01-09T12:45:52.041Z", "customer_id": "2", "tags": [{"some key": "some value"}]}]')
    raw_data['weekNumber'] = raw_data['event_time'].apply(lambda x: x.week)
    TopXSimpleLTVCustomers(2, raw_data).to_csv('/shutterfly/output/output.txt', sep='\t', encoding='utf-8')
    #print(TopXSimpleLTVCustomers(2, raw_data))
