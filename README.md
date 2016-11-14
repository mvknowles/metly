Metly
=====

*WARNING: THIS CODE IS UNDER HEAVY DEVELOPMENT.  IT's LIKELY TO BLOW UP YOUR HOUSE AND EAT YOUR CAT.*

Metly is an Open Source tool for collecting "metadata".  Metadata includes many
things, including internet logs, syslog, telephone logs and email logs.  The
sky is the limit.

Metly is designed to scale to a massive size.  That's why it's split up into 3
components:
* Collector (Collects metadata - such as a syslog listener)
* Web (Allows you to analyse metadata)
* Daemon (Stores metadata and acts as the glue between all the components)

The following technologies are in use:
* Bootstrap
* Apache Phoenix
* Hadoop
* CherryPy
* SQLAlchemy

Here's a screenshot that shows the basic end results:

![search results](https://cloud.githubusercontent.com/assets/23462962/20283480/1bbec27a-ab1e-11e6-859f-b12610f0d922.png)

Getting Started
---------------

Download the code
    git clone https://github.com/mvknowles/metly.git

Start the daemon:
    cd ${PROJECT_HOME}/metly
    ./scripts/rundaemon --clean

Start the webserver
    cd ${PROJECT_HOME}/metly
    ./scripts/runweb --clean

At this stage it will say the webserver is not authorized.  It will supply a
UUID.  That's cool, we just need to tell the daemon about the new web server.
    cd ${PROJECT_HOME}
    ./metly/daemon/metlycmd -aw ${INSERT_UUID}

Start the collector
    cd ${PROJECT_HOME}/metly
    ./scripts/runcollector --clean

At this stage the collector will say it's not authorized.  Now we need to load
up the web server to authorize the collector.

Open up https://localhost:4443
Username: mark
Password: test

Click Admin -> Collectors
Click Add New Collector
Insert the UUID, click next, then enter a description

Next, define a syslog listener.
Click Admin -> Metadata Sources
Click "New MetaData Source"
Enter a name and a port
Click Add

You should now be able to point syslog traffic at your collector.

To see if results are coming through, enter the following query in the
quick search box at the top:
    select message from logs


More Screenshots:
-----------------

![search list](https://cloud.githubusercontent.com/assets/23462962/20283485/1c1d114a-ab1e-11e6-9a8c-125b966c7211.png)
![user list](https://cloud.githubusercontent.com/assets/23462962/20283484/1c1cfaa2-ab1e-11e6-9bf0-f69b0c36a83b.png)
![add new collector](https://cloud.githubusercontent.com/assets/23462962/20283487/1c238a66-ab1e-11e6-8656-c9f6025b7388.png)
![collectors list](https://cloud.githubusercontent.com/assets/23462962/20283483/1c1cbd30-ab1e-11e6-8bd3-74db076f4922.png)
![add new metadata source](https://cloud.githubusercontent.com/assets/23462962/20283486/1c21aade-ab1e-11e6-8b1b-72909fed6704.png)
![metadata sources](https://cloud.githubusercontent.com/assets/23462962/20283481/1bf39eb4-ab1e-11e6-9f74-b602cafe4968.png)
![new service request](https://cloud.githubusercontent.com/assets/23462962/20283488/1c2874ae-ab1e-11e6-9cb0-57079f1f48c7.png)
