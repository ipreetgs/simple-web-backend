docker run -d \
  -e DATABASE_URL=postgresql://postgres:yourpassword@host:5432/yourdb \
  -e JWT_SECRET_KEY=your-very-secret-key \
  -p 5000:5000 \
  my-flask-backend

# Deployment (Ubuntu, from Wheel)

1. **Transfer the wheel file to your server**
   
   After building, copy the wheel (e.g., `myapp-0.1.0-py3-none-any.whl`) to your Ubuntu server:
   
       scp dist/myapp-0.1.0-py3-none-any.whl user@your-server:/home/user/

2. **Set up a Python virtual environment**
   
       python3 -m venv venv
       source venv/bin/activate

3. **Install the wheel**
   
       pip install --upgrade pip
       pip install myapp-0.1.0-py3-none-any.whl

4. **Set environment variables**
   
   Export variables or create a `.env` file:
   
       export DATABASE_URL=your_database_url
       export JWT_SECRET_KEY=your_secret_key

5. **Run the application with Gunicorn**
   
       gunicorn -w 4 -b 0.0.0.0:5000 myapp.main:app

6. **(Recommended) Set up as a systemd service**
   
   Create `/etc/systemd/system/myapp.service`:
   
       [Unit]
       Description=Gunicorn instance to serve myapp
       After=network.target

       [Service]
       User=youruser
       Group=www-data
       WorkingDirectory=/home/youruser/
       Environment="PATH=/home/youruser/venv/bin"
       EnvironmentFile=/home/youruser/.env
       ExecStart=/home/youruser/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 myapp.main:app

       [Install]
       WantedBy=multi-user.target

   Then reload and start:

       sudo systemctl daemon-reload
       sudo systemctl start myapp
       sudo systemctl enable myapp

7. **(Recommended) Use Nginx as a reverse proxy**
   
   Set up Nginx to forward requests to Gunicorn for production use.

---

# Backend Testing

## Run Unit Tests with Coverage

Install dependencies:

    pip install -r requirements.txt

Run tests and generate coverage report (fail if coverage < 80%):

    coverage run -m pytest
    coverage report --fail-under=80
    coverage html  # (optional) to generate HTML report 