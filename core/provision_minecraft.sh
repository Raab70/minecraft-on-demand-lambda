#!/bin/bash
yum update -y
yum install -y java-1.8.0 expect tmux htop ncdu git # java-1.8.0-openjdk-devel
yum remove -y java-1.7.0-openjdk
pip install mcstatus requests

mkdir -p /minecraft
chown -R ec2-user:ec2-user /minecraft

exec sudo -u ec2-user -i /bin/bash - <<'DROP_PRIVILEGES_EOF'

aws s3 sync s3://${aws_s3_world_backup} /minecraft/
cd /minecraft

spigot_jar="$(find . -maxdepth 1 -name 'spigot*jar' | sort | tail -1)"
minecraft_jar='minecraft_server.1.12.2.jar'
server_jar="$${spigot_jar:-$$minecraft_jar}" # dollar doubled for terraform template

if [[ ! -r minecraft-setup-done ]]; then
    wget 'https://s3.amazonaws.com/Minecraft.Download/versions/1.12.2/minecraft_server.1.12.2.jar'
    cat <<EOF >eula.txt
#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).
#Tue Sep 19 00:42:15 EDT 2017
eula=true
EOF
    echo -e 'save-all\rsay SERVER RESTARTING\rstop' | java -Xmx900M -Xms900M -jar $server_jar nogui
    touch minecraft-setup-done
    aws s3 sync /minecraft/ s3://${aws_s3_world_backup}
fi

{ crontab -l; echo "*/15 * * * * aws s3 sync /minecraft/ s3://${aws_s3_world_backup}"; } | crontab -
{ crontab -l; echo "*/5 * * * * python /minecraft/auto_shutoff.py"; } | crontab -

tmux new-session -d -s minecraft -n minecraft
tmux send-keys -t minecraft:minecraft "while true; do java -Xmx900M -Xms900M -jar $server_jar nogui; sleep 5; done" C-m
# Reset the active time at start so that server doesn't kill itself right after starting.
python -c "import time;f = open('/minecraft/last_activity', 'w');f.write(str(time.time()));f.close()"
DROP_PRIVILEGES_EOF

