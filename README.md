# pyAirmail
Python implementation of the Airmail Client for send/recieve emails over the Sailmail/Winlink (SSB radio) networks and to receieve WeatherFax transmissions.  

## Why do this 
Mark Pitman developed this so that he could send and receive mail via SSB radio *and* receive WeatherFax transmissions on his low-powered ARM-based computer (Cubieboard) using his ICOM-M802 and SCS PTC-IIex PACTOR modem.  Using a low-powered ARM-based computer had several advantages, including:
* Power consumption could be reduced to less than 1-Watt (0.1 Amps) as compared to ~5 Amps for an old laptop running Windows XP and Airmail
* The low-power computer had reduced interference with the SSB radio than a full laptop
* As the ARM processor could run continuously without power issues then send/receieve could be scheduled at optimal times for best propagation
* The ARM-computer was more robust/water-resistant than a laptop with fan
* Multiple processor boards were carried and, in case or failure or water/salt damage, the waterproof SD-card could be swapped with a new unit.

This system was used for his voyage from Australia to Denmark from 2015 to 2016 over a distance of 18,000 nautical miles across the Indian and South and North Atlantic Oceans.

This pure-Python implementation allows cross-platform operation on any system that supports Python (which is almost everything) incluing operation on low-powered ARM-based processors (Raspberry-PI, Cubieboard, etc.).  So you don't have to run this on an ARM-board necessarily.

## How was this developed 
Most of this work was reverse-engineered from the existing Airmail client for Windows XP.   

## Installation 
Sailmail/Winlink messages may be sent/received in any email client. A **mail transfer agent** is required to route messages between your email client and pyAirmail.  We use Postfix for this.  This can be installed on a Debian-based ARM system (such as ARMbian or any Debian/Ubuntu based OS) as follows:

```
# Setup information from here:
# https://help.ubuntu.com/community/PostfixBasicSetupHowto

# Install and test
sudo apt-get install postfix
sudo apt-get install courier-pop
sudo postfix status

# Instruct Postfix to use Maildirs instead of Mboxes:
sudo postconf -e "home_mailbox = Maildir/"

# Ensure Procmail isn't used: (if the step was taken during dpkg-reconfigure, by mistake) 
sudo postconf -e "mailbox_command = "

# Set postfix to get messages from local machine only
sudo postconf -e "inet_interfaces = loopback-only"

# Restart Postfix to make changes effect. 
sudo  /etc/init.d/postfix restart

#Add the following lines to your /etc/postfix/master.cf:
fs_mail    unix  -       n       n       -       -       pipe
   flags=F user=%YOUR_USER_NAME% argv=tee /home/%YOUR_USER_NAME%/fs_mail.dump
# OR to send to a python script
   flags=F user=mark argv=/home/mark/git/pyPaclink/parseoutgoing.py

#And then change this line to your /etc/postfix/main.cf:
#default_transport = error
default_transport = fs_mail
```

