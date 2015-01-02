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



: '
To setup in Thunderbird

'

