![alt text](https://raw.githubusercontent.com/CCRami/GradScraper/main/staticfiles/img/logo-transparent.png)
=====================

This project is a Django-based web application that allows users to scrape LinkedIn profiles and manage scraped data, focusing on student and employee information. It includes user authentication, secure access, and an interactive dashboard to view results.

Features
--------

-   **User Authentication**: Users can sign up, log in using email and password, and manage their session.
-   **Protected Routes**: All views except login and registration are protected, ensuring only logged-in users can access them.
-   **LinkedIn Scraper**: Scrape data from LinkedIn profiles, including students and employee information.
-   **Dashboard**: Interactive UI displaying scraped data, charts, and detailed information about graduates and companies.
-   **Profile Management**: Ability to view, edit, and manage user profiles.
-   **AJAX Search**: Real-time search in the student and employee list.
-   **Progress Tracking**: Users can monitor the scraping progress and time required to finish scraping.

Installation
------------

1.  **Clone the repository**:

    `git clone https://github.com/CCRami/GradScraper.git
    &&
    cd gradscraper`

3.  **Create a virtual environment** (optional but recommended):

    `python -m venv venv
    &&
    source venv/bin/activate  # On Windows use: venv\Scripts\activate`

5.  **Install dependencies**:

    `pip install -r requirements.txt`

6.  **Set up the database**:

    The project uses PostgreSQL. Update your `settings.py` file with your PostgreSQL configuration, or use SQLite for quick setup.

    `DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'your_db_name',
            'USER': 'your_db_user',
            'PASSWORD': 'your_db_password',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }`

    Then, run the following commands to set up the database:

    `python manage.py makemigrations
    python manage.py migrate`

7.  **Create a superuser** to access the admin panel:

    `python manage.py createsuperuser`

8.  **Run the development server**:

    `python manage.py runserver`

    Visit `http://127.0.0.1:8000/index` in your browser to access the application.

Usage
-----

1.  **Login and Registration**:

    -   Go to `/login/` to log in using your email and password.
    -   Go to `/register/` to sign up as a new user.
2.  **Dashboard**:

    -   After logging in, you will be redirected to the dashboard where you can start scraping LinkedIn profiles.
    -   You can view statistics, employee data, and company data from the dashboard.
3.  **Scraping Process**:

    -   Choose the scraping options (e.g., year of education, number of people).
    -   Track the scraping progress and view the results in the dashboard.
4.  **Protected Views**:

    -   Only logged-in users can access views like the dashboard, profile management, and scraping functionality. Non-logged-in users will be redirected to the login page.

Requirements
------------

-   Python 3.x
-   Django 3.x or later
-   PostgreSQL (or SQLite for local development)
-   Selenium (for LinkedIn scraping)
-   Celery (optional, for background scraping tasks)
-   Redis (optional, for task queue management)

Contributing
------------

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature-branch`).
3.  Make your changes.
4.  Commit and push your changes (`git commit -m "Add feature"`).
5.  Open a pull request to the `main` branch.

License
-------

This project is licensed under the MIT License. See the LICENSE file for details.
