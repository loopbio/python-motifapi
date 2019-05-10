def datetime_to_cron(dt):
    return '%d %d %d %d %d ?' % (dt.second, dt.minute, dt.hour, dt.day, dt.month)
