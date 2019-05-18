Python API for Motif Recording Systems
======================================

This library allows you to control cameras and recording on loopbio [motif](http://loopbio.com/recording)
recording systems, including the ability to control outputs and schedule operations. This allows
you to implement experimental or operational protocols like;

 * "start recording every hour for 30 minues. while recording give this stimulus (switch this output)
    every 5 minutes"
 * "record at 9am and 3pm. at 5pm copy all recorded videos to network storage"
 * "while recording, at minute 1 switch this output on, then every 30 seconds thereafter, switch on and
    off this other output"

**Table of Contents**

 * [Examples](#examples)
 * [Examples (IO and Scheduling)](#scheduling-examples)
 * [API Documentation](#api-documentation)
 * [Scheduling](#scheduling-function)
 * [API Documentation (Scheduling)](#scheduling-api-documentation)
 * [Realtime Streaming](#realtime-streaming)

## Getting Started

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
* this library is compatible with all motif versions, although real-time image streaming and
  some IO operations are only supported in motif 5 and above

### Examples

Set up the connection to the machine

```python
from motifapi import MotifApi

IP_ADDRESS = '10.11.12.23'
API_KEY = 'abcdef123456abcdef123456abcdef12'

api = MotifApi(IP_ADDRESS, API_KEY)
# check the client is connected
api.call('version')
# list the connected cameras
api.call('cameras')
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

## API Documentation

The complete list of API endpoints/paths, as passed to `call(path, **arguments)`,
can be found below. Text between `<` and `>` characters should be replaced
with the appropriate values. Arguments are passed after the path, e.g.
`api.call('recording/start', duration=5.0)`.

 * `version`
   * return the current software version
 * `cameras`
   * return a list of connected cameras and their status
 * `camera/<serial>`
   * returns the selected camera status
   * `serial`: the serial number of the camera
 * `camera/<serial>/configure`
   * change camera configuration
   * `serial`: the serial number of the camera
   * arguments (for example, optional)
     * `AcquisitionFrameRate`: change the framerate of the camera
     * `ExposureTime`: exposure time in us
     * `...` or any other camera supported parameter name and value
 * `cameras/configure`
   * as previous, but apply the configuration changes to every attached camera
 * `camera/<serial>/recording/start`
   * start recording on the selected camera
   * `serial`: the serial number of the camera
   * arguments
     * `filename` (optional): recording filename (excluding timestamp)
     * `record_to_store` (optional)
       * `True`
       * `False`
       * no argument provided: use configured defaults
     * `codec` (optional): code identifier or use configured default (if omitted)
     * `duration` (optional): number of seconds to record for, or indefinately if omitted
     * `metadata` (optional): a dictionary of metadata to save in the resulting video
 * `recording/start`
   * as previous, but start recording on all cameras
 * `camera/<serial>/recording/stop`
   * stop recording on the selected camera
   * `serial`: the serial number of the camera
 * `recording/stop`
   * as previous, but stop recording on all cameras
 * `camera/<serial>/recordings`
   * return a list of recordings
   * `serial`: the serial number of the camera
 * `recordings`
   * as previous, but return recordings for all cameras
 * `camera/<serial>/recordings/copy_all`
   * copy (or move) all currently completed recordings to another location
   * `serial`: the serial number of the camera
   * arguments
     * `location` (optional): local user path or if omitted, default configued location
     * `delete_after` (optional, default=False): delete original recordings after successful copy
     * `loopy_username` (optional)
     * `loopy_url` (optional)
     * `loopy_api_key` (optional)
     * `loopy_import_base` (optional)
     * connection details of accesibly self hosted loopy instance for automatic
       importing of videos into loopy after copy finishes
 * `recordings/copy_all`
   * as previous, but copy recordings from all cameras
 * `camera/<serial>/recordings/export_all`
   * export image stores to normal mp4 videos (or image stores)
   * `serial`: the serial number of the camera
   * arguments
     * `to_store` (optional)
       * `True`
       * `False`
       * no argument provided: use configured defaults
     * `codec` (optional)
     * `delete_after` (optional)
     * `path` (optional)
 * `recordings/export_all`
   * as previous, but export image stores from all cameras
 * `camera/<serial>/io/<name>/set`
   * set named output associated with camera to provided value
   * `serial`: the serial number of the camera
   * `name`: the name of the configured output channel
   * arguments
     * `value`: the value to set on the output (backend dependent)
 * `io/<name>/set`
   * set named ouput to the provided value. in index or master mode in
     a multiple camera setup, the named output channel must be on a
     output device attached to the master or index node.
     setup (or to the only attached camera in a single camera setup) 
   * `name`: the name of the configured output channel
   * arguments
     * `value`: the value to set on the output (backend dependent)
 * `io/<io_serial>/<io_port>/set` (DEPRECATED)
   * configure and set output to provided value
   * `io_serial`: serial number of IO device
   * `io_port`: port on device to set
   * arguments
     * `value`: continuous value to set OR
     * `state`: 0 or 1 to turn on or off

**Outputs and Toggling Values**

There exists a special value for (digital) outputs that results in the output state being
toggled (alternating) between minimum and maximum values. If you pass `value=+inf` then this means
start with a switch to maximum, then toggle between minimum and maximum subsequently. `value=-inf`
start with a switch to minimum, then toggle between maximum and minimum subsequently.

## Scheduling Function

Motif allows scheduling of almost all previously documented API operations.
Scheduling allows executing a certain operation as a defined time. 

This allows for example, to schedule recordings and their subsequent copy
to storage to occur at specific times. Task scheduling re-uses [Cron syntax]()
with some extensions. 

### Cron Syntax

Please refer to [here](README.cronex.md) for a complete specification and more examples.

Each scheduled operation is specified with a combination of six white-space
separated fields that dictate when the event should occur. In order, the fields
specify trigger times for the second, minute, hour, day of the month,
month and day of the week.

    .------------------ Second (0 - 59)
    |   .--------------- Minute (0 - 59)
    |   |   .------------ Hour (0 - 23)
    |   |   |   .--------- Day of the month (1 - 31)
    |   |   |   |   .------ Month (1 - 12) or Jan, Feb ... Dec
    |   |   |   |   |   .---- Day of the week (0 (Sun.; also 7) - 6 (Sat.))
    |   |   |   |   |   |
    V   V   V   V   V   V
    *   *   *   *   *   *

### Scheduling API Documentation

The API for scheduling tasks is very similar to that of other tasks - API endpoints are
prefixed with `schedule/VERB` may/should be passed additional optional or
compulsory arguments.

**Scheduling specific arguments**

   * `task_name` (required): A unique shor identifier for this task
   * `cron_expression` (required): a cron specifier conforming to the cron syntax above
   * `camera_relative` (optional, Motif 5 and above only)
     * `True`: if true all absolute and relative dates are relative to the start of the recording
     * `False` (default): all dates are absolute, and monotonic expressions are relative to 1-Jan-1970

**Camera Relative Schedules**

Please ensure you have read the [full documentation](README.cronex.md) on cron triggers first. Often one needs to schedule events not in the conventional cron sense - relative to the date and time of the day, but instead wants to schedule operations relative to when a recording was started. If a task is scheduled with `camera_relative=True` then dates are interpreted differently. For example the expression

 * `0 5 * ? * * *`
   * with `camera_relative=False` means execute the task *at second :00 of minute :05 of every hour*
     * e.g. Fri May 17 16:05:00 UTC 2019, Fri May 17 17:05:00 UTC 2019, Fri May 17 18:05:00 UTC 2019
   * with `camera_relative=False` means execute the task *at second :00 of minute :05 of every hour* relative to when recording was started.
     * e.g., for a recording started at Fri May 17 13:14:00 UTC 2019, the task would trigger at Fri May 17 13:19:00 UTC 2019, Fri May 17 14:19:00 UTC 2019, etc.

With monotonic triggers `7%7` or `%10` this can be confusing. Monotonic triggers execute *every unit of time*. For example the expression

 * `0 * %2 ? * * *`
    * with `camera_relative=False` means *execute every 2 hours starting at 00:00:00*
      * e.g. Fri May 17 00:00:00 UTC 2019, Fri May 17 02:00:00 UTC 2019
    * with `camera_relative=True` means *execute every 2 hours starting at the time of recording start*
       * e.g., for a recording started at Fri May 17 13:14:00 UTC 2019, the task would trigger at Fri May 17 15:14:00 UTC 2019, Fri May 17 17:14:00 UTC 2019, etc.

**API (continued)**

 * `schedule`
   * list all scheduled tasks, return also including the current time on
     the system
 * `schedule/clear`
   * delete all scheduled tasks
 * `schedule/<task_name>/clear`
   * delete the provided task
   * `task_name`: the identifier of the task to clear 
 * `schedule/camera/<serial>/recording/start`
   * schedule the start of recording on the selected camera
   * `serial`: the serial number of the camera
   * arguments
     * scheduling specific (above), excluding `camera_relative`
     * see `recording/start` (above)
 * `schedule/recording/start`
   * as previous, but schedule the start of recording on all cameras
 * `schedule/camera/<serial>/recordings/copy_all`
   * schedule copy (or move) of recordings
   * `serial`: the serial number of the camera
   * arguments
     * scheduling specific (above), excluding `camera_relative`
     * see `recordings/copy_all` (above)
 * `schedule/recordings/copy_all`
   * as previous, but schedule copy (or move) of recordings on all cameras
 * `schedule/camera/<serial>/recordings/export_all`
   * schedule export of recordings on the selected camera
   * `serial`: the serial number of the camera
   * arguments
     * scheduling specific (above), excluding `camera_relative`
     * see `recordings/export_all`
 * `schedule/recordings/export_all`
   * as previous, but schedule export of recordings on all cameras
 * `schedule/camera/<serial>/configure/<name>`
   * schedule the change of a camera configuration
   * `serial`: the serial number of the camera
   * `name`: the the name of the parameter to change (e.g. `ExposureTime`)
   * arguments
     * scheduling specific (above)
     * `value` (required): the new value of the parameter
 * `schedule/cameras/configure/<name>`
   * as previous, but schedule the change of camera configuration on all cameras
 * `schedule/camera/<serial>/io/<name>/set`
   * schedule the setting of a named output, on an IO device connected to the
     supplied camera, to a provided value
   * `serial`: the serial number of the camera
   * `name`: the name of the configured output channel
   * arguments
     * scheduling specific (above)
     * `value` (required): the new value of the parameter
 * `schedule/io/<name>/set`
   * schedule the setting of the named ouput to the provided value.
     in index or master mode in a multiple camera setup, the named output
     channel must be on a output device attached to the master or index node.
   * arguments
     * scheduling specific (above)
     * `value` (required): the new value of the parameter

## Scheduling Examples

To schedule a 30 minute recording as configured above
to be executed every-hour-on-the-hour between 9am and 4pm, make the following API call

```python
api.call('schedule/recording/start',
         task_name='record_video',
         cron_expression='0 6-16 * * * *',
         duration=30*60)
```

*** FAQ ***

* Q) What if Motif is running on another computer? how to I find the time on the system

```python
now = api.call('schedule')['now']
dt = datetime.datetime.fromtimestamp(now)
```

 * Q) What is the easiest way to schedule something to happen 'some time from now'
 
 ```python
# following from the example above
import datetime
from motifapi import datetime_to_cron
future = dt + datetime.timedelta(seconds=30)
api.call('schedule/recording/start',
         task_name='record_video_in_30s_time',
         cron_expression=datetime_to_cron(future),
         duration=30*60)
 ```

**See examples/scheduler.py for more information**

## Realtime Streaming

Motif can, with very low latency (&lt;1ms), stream realtime images from the camera, without interfering with
the recording, compression, or any other motif functions. This allows developing *out of process* realtime
image processing algorithms for closed loop experiments. Such experiments could for example then provide
stimulus to the animal using either Motif connected and configured outputs, or other user provided methods.

Per default streaming is limited to localhost (so such scripts must run on the same PC as Motif), however
Motif can be configured to stream also to other network locations if you are aware of the latency
implications and have sufficient network infrastructure.

### Streaming Images

A realtime image stream can be established as follows (after constructing the `api` object with the correct IP address and API_KEY as indicated above

```python
# small example using opencv to show the image in realtime, outside of motif

stream = api.get_stream(stream_type=MotifApi.STREAM_TYPE_IMAGE)
if stream is not None:
    while True:
        I, md = stream.get_next_image()
        cv2.imshow('live', I)
        cv2.waitKey(1)
```

### Streaming State

If you have other more custom data acquisition needs not supported by Motif IO / DAQ support, and want to subsequently 
integrate or synchronize this custom data with the motif imagestore `frame_number`s and `frame_time`s then you can use the realtime state streaming. Motif publishes to this stream, at low latency (&lt;&lt;1ms), the current `frame_number`, `frame_time`, and other information. A realtime state stream is established as follows

```python
stream = api.get_stream(stream_type=MotifApi.STREAM_TYPE_STATE)
if stream is not None:
    while True:
        print stream.get_next_state()
```

## Other Languages

The API is a pure REST api, which means any language / framework / environment with support for calling REST+JSON endpoints and handling their responses is supported.

Note: You must provide the HTTPS server certificate and authenticaion API key in a manner appropriate for your language / framework / environment.

### Example Use From MATLAB

Note: Examples for the hypothetical IP address and API_KEY listed in the first example. Please replace with your own
Note: `server.crt` must be the full path to the `server.crt` file in this repository

```matlab
% example showing how to list connected cameras from MATLAB
o = weboptions('CertificateFilename', 'server.crt', ...
               'HeaderFields', {'X-Api-Key', 'abcdef123456abcdef123456abcdef12'})
# list the connected cameras
webread('https://10.11.12.23:6083/api/1/cameras', o)
```

```matlab
% example showing how to set an output using a POST request
o = weboptions('CertificateFilename', 'server.crt', ...
               'HeaderFields', {'X-Api-Key', 'abcdef123456abcdef123456abcdef12'}, ...
               'MediaType', 'application/json')
arguments = struct('value',0.3);
webwrite('https://127.0.0.1:6083/api/1/io/led/set',arguments,o)
```

Note: not all endpoints are `POST`, although most are. The endpoint type is documented in `motifapi/api.py`
