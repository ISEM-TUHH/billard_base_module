# Run this script with sudo privileges to register the cron job and start the server

service=billard-game-server

# relative to this file:
#templatefolder=../../templates/

echo "Installing ${service}..."

# add download_page.html as symbolik link to the template folder of 
#ln -s ${templates}/download_page.html download_page.html


cp ./job.service /etc/systemd/system/${service}.service && echo "File succesfully moved"

systemctl daemon reload && echo "Systemctl daemon reloaded"
systemctl start ${service}.service && echo "Service succesfully started"
systemctl enable ${service}.service && echo "Service succesfully registered for startup"

systemctl status ${service}.service

echo "IP addresses:"
ip a | grep inet
