Syntax
------

### Basics ###

Each cron trigger is specified with a combination of six (or 7) white-space
separated fields that dictate when the event should occur. In order, the fields
specify trigger times for the second, minute, hour, day of the month,
month, day of the week, and the year (optional)

    .------------------ Second (0 - 59)
    |   .--------------- Minute (0 - 59)
    |   |   .------------ Hour (0 - 23)
    |   |   |   .--------- Day of the month (1 - 31)
    |   |   |   |   .------ Month (1 - 12) or Jan, Feb ... Dec
    |   |   |   |   |   .---- Day of the week (0 (Sun.; also 7) - 6 (Sat.))
    |   |   |   |   |   |   .- Year (optional) 
    V   V   V   V   V   V   V
    *   *   *   *   *   *   *

If the hour, minute, and month of a given time period are valid values as
specified in the trigger and _either_ the day of the month _or_ the day of the
week is a valid value, the trigger fires.

<!-- <TBD> -->

### Ranges and Wild-cards ###

Ranges specify a starting and ending time period. It includes all values from
the starting value to and including the ending value.

Wild-cards ("*") in a field represents all valid values.

The following cron expression is triggered every day at noon from June through
September:

    0 12 * 6-9 * *

If the day of the week field is a wild card, but the day of the month is an
explicit range, the day of the week will be ignored and the trigger will only
be activated on the specified days of the month. If the day of the month is a
wild card, the same principal applies.

This expression is triggered every week day at 4:00 PM: `0 16 * * 1-5 *`

This one is triggered the first nine days of the month: `0 16 1-9 * * *`

This one is triggered every day for the first week, but only on Saturdays
thereafter: `0 16 1-7 * 6 *`

### Steps ###

Steps are specified with a "/" and number following a range or wild-card. When
iterating through a range with a step, the specified number of values will be
skipped each time. `1-10/2` is the functional equivalent to `1,3,5,7,9`.

The following cron expression is triggered on the first day of every quarter
(Jan., Apr., ... Oct.) at midnight:

    0 0 1 */2 * *

<!-- </TBD> -->

### Monotonic Triggers ###

In typical cron implementations, setting the hour field to "*/9" would mean
cause it to match the hours 00:XX, 09:XX and 18:XX. The following day, pattern
would begin again starting from 00:XX making it impossible to easily define an
event that occurs every 9 hours. Monotonic triggers are Cronex's solution to
this problem; "%" in any field except the day of the week can be used to denote
expressions that should happen every N-intervals.

Monotonic expressions in the year, month and day field use calendar values. For
example, using "%15" in the day field with an epoch set to January 1st, 2017
would cause the days to match on January 1st, 16th and the 31st regardless of
the time zone.

As per default, monotonic expressions match always with 0, one can also
specify an offset. For example, the expression

    %7 * * ? * *

Triggers every 7 seconds, starting at 0 seconds, so triggers at :0, :7, :14,
etc. Whereas the monotonic trigger with offset 7

    7%7 * * ? * *
 
triggers at :7, :14, :21, etc

