# OpenUR 

* Dashbaord Server - perfectly connects and executes all the commands
* RTDE Commands - perfectly connects and executes all the commands
    * Need to think of a way when the user calls a function, rtde_configuration.xml shall be automatically generated.
* URScript Commands - Alpha version of the script is ready. need to add the is_program_running() function to stop the user from executing the script when the program is running.



# OpenUR

So, the reason you are seeing the error the first time you run the code is because the rtde_configuration.xml file is being read into memory when you create the RTDECommands object, but it is not being updated in memory after you modify the file on disk. 

- need to think of a way when the user calls a function, memory shall be automatically updated.

- implement connection clothing methods from Dashboar to RTDECommands