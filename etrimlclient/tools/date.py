
from datetime import datetime, timedelta


# convert rfc 3339 time string into a datetime object that represents time in UTC
def to_utc(date_str: str, format_str="%Y-%m-%dt%H:%M:%S.%fz"):
    """ convert rfc 3339 time string into a datetime object that represents time in UTC

    Args:
        date_str (str): date string in rfc 3339 format, like "2015-09-15T17:13:29.380Z"

    Returns:
        datetime: UTC time
    """
    utc_time = datetime.strptime(date_str, format_str)
    return utc_time


def unix_timestamp(date_str: str, format_str="%Y-%m-%dt%H:%M:%S.%fz"):
    """convert rfc 3339 time string into timestamps

    Args:
        date_str (str): date string in rfc 3339 format, like "2015-09-15T17:13:29.380Z"
        format_str (str, optional):  Defaults to "%Y-%m-%dT%H:%M:%S.%fZ".

    Returns:
        float: timestamp
    """
    milliseconds = (to_utc(date_str, format_str) -
                    datetime(1970, 1, 1)) // timedelta(milliseconds=1)
    return milliseconds


if __name__ == "__main__":
    print(unix_timestamp("2019-03-28t16:00:00.000z"))
