virtual=$(python -c 'import sys; print("1" if hasattr(sys, "real_prefix") else "0")')

if [ $virtual -eq "1" ]; then
    deactivate;
fi

if lsvirtualenv -b | grep -E "^soup-dumpling$"; then
    rmvirtualenv soup-dumpling
fi

mkvirtualenv -p python3.6 soup-dumpling
pip install -r requirements.txt
cp supervisor.conf /etc/supervisor/conf.d/soup-dumpling.conf
supervisorctl reread
supervisorctl update
