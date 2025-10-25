# DevSecOps Pipeline

This project demonstrates the implementation of a DevSecOps pipeline to secure an API.

The pipeline includes the following stages:

![alt text](<images/pipeline.png>)

- **SCA** (Software Composition Analysis) scan : Analysis of the application’s open-source libraries and dependencies to detect known vulnerabilities, outdated versions, and license risks.
- **SAST** (Static Application Security Testing) scan: Static analysis of the source code to detect vulnerabilities before execution, by reviewing each line of code.
- **DAST** (Dynamic Application Security Testing) scan: Dynamic testing of the running application to identify security flaws that can be exploited at runtime.
- **Test: Integration and Functional Tests**: Verification of the correct functioning of the application and the integration of its components, while ensuring the absence of regressions and security issues.


### Tools

- [**Snyk**](https://app.snyk.io/) to perform SCA, SAST scan and Monitoring
  - Scans your code and dependencies for vulnerabilities (SCA & SAST)
  - Monitoring : monitors your project over time for new security issues. Creates snapshots of dependencies and code uploaded to Snyk, sending alerts if new vulnerabilities appear later.
- [**ZAP Action Full Scan**](https://github.com/zaproxy/action-full-scan) to perform DAST scan
- **Pytest** to perform Integration and Functional Tests


### Difference between Integration and Functional Tests

- **Integration Tests** focus on verifying the interactions between different modules or components of the API. They ensure that combined parts of the system work together as expected (e.g., database and API endpoints working in sync).
- **Functional Tests** validate that a specific feature or function of the API behaves according to the requirements, typically by testing endpoints independently from their internal implementation.


## Setup environment

```bash
# Create a virtual environment
python3 -m venv env
````

```bash
# Activate the virtual environment
source env/bin/activate
```

```bash
# Install the requirements
pip3 install -r requirements.txt
```

```bash
# Create .env.local file
vim .env.local
# Add the following lines in .env.local:
DJANGO_SECRET_KEY="xxxxxxxxxx"
STRIPE_SECRET_KEY="xxxxxxxxxx"
```

To load these environment variables in your terminal session, run:

```bash
set -a; source .env.local; set +a
```
This will export all variables defined in .env.local to your current shell session.


```bash
# Apply the migrations
python3 manage.py migrate
```

```bash
# Run the application
python3 manage.py runserver
```

## Stripe Configuration

Don't forget to Stripe Secret Key in the `django_stripe/settings.py` file.

```python
STRIPE_SECRET_KEY = 'YOUR_STRIPE_SECRET_KEY'
```

## Postman Collection for testing the API

[Postman Collection](./django-stripe.postman_collection.json)


## Frontend Applications integrated with this Django Project and Stripe Frontend Library

These are the repositories that use this Django project as a backend and Stripe Frontend Library to make payments.

- [React Native Application](https://github.com/Alexon1999/react-native-stripe)
