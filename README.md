# CM3070_FinalProject
Home Surveillance System

# Frontend
Ensure latest NodeJS LTS is installed.

Install the Angular CLI globally:
```shell
npm install -g @angular/cli
```

Once completed, within the frontend project run:
```shell
npm install
```

Then run:
```shell
npm run start
```

The port used for the web application is typically 4200, thus navigating to:
http://localhost:4200
Will show the web app. Otherwise, after running "npm run start", check the terminal/command prompt output to see the port being used.

# Backend
First it is recommended to create a virtual environment. Here's a guide to assist:
https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/

Once creating the venv and activating it within the backend directory, run:
```shell
pip install -r requirements.txt
```

Then run:
```shell
uvicorn main:app --reload
```

This will startup the API.