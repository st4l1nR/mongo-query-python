import re
from datetime import datetime
from urllib.parse import parse_qs


def is_iso_date(date_str):


    try:
        pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$'
        if not bool(re.match(pattern, date_str)):
            return False
        datetime.strptime(date_str[:-1], '%Y-%m-%dT%H:%M:%S.%f')
        return True
    except (ValueError, TypeError):
        return False


def is_string_number(string):
    try:
        float(string)
        return True
    except (ValueError, TypeError):
        return False


def mongo_query(q):
    query_object = parse_qs(q, keep_blank_values=True)
    output_dict = {}

    for key, value in query_object.items():
        # Remove '[]' characters from the key
        key = key.replace('[]', '')

        # Convert arrays with a single element to a single value
        if len(value) == 1:
            value = value[0]

        output_dict[key] = value
    query_array = []

    for key, value in output_dict.items():

        if (is_iso_date(value)):
            value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        if (is_string_number(value)):
            value = int(value)
        if key == 's':
            query_array.append({'$text': {'$search': value}})
        elif isinstance(value, list):

            if '.' in key:
                embed_entries = key.split('.')
                query_array.append({embed_entries[0]: {'$elemMatch': {
                                   embed_entries[1]: {'$gte': value[0], '$lte': value[1]}}}})
            elif is_iso_date(value[0]):
                query_array.append({key: {'$gte': datetime.strptime(
                    value[0], "%Y-%m-%dT%H:%M:%S.%fZ"), '$lte': datetime.strptime(value[1], "%Y-%m-%dT%H:%M:%S.%fZ")}})
            else:
                query_array.append(
                    {key: {'$gte': int(value[0]), '$lte': int(value[1])}})
        elif '/' in key:
            if '!' in key:
                query_array.append({key.replace('!/', ''): {'$nin': [value]}})
            else:
                query_array.append({key.replace('/', ''): {'$in': [value]}})
        elif '*' in key:
            values = value.split(',')
            print(values)
            if '!' in key:
                query_array.append({key.replace(
                    '!*', ''): {'$all': [{'$elemMatch': {'$ne': val}} for val in values]}})
            else:
                query_array.append({key.replace('*', ''): {'$all': values}})
        elif '^' in key:
            if '!' in key:
                query_array.append({key.replace('!^', ''): {'$lte': value}})
            else:
                query_array.append({key.replace('^', ''): {'$gte': value}})
        elif 'v' in key:
            if '!' in key:
                query_array.append({key.replace('!v', ''): {'$gte': value}})
            else:
                query_array.append({key.replace('v', ''): {'$lte': value}})
        elif '!' in key:
            query_array.append(
                {key.replace('!', ''): {'$ne': None if value == 'null' else value}})
        else:
            query_array.append({key: None if value == 'null' else value})

    query = {}
    for item in query_array:
        query.update(item)

    return query


query_string = 's=A text search&total=1&name!=banned&price[]=11&price[]=50&schedule.start_at^=2023-05-09T15:30:00.000Z&schedule.end_atv=2023-05-09T15:30:00.000Z&schedule.medium_at=2023-05-09T15:30:00.000Z'
query = mongo_query(query_string)
print(query) # {'$text': {'$search': 'A text search'}, 'total': 1, 'name': {'$ne': 'banned'}, 'price': {'$gte': 11, '$lte': 50}, 'schedule.start_at': {'$gte': datetime.datetime(2023, 5, 9, 15, 30)}, 'schedule.end_at': {'$lte': datetime.datetime(2023, 5, 9, 15, 30)}, 'schedule.medium_at': datetime.datetime(2023, 5, 9, 15, 30)}