```
__author__ = "Beck Isakov"
__copyright__ = "Beck isakov"
__credits__ = "Martin Huus Bjerge"
__contact__ = "https://github.com/Jp-Beck"
__license__ = "GPL v3"
__version__ = "0.2.4"
__maintainer__ = "Beck Isakov"
__email__ = "jp-beck@outlook.com"
__status__ = "Development"
```

For full documentation visit [jp-beck.github.io](https://jp-beck.github.io/learnur/OpenUr/).


# Documentation Guide

## Introduction
- **Overview**: 
This is the all in one package to control or get data from the Universal robots.
- **Features**: 
    - Real Time Data Exchange [RTDE](https://www.universal-robots.com/articles/ur/interface-communication/real-time-data-exchange-rtde-guide/) fully implemented.
    - [Dashboard](https://www.universal-robots.com/articles/ur/dashboard-server-e-series-port-29999/).
    - [URScript](https://www.universal-robots.com/download/manuals-e-series/script/script-manual-e-series-sw-512/), send URScript commands to the robot and get the response.
    - Send and receive any data via Socket communication from the Robot.
    - [XMLRPC](https://en.wikipedia.org/wiki/XML-RPC) communication with the robot. (allows you to outsource the CPU intensive tasks to the PC)
- **Supported Versions/Platforms**: 
    - Python 3.6+ (will later support 2.7)
    - Universal Robots e-Series, tested on UR3e, UR5e, UR10e, UR16e
    - Windows, Linux, Mac OS X

## [Quick Start or Getting Started](./docs/quick_start.md)

1.  `pip install OpenUr` - Install the latest version of OpenUr package.
2. `openur make .` - Create a new rtde_configuartion.xml file in your project directory to enable the use of RTDE.
3. `import openur` - Import the package in your project.
4. `openur = OpenUR('ROBOT_IP_ADDRESS')` - Connect to the robot and access all the features of the package via the `openur` object.
5. For example: `openur.get_actual_tcp_pose()` - Get the current TCP pose of the robot.

## [Installation Guide](./docs/installation_guide.md)
- `pip install OpenUr` - Easiest way to install the package.
- [Source Code](https://github.com/Jp-Beck/openur) - You can source it from the github repository.
- [Docker](#) - You can also use the docker image to run the package (In the future)

## [User Guide or Manual](./docs/user_guide.md)
- [Getting Started in User Guide](docs/user_guide.md#getting-started)
- Refer to the [Examples/Tutorials](./docs/examples.md)

## [API Reference](./docs/APIReference.md#API)
- This section will be update in the future.

## [Examples/Tutorials](./docs/examples.md)
- Step-by-step guides or use-case driven tutorials.
- Helps users understand real-world applications of your package.

## [FAQs](./docs/FAQs.md)
-  Common questions or issues that users might encounter.

## [Troubleshooting](./docs/troubleshooting.md)
- Common issues, error messages, and their resolutions.
- Tips for diagnosing issues.

## [Contribution Guide](./docs/contribution_guide.md)
- Feel free to request pulls and collaborate.
- Please read the contribution guide before making pull requests.

## [Changelog or Release Notes](./CHANGELOG.md)
- Document the changes made in each release.

## [License](./LICENSE)
- Clearly state the license under which your software is released.

## [Contact/Support](./docs/support.md)
- Provide information on how users can get support.

## [Glossary](./docs/glossary.md)
- Technical terms or jargon used.


## Project layout
```
    .
├── build
├── CHANGELOG
├── dist
├── docs
│   ├── examples.md
│   ├── glossary.md
│   ├── installation_guide.md
│   ├── migration_guide.md
│   ├── quick_start.md
│   ├── support.md
│   ├── troubleshooting.md
│   └── user_guide.md
├── LICENSE
├── MANIFEST.in
├── openur
│   ├── cli.py
│   ├── connections
│   │   ├── connection_state.py
│   │   ├── __init__.py
│   │   ├── realTimeClient.py
│   │   └── robotConnector.py
│   ├── dashboard
│   │   ├── dashboard.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── kinematics
│   │   ├── __init__.py
│   │   ├── kinematic.py
│   │   └── manipulation.py
│   ├── rtde
│   │   ├── csv_binary_writer.py
│   │   ├── csv_reader.py
│   │   ├── csv_writer.py
│   │   ├── __init__.py
│   │   ├── rtde_config.py
│   │   ├── rtde.py
│   │   └── serialize.py
│   ├── rtde_command
│   │   ├── __init__.py
│   │   ├── rtde_commands.py
│   │   └── rtde_connect.py
│   ├── urscript
│   │   ├── freedrive.py
│   │   ├── __init__.py
│   │   ├── script.txt
│   │   ├── urScriptExt.py
│   │   ├── urscript.py
│   │   └── urScript.py
│   └── utils
│       ├── dataLogging.py
│       ├── data_log.py
│       ├── dataLog.py
│       ├── __init__.py
│       └── logConfig.xml
├── openur.py
├── README.md
├── requirements.txt
├── rtde_configuration.xml # This file is created by the command `openur make .` and must have the name rtde_configuration.xml
├── setup.py
└── TODO.MD
```