deactivate
mkvirtualenv -p python3.6 soup-dumpling
pip install -r requirements.txt
cp supervisor.conf /etc/supervisor/conf.d/soup-dumpling.conf
supervisorctl reread
supervisorctl update
