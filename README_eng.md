# Job_stat
This program is designed to calculate the expected average salary and the number of vacancies for programmers who speak the most popular programming languages.
For the calculation for the used data for the city of Moscow (Russia), taken from the web-sites [superjob.ru](https://www.superjob.ru/) and [hh.ru](https://www.hh.ru/). 

### How to setup

Python3 must already be installed.
 
Then use `pip` (или `pip3`, if there is a conflict with Python2) to install the dependencies:
```
pip install -r requirements.txt
```
#### Programm setting

In order for the program to work correctly, create an .env file in the program folder containing the key for accessing the [superjob.ru website](https://www.superjob.ru/).
Write it like this:

```
SUPERJOB_KEY="number of key"
```
The access key should be obtained according to the [instructions](https://api.superjob.ru/?from_refresh=1).


#### How to run

The program runs from the command line. To run the program using the cd command, you first need to go to the folder with the program.
To run the program on the command line, write:
```
python job_stat.py
```
Upon completion of the program, the user will receive two tables with data for each of the sites.

### Goal of project

The code is written for educational purposes in an online course for web developers [dvmn.org](https://dvmn.org/).
