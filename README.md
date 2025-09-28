# DevSecOps Pipeline

This project demonstrates the implementation of a DevSecOps pipeline to secure an API.

The pipeline includes the following stages:
- **SAST** (Static Application Security Testing): Static analysis of the source code to detect vulnerabilities before execution, by reviewing each line of code.
- **DAST** (Dynamic Application Security Testing): Dynamic testing of the running application to identify security flaws that can be exploited at runtime.
- **Integration and Functional Tests**: Verification of the correct functioning of the application and the integration of its components, while ensuring the absence of regressions and security issues.

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