var __index = {"config":{"lang":["en","de"],"separator":"[\\s\\-]+","pipeline":["stopWordFilter"]},"docs":[{"location":"index.html","title":"Welcome to the NOW - Learning Management System documentation.","text":"<p>The main objetive of NOW - LMS is to be a simple to {install, use, configure, mantain} learning management system (LMS).</p> <p></p> <p>Online education can be used as a primary source of knowledge or as a reinforcement method.</p> <p>This is alpha software!</p>"},{"location":"index.html#first-steps","title":"First Steps","text":"<p>NOW-LMS is available as a Python Package in Pypi, to run it you just have a recent Python interpreter and run the following commands:</p> <pre><code># Python &gt;= 3.8\n\n# Linux or Mac:\npython3 -m venv venv\nsource venv/bin/activate\n\n# Windows\npython3 -m venv venv\nvenv\\Scripts\\activate.bat\n\n# Inside your python virtual env:\n\npython -m pip install now_lms\npython -m now_lms\n</code></pre> <p>Visit <code>http://127.0.0.1:8080</code> in your browser and login with the default user and password: <code>lms-admin</code>.</p> <p>This will install NOW - LMS from the Python Package Index with a local WSGI server and SQlite as database backend, for really tiny septups or testing this can work, for a most robust deployment suitable for many users refers to the setup guide.</p> <p>NOW-LMS aims to offers a full online learning experience and is influenced by others project.</p>"},{"location":"CONTRIBUTING.html","title":"Contributing with NOW Learning Management System.","text":"<p>Thank you for your interest in collaborating with NOW Learning Management System. (the project).</p>"},{"location":"CONTRIBUTING.html#project-license","title":"Project License.","text":"<p>NOW LMS is free and open source software released under the Apache Version 2 license (the license of the proyect), this means that project users can:</p> <ul> <li>Use the project for profit or not.</li> <li>Modify the project to fit theirs specific needs (clearly defining the changes made to the original project).</li> </ul> <p>However, users cannot:</p> <ul> <li>Make use of the project trademarks without explicit permission.</li> <li>Require warranties of any kind; the project is distributed as is without guarantees that it may be useful for any specific purpose.</li> </ul>"},{"location":"CONTRIBUTING.html#certify-the-origin-of-your-contributions","title":"Certify the origin of your contributions.","text":"<p>To incorporate your contributions to the project we require that you certify that the contribution or contributions are your property or that you have permission from third parties to incorporate the contribution or contributions to the project, following the developer certificate of origin.</p> <p>We recommend running:</p> <pre><code>git commit -s\n</code></pre> <p>And an appropriate signature will be added to the commit, not included in the commits project without the corresponding Sing-Off.</p>"},{"location":"CONTRIBUTING.html#collaborating-with-the-project","title":"Collaborating with the project:","text":""},{"location":"CONTRIBUTING.html#ways-to-collaborate","title":"Ways to collaborate.","text":"<p>You can collaborate in different ways:</p> <ul> <li>As a developer.</li> <li>As a Quality Assurance (QA).</li> <li>Writing and improving documentation.</li> <li>Contributing ideas of new characteristics.</li> <li>Reporting bugs.</li> <li>Translating.</li> <li>Providing guidance and support to other users.</li> <li>Sharing the project with others.</li> </ul>"},{"location":"CONTRIBUTING.html#collaborating-with-the-development-of-the-project","title":"Collaborating with the development of the project:","text":"<p>The development is cross-platform, you can use both Windows, Linux or Mac to contribute the project, to collaborate with the project you need:</p> <ul> <li>Git.</li> <li>NPM.</li> <li>Python.</li> </ul> <p>Minimal Python version is: &gt;=3.7</p> <p>Technologies used:</p> <ul> <li>Backend: Flask, with a set of many libraries:</li> <li>flask-babel</li> <li>flask-caching</li> <li>flask-login</li> <li>flask-mde</li> <li>flask-reuploaded</li> <li>flask-sqlalchemy</li> <li>flask-wtf</li> <li>Frontend: Bootstrap 5.</li> <li>ORM: SQLAlchemy:</li> <li>flask-alembic</li> </ul> <p>Other libraries used in the project are:   - appdirs: App directories.   - bleach: HTML sanitisation.   - configobj: Configuration files parser.   - bcrypt: Password hashing.   - loguru: Logging.   - markdown: Render markdown as HTML.   - python-ulid: Generate uniques id.   - waitress: WSGI server.</p> <p>Development is done in the branch <code>development</code>, once the project is released for production the branch <code>main</code> will contain the latest version suitable for use in production.</p>"},{"location":"CONTRIBUTING.html#getting-the-source-code","title":"Getting the source code","text":"<pre><code>git clone https://github.com/bmosoluciones/now-lms.git\n</code></pre>"},{"location":"CONTRIBUTING.html#create-a-python-virtual-env","title":"Create a python virtual env","text":"<pre><code>python3 -m venv venv\n# Linux:\nsource venv/bin/activate\n# Windows\nvenv\\Scripts\\activate.bat\n</code></pre>"},{"location":"CONTRIBUTING.html#install-python-deps","title":"Install python deps","text":"<pre><code>python3 - m pip install -r development.txt\n</code></pre>"},{"location":"CONTRIBUTING.html#install-boostrap","title":"Install Boostrap","text":"<pre><code> cd now_lms/static/\n npm install\n cd ..\n cd ..\n</code></pre>"},{"location":"CONTRIBUTING.html#start-a-development-server","title":"Start a development server","text":"<pre><code>hupper -m now_lms\n</code></pre> <p>Please note that we use waitress as WSGI server because gunicorn do not works on Windows, hupper will live reload the WSGI server as you save changes in the source code so you will be able to work with your changes as you work, please note that changes to the jinja html templates will not trigger the server reload, only changes to python files.</p> <p>Default user and password are <code>lms-admin</code>, default url to work with the server will be <code>http://127.0.0.1:8080/</code>.</p> <p>You can disable the default cache service with:</p> <pre><code>NO_LMS_CACHE=True hupper -m now_lms\n</code></pre>"},{"location":"CONTRIBUTING.html#style-guide","title":"Style Guide:","text":"<p>PEP8 with a maximum line length of 127 characters.</p>"},{"location":"CONTRIBUTING.html#database-support","title":"Database Support","text":"<p>These database are supported:</p> <ul> <li>SQLite</li> <li>Postgres</li> <li>MySQL</li> </ul> <p>These database should work:</p> <ul> <li>MariaDB</li> </ul>"},{"location":"CONTRIBUTING.html#sqlite","title":"SQLite","text":"<p>SQLite works out of the box, to test NOW - LMS with SQLite just run:</p> <pre><code>python -m pytest  -v --exitfirst --cov=now_lms\n</code></pre>"},{"location":"CONTRIBUTING.html#postgres","title":"Postgres","text":"<p>To test NOW - LMS with Postgres follow this steps:</p> <pre><code>sudo dnf install postgresql-server postgresql-contrib\nsudo postgresql-setup --initdb --unit postgresql\nsudo systemctl start postgresql\nsudo -u postgres psql\npostgres=# CREATE USER postgresdb WITH PASSWORD 'postgresdb';\npostgres=# CREATE DATABASE postgresdb OWNER postgresdb;\npostgres=# \\q\n</code></pre> <p>Allow connet with user and password:</p> <pre><code>sudo gedit /var/lib/pgsql/data/pg_hba.conf\nAnd edit host all all 127.0.0.1/32 ident to host all all 127.0.0.1/32 md5\n</code></pre> <p>Run the test with postgres:</p> <pre><code>DATABASE_URL=postgresql://postgresdb:postgresdb@127.0.0.1:5432/postgresdb pytest  -v --exitfirst --cov=now_lms\n</code></pre>"},{"location":"CONTRIBUTING.html#mysql","title":"MySQL","text":"<p>To test NOW - LMS with MySQL follos this steps:</p> <pre><code>sudo dnf install community-mysql-server -y\nsudo systemctl start mysqld\nsudo mysql_secure_installation\nsudo mysql -u root -p\nCREATE USER 'mysqldatabase'@'localhost' IDENTIFIED BY 'mysqldatabase';\nCREATE DATABASE mysqldatabase;\nGRANT ALL PRIVILEGES ON mysqldatabase.* TO 'mysqldatabase'@'localhost';\nFLUSH PRIVILEGES;\n</code></pre> <p>For the most the users, this script will work fine but if it asks you for the password, you can retrieve a temporary password from mysqld.log at /var/log/ by the given command:</p> <pre><code>sudo grep 'temporary password' /var/log/mysqld.log\n</code></pre> <p>Now you can test NOW - LMS with MySQL running:</p> <pre><code>DATABASE_URL=mysql://mysqldatabase:mysqldatabase@127.0.0.1:3306/mysqldatabase pytest  -v --exitfirst --cov=now_lms\n</code></pre>"},{"location":"db.html","title":"Database setup","text":""},{"location":"dev_ops.html","title":"Other deployment options","text":"<p>There are templates available to deploy Now - LMS to these [PAID] services:</p> <p> </p>"},{"location":"dev_ops.html#render","title":"Render","text":"<p>On render you can host NOW-LMS for free, just set your project settings as follow:</p> <pre><code>Build Command: pip install -r requirements.txt &amp;&amp; cd now_lms/static/ &amp;&amp; npm install\nStart Command: python -m now_lms\n</code></pre> <p>Important: You can test NOW-LMS for free on Render, but with the default configuration NOW LMS will use a SQLite database as data store, this database is not goin to persist after system upgrades, to keep your data safe ve sure to set the next enviroment variables:</p> <pre><code>DATABASE_URL=proper_db_connet_string\n</code></pre> <p>Note that you can host a tiny up to 20MB PostgreSQL database for free in elephantsql.</p>"},{"location":"dreamhost.html","title":"Install NOW - LMS in DreamHost shared host.","text":"<p>NOW - Learning Management System can be hosted at DreamHost shared hosting service, this is usefull if you alredy have a host plan in DreamHost and you want to serve a few users, in a shared hosting enviroment there will be some limitations like no separate cache service or memory constraints, but if you alredy have a host plan in DreamHost adding NOW - Learning Management System  can be handy.</p> <p>Last update: 2023 Nov 01</p> <ol> <li> <p>Setup your domain with Passenger support.</p> </li> <li> <p>Login via SSH to your host.</p> </li> <li> <p>Check your python3 version:</p> </li> </ol> <pre><code>$ cat /etc/issue\nUbuntu 20.04.6 LTS\n$ python3 --version\nPython 3.8.10\n\n</code></pre> <p>You need Python &gt;= 3.8 in order to run NOW - LMS, with the current version of Python available in DreamHost you can run a NOW - LMS instance.</p> <ol> <li>Go to your domain folder:</li> </ol> <pre><code>$ cd your.domain\n</code></pre> <ol> <li>Create a python virtual enviroment:</li> </ol> <pre><code>$ virtualenv venv\n$ ls\npublic  venv \n</code></pre> <ol> <li>Activate the virtual env:</li> </ol> <pre><code>$ source venv/bin/activate\n</code></pre> <ol> <li>Install NOW - LMS:</li> </ol> <pre><code>$ pip install now_lms\n</code></pre> <ol> <li>Go to the public directory in your.domain directory:</li> </ol> <pre><code>$ cd public\n</code></pre> <ol> <li>Create a app.py file following this template:</li> </ol> <pre><code>$ touch app.py\n</code></pre> <p>app.py template:</p> <pre><code>from now_lms import lms_app\n# Configure your app:\nlms_app.config[\"SECRET_KEY\"] = \"set_a_very_secure_secret_key\"\nlms_app.config[\"SQLALCHEMY_DATABASE_URI\"] = \"database_uri\"\n\napp = lms_app\n\nfrom now_lms import serve, init_app\n\napp.app_context().push()\n\nif __name__ == \"__main__\":\n    init_app(with_examples=False)\n</code></pre> <ol> <li>Init app: Be sure to run <code>lmsctl</code> commands in the same directory that your app.py file. You can set the Administrator user and password o let the user use the default values. Since default values for admin user are publics in documentation they are more suitables for development purposes that for production usage.</li> </ol> <pre><code>$ ls\napp.py  favicon.gif  favicon.ico\n$ ADMIN_USER=setyouruserhere ADMIN_PSWD=setasecurepasswd flask --app app.py setup\n</code></pre> <ol> <li>Your your.domain/public directory should be like this:</li> </ol> <pre><code>$ ls\napp.py  favicon.gif  favicon.ico\n</code></pre> <ol> <li>Create a passenger_wsgi.py file in your.domain directory following the next template:</li> </ol> <pre><code>$ cd ..\n# ls\npublic  venv\n</code></pre> <p>passenger_wsgi.py template:</p> <pre><code>import sys\nimport os\n\n\n# Ensure we are using the virtual enviroment.\nINTERP = os.path.join(os.environ[\"HOME\"], \"yourdomain.com\", \"venv\", \"bin\", \"python3\")\nif sys.executable != INTERP:\n    os.execl(INTERP, INTERP, *sys.argv)\nsys.path.append(os.getcwd())\nsys.path.append(os.path.join(os.environ[\"HOME\"], \"yourdomain.com\", \"public\"))\n\n# Now we can import the configured app from the current directory\nfrom public.app import lms_app as application\n</code></pre> <ol> <li>You your.dommain folder should be like this:</li> </ol> <pre><code>$ ls\npassenger_wsgi.py venv public\n</code></pre> <p>You can check your passenger file works running it with python:</p> <pre><code>$ python3.8 passenger_wsgi.py\n</code></pre> <p>Is there are no errors Passenger should be able to run NOW - LMS without issues.</p> <p>Make the passenger_wsgi.py</p> <pre><code>$ chmod +x passenger_wsgi.py\n</code></pre> <ol> <li>Restart passenger:</li> </ol> <pre><code>mkdir tmp\ntouch tmp/restart.txt\n</code></pre> <p>your.domain directory should looks like this:</p> <pre><code>passenger_wsgi.py  public  tmp  venv\n</code></pre> <ol> <li>You should be able to acces NOW - LMS in your domain.</li> </ol>"},{"location":"logo.html","title":"The NOW-LMS logo","text":"<p>We use as primary font the Clarendon Serialfont, and the secondy font is Roboto.</p>"},{"location":"oci.html","title":"Install NOW - LMS with the OCI image.","text":""},{"location":"oci.html#oci-image","title":"OCI Image","text":"<p>There is also a OCI image disponible if you prefer to user containers, in this example we use podman:</p> <pre><code># &lt;---------------------------------------------&gt; #\n# Install the podman command line tool.\n# DNF family (CentOS, Rocky, Alma):\nsudo dnf -y install podman\n\n# APT family (Debian, Ubuntu):\nsudo apt install -y podman\n\n# OpenSUSE:\nsudo zypper in podman\n\n\n# &lt;---------------------------------------------&gt; #\n# Run the software.\n# Create a new pod:\npodman pod create --name now-lms -p 80:80 -p 443:443\n\n# Database:\npodman run --pod now-lms --rm --name now-lms-db --volume now-lms-postgresql-backup:/var/lib/postgresql/data -e POSTGRES_DB=nowlearning -e POSTGRES_USER=nowlearning -e POSTGRES_PASSWORD=nowlearning -d postgres:13\n\n# App:\npodman run --pod now-lms --rm --name now-lms-app -e LMS_KEY=nsjksldknsdlkdsljdnsdj\u00f1as\u00f1\u00f1qld\u00f1aas554dlkallas -e LMS_DB=postgresql+pg8000://nowlearning:nowlearning@localhost:5432/nowlearning -e LMS_USER=administrator -e LMS_PSWD=administrator -d quay.io/bmosoluciones/now-lms\n\n# Web Server\n# Download nginx configuration template:\ncd\nmkdir now_lms_dir\ncd now_lms_dir\ncurl -O https://raw.githubusercontent.com/bmosoluciones/now-lms/main/docs/nginx.conf\n\n# In the same directoy run the web server pod:\npodman run --pod now-lms --name now-lms-server --rm -v $PWD/nginx.conf:/etc/nginx/nginx.conf:ro -d nginx:stable\n\n</code></pre> <p>NOW-LMS also will work with MySQL or MariaDB just change the image of the database container and set the correct connect string. SQLite also will work if you will serve a few users.</p>"},{"location":"pypi.html","title":"Install NOW - LMS with the phyton package.","text":"<p>NOW - Learning Management System makes public releases as python packages on pypi, this packages can be installed via the pip tool with:</p> <pre><code>$ pip install now_lms\npython -m now_lms\n</code></pre> <p>Visit http://127.0.0.1:8080/ in your browser, default user and password are <code>lms-admin</code></p>"},{"location":"references.html","title":"Why yet another learning app?","text":"<p>We must agree that there are many options to host your online teaching on the web.</p> <p>Moodle is a PHP based giant and the primaty choice for many universities and big school, any way you must firts to use Moodle to serve a efective learning experience. Long history in short: maybe Moodle just feel to moucht for your online school requeriments.</p> <p>OpenEDX is the software thats powers the EDX, another great project if you want to go bit.</p> <p>Udemy If you only want to organize your lesson in videos and try to reach the largest possible audience Udemy is an option, however they have an aggressive charging policy and you may feel that they take most of the profit for your course online.</p> <p>Haven said that are some really nice options to host your courses on line like Thinkific and Teachable, with both of then you can make a on line class run than feels yours and just pay the hosting a payment fee, so NOW - LMS aims to be a place to your cources than you can host almost anywhere and if you want to get paid do not share the income with anyone.</p> <p>These sites can be a inspiration for you:</p> <ul> <li>Ana Ivars</li> <li>Miguel Grinberg</li> <li>Oana Labes</li> </ul>"},{"location":"references.html#a-flexible-way-to-set-up-your-course","title":"A flexible way to set up your course.","text":"<p>But there is more, we want to provide a flexible way to set up your cource flow, in NOW - LMS you can set up 3 types of resources:</p> <ul> <li>Required: A student must take the resource to advance her learning.</li> <li>Optional: A student can choose to not take this resource to advance her learning.</li> <li>Alternative: A student can choose betwen to or more equivalent leaning options to advance her learning.</li> </ul> <p>Here is a lexample with a flaute course:</p> <ul> <li>Lesson One (Required) - Introduction to floute</li> <li>Lesson Two (Optional) - How to read music: Treble Clef (it is optional because a student may al ready know     how to read music)</li> <li>Lesson Tree (Alternative) - POP easy songs</li> <li>Lesson Four (Alternative) - Rock easy songs</li> <li>Leasson Five (Alternative) - Classic easy songs: Here a student must finish at least one on the alternative     options to advance in the course, if the student takes 2 o the 3 options it will not count adicional since     the idea is to let student choose its learning path and ensure at less was options have been finished and     maybe evaluated.</li> </ul> <p>Another example with a Linux course:</p> <ul> <li>Lesson One (Required) - Bash command line.</li> <li>Lesson Two (Alternative) - Installing software in Debian and derivates with apt.</li> <li>Lesson Tree (Alternative) - Installing software in Fedora and derivates with dnf.</li> <li>Lesson Four (Optional) - Installing software in Arch Linux with pacman.</li> </ul> <p>Here a student must learn at less how to install software in Debian or Fedora and optionally learn how to install software in Arch Linux.</p>"},{"location":"references.html#not-only-video-driven-courses","title":"Not only video driven courses.","text":"<p>YouTube tutorials are a good way to learns something new, but creating high quality video lessons is hard and can be expensive to produce, we believe than a good course must have a good mix of resource formats, from plain text to videos, passing from pdf, infografics, audios, embebed content, etc.</p>"},{"location":"setup-conf.html","title":"Configuring NOW-LMS","text":"<p>There are several options to set the system configuration, for example if your are running NOW-LMS in a dedicated server most of the time system administrator prefer to save configuration options in a file saved in the file system, for administrator of the system using a container based enviroment or a server less setup setting up configuration via enviroment variables can be handy.</p>"},{"location":"setup-conf.html#enviroment-variables","title":"Enviroment variables:","text":"<p>NOW-LMS can load its configuration from enviroment variables, when running in a container enviroment it is usefull to set the configuration with enviroment variables than can be set via command line, Dockerfile o Containerfile archive or v\u00eda a grafical user interface like Cockpit <sup>1</sup> <sup>2</sup>, also enviroment variables can be set in a systemd unit file.</p>"},{"location":"setup-conf.html#setting-enviroments-variables-in-bash","title":"Setting enviroments variables in bash:","text":"<pre><code># Example of setting up variables in bash shell\nexport SECRET_KEY=set_a_very_secure_secret_key\nexport DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase\nlmsctl serve\n</code></pre>"},{"location":"setup-conf.html#example-systemd-unit-file","title":"Example systemd unit file:","text":"<p>In most modern Linux distribution systemd is the init service, you can set your own services writing a unit file:</p> <pre><code>[Unit]\nDescription=NOW - Learning Management System\n\n[Service]\nEnvironment=SECRET_KEY=set_a_very_secure_secret_key\nEnvironment=DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase\nExecStart=/usr/bin/lmsctl serve\n\n[Install]\nWantedBy=multi-user.target\n</code></pre>"},{"location":"setup-conf.html#dockerfile-enviroment-variables","title":"Dockerfile enviroment variables:","text":"<p>Most of the time you will want to save Docker enviroment varibles in a <code>compose.yml</code> file:</p> <pre><code>services:\n  web:\n    image: quay.io/bmosoluciones/now_lms\n    environment:\n    - SECRET_KEY=set_a_very_secure_secret_key\n    - DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase\n    ports:\n      - '8080:8080'\n\n</code></pre>"},{"location":"setup-conf.html#configuration-from-file","title":"Configuration from file:","text":"<p>NOW-LMS can load its configuration from a init like file placed in <code>/etc/nowlms.conf</code> or <code>$home/.config/nowlms.conf</code> or a file named <code>nowlms.conf</code> in the current directory of the main proccess. Save the configuration in a plain text is common for unix like operative systems administrators.</p> <pre><code># Example minimal configuration file in `/etc/nowlms.conf`\nSECRET_KEY=set_a_very_secure_secret_key_with_[\\w\\[\\]`!@#$%\\^&amp;*()={}:;&lt;&gt;+'-]*\nSQLALCHEMY_DATABASE_URI=postgresql+pg8000://scott:tiger@localhost/mydatabase\n</code></pre>"},{"location":"setup-conf.html#ad-hoc-configuration","title":"Ad hoc configuration:","text":"<p>You can can also configure NOW-LMS at run time setting configuration values in the <code>config</code> dictionary of the main Flask app.</p> <pre><code>from now_lms import lms_app\n# Configure your app:\nlms_app.config[\"SECRET_KEY\"] = \"set_a_very_secure_secret_key\"\nlms_app.config[\"SQLALCHEMY_DATABASE_URI\"] = \"database_uri\"\n\napp = lms_app\n</code></pre> <p>Note that initial log messages will refer to the default options because you are overwritten options before the initial import of the app.</p>"},{"location":"setup-conf.html#list-of-options","title":"List of options:","text":"<p>You can use the following options to configure NOW-LMS:</p> <ul> <li>SECRET_KEY (required): A secure string used to secure the login proccess and form validation.</li> <li>SQLALCHEMY_DATABASE_URI (required): A valid SQLAlchemy conextion string, SQLite, MySQL version 8 and a resent version of PostgreSQL     must work out of the box, MariaDB ans MS SQLServer should work but we not test the release versus this database engines. Checkout the     SQLAlchemy docs to valid examples to conections strings, the PyMSQL and PG800 database drivers are installed as normal dependencies, other database engines may requiere manual drivers setup.</li> <li>DATABASE_URL (alias): User friendly alias to <code>SQLALCHEMY_DATABASE_URI</code>.</li> <li>CACHE_REDIS_URL (optional): Connection string to use Redis as cache backend. Example to connect to a Redis     instance running in the same host is: <code>redis://localhost:6379/0</code>.</li> <li>REDIS_URL (alias): User friendly alias to <code>CACHE_REDIS_URL</code>.</li> <li>CACHE_MEMCACHED_SERVERS (optional): Connection string to use Mencached as cache backend.</li> <li>UPLOAD_FILES_DIR (recomended): Directory to save user uploaded files, must be writable. Note that this variable can be set AD-HOC     because the order we parse the configuration options upload file directorios must be set before the initial import of the app, any     overwritte we do can lead to unexpected results. It is better to set this option as enviroment variable before the firts run of the app. Note that if you migrate your instalation to a diferent host must edit this value so database records can match fisical file storage.</li> </ul>"},{"location":"setup.html","title":"Setup NOW-LMS","text":"<p>To run Now - LMS you need:</p> <ol> <li>A SWGI server to execute the Python Code.</li> <li>A database backend.</li> <li>A HTTP server, most of the times you will no want to expose your SWGI server to the wild.</li> <li>A optional cache service like Redis or Memcached.</li> </ol> <p>Now -LMS requires very low resources to run, a RaspberryPI can serve as a apropiate host, also a minimal VPS, a Shared Host service with support for Python 3.8 or greatter and serverless services like Render, Heroko or similar.</p> <p>Now-LMS is available as:</p> <ul> <li>Source Code.</li> <li>Python Package.</li> <li>OCI Image available.</li> </ul>"},{"location":"sing-off.html","title":"Developer Certificate of Origin","text":"<p>Developer Certificate of Origin Version 1.1</p> <p>Copyright (C) 2004, 2006 The Linux Foundation and its contributors.</p> <p>Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.</p> <p>Developer's Certificate of Origin 1.1</p> <p>By making a contribution to this project, I certify that:</p> <p>(a) The contribution was created in whole or in part by me and I     have the right to submit it under the open source license     indicated in the file; or</p> <p>(b) The contribution is based upon previous work that, to the best     of my knowledge, is covered under an appropriate open source     license and I have the right under that license to submit that     work with modifications, whether created in whole or in part     by me, under the same open source license (unless I am     permitted to submit under a different license), as indicated     in the file; or</p> <p>(c) The contribution was provided directly to me by some other     person who certified (a), (b) or (c) and I have not modified     it.</p> <p>(d) I understand and agree that this project and the contribution     are public and that a record of the contribution (including all     personal information I submit with it, including my sign-off) is     maintained indefinitely and may be redistributed consistent with     this project or the open source license(s) involved.</p>"}]}