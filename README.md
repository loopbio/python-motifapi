Python API for Motif Recording Systems
======================================

This library allows you to control cameras and recording on loopbio motif recording
systems.

Getting Started
---------------

* this library works out of the box on Python2 and Python3 and has no dependencies outside
  of the standard library
* to control a motif recording system you need to know it's IP address and an API key.
  * the IP address is that which you browse to inorder to control the recording software
    using your web browser
  * the API key is specific to the installation of the recording software and secures the
    API from unauthorized access. To find the API key for the recording system you wish to
    control, SSH into the machine (or request your sysadmin to) and execute the following
    command `recnode-apikey`
* this library wraps the REST+JSON API and handles sending and parsing the responses

Examples
--------

Set up the connection to the machine

```python

from motifapi import MotifApi


IP_ADDRESS = '10.11.12.23'
API_KEY = 'abcdef123456abcdef123456abcdef12'

api = MotifApi(IP_ADDRESS, API_KEY)
# check the client is connected
api.call('version')
```

To start recording on all cameras with the predefined compression settings named 'high'
(see the web UI for the names of your configured compression formats). The recording will run
for 5 seconds and will have have the following metadata attached.

```python
api.call('recording/start',
         codec='high',
         duration=5,
         metadata={'foo': 1, 'bar': 'bob'})
```

To stop all recordings on all cameras

```python
api.call('recording/stop')
```

To configure one camera and start recording on it alone

```python
api.call('camera/FAKE0/configure', Gain=0))
api.call('camera/FAKE0/recording/start', codec='low')
```

Cameras are identified by their serial number ('FAKE0' in the example above). To find the serial
numbers of connected cameras do

```python
api.call('cameras')
```

To find the status of a camera (is it recording, uploading, etc) do

```python
api.call('camera/FAKE0')
```

**See `examples/*.py` for further examples of API usage**

Scheduling
----------

The API also supports defining scheduled tasks, this allows for example, to schedule recordings
and their subsequent copy to storage to occur at specific times.

Task scheduling re-uses [Cron syntax]() with some extensions. Specifically it utilises
the [Cronex](https://github.com/ericpruitt/cronex/blob/057509738a86ea70bddbfe853736fa4ef6f67f3b/README.md) library
and supports the formats mentioned there (including monotonic tasks with `%` markup). All times are
in local-time of the machine running the recording software.

To list currently scheduled tasks (and the current machine time)

```python
print(api.call('schedule'))
```

The API for scheduling tasks is very similar to that of other tasks - API endpoints are
prefixed with `schedule/VERB` and require passing two compulsory additional parameters,
`task_name` and `cron_expression`. For example, to schedule a 30 minute recording as configured above
to be executed every-hour-on-the-hour between 9am and 4pm, make the following API call

```python
api.call('schedule/recording/start', task_name='record_video', cron_expression='0 06-16 * * *',
                                     codec='low', duration=30*60)
```

**See examples/scheduler.py for more information**
